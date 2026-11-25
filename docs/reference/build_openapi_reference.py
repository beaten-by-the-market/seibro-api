"""Generate the SEIBRO Open API reference from the KSD guides and portal checks."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

ROOT = Path(__file__).resolve().parent
GUIDES = {
    "Corp": "기업정보",
    "Stock": "주식정보",
    "Bond": "채권정보",
    "DerivCombi": "파생결합증권정보",
    "Oversea": "외화증권정보",
}
API_ID = re.compile(r"get[A-Za-z0-9]+")
URL_ID = re.compile(r"[?&]apiId=([A-Za-z0-9]*)", re.IGNORECASE)
URL_PARAMS = re.compile(r"[?&]params=([^&\n]*)", re.IGNORECASE)
URL_KEY = re.compile(r"([?&]key=)[^&\s]*", re.IGNORECASE)
Row = list[str]


def read_rows(sheet: Worksheet) -> list[Row]:
    def as_text(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, datetime) and not any((value.hour, value.minute, value.second, value.microsecond)):
            return value.date().isoformat()
        return str(value).strip()

    result = []
    for values in sheet.values:
        row = [as_text(value) for value in values]
        if any(row):
            result.append(row)
    return result


def table(header: Row, rows: list[Row]) -> str:
    def format_row(row: Row) -> str:
        cells = []
        for value in row[:len(header)]:
            text = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            cells.append(text.replace("|", r"\|").replace("\n", "<br>").replace("\r", ""))
        cells.extend([""] * (len(header) - len(cells)))
        return "| " + " | ".join(cells) + " |"

    return "\n".join([format_row(header), format_row(["---"] * len(header)), *(format_row(row) for row in rows)])


def marker(rows: list[Row], label: str) -> int:
    return next(i for i, row in enumerate(rows) if "".join(row[0].split()) == label)


@dataclass
class Fields:
    header: Row
    rows: list[Row]
    notes: list[str]

    @classmethod
    def from_rows(cls, rows: list[Row]) -> Fields:
        headings, *body = rows
        if headings[0].casefold() != "no.":
            raise ValueError(f"항목 표의 헤더를 찾을 수 없습니다: {headings[0]}")
        width = max(i for row in rows for i, value in enumerate(row, start=1) if value)
        fields = [row[:width] for row in body if row[0].isdigit()]
        notes = [" ".join(value for value in row if value) for row in body if not row[0].isdigit()]
        return cls(headings[:width], fields, notes)

    def markdown(self) -> str:
        return "\n\n".join([table(self.header, self.rows), *(f"> {note}" for note in self.notes)])


@dataclass
class Preview:
    records: int
    url: str = ""
    samples: dict[str, str] = field(default_factory=dict)
    required: dict[str, str] = field(default_factory=dict)
    renamed_fields: dict[str, str] = field(default_factory=dict)
    added_fields: dict[str, tuple[int, str]] = field(default_factory=dict)
    result_element: str = ""
    notes: list[str] = field(default_factory=list)

    def inputs(self, source: Fields) -> Fields:
        rows = [row.copy() for row in source.rows]
        for row in rows:
            row[4] = self.samples.get(row[2], row[4])
            row[6] = self.required.get(row[2], row[6])
        return Fields(source.header, rows, source.notes)

    def outputs(self, source: Fields) -> Fields:
        rows = [row.copy() for row in source.rows]
        for row in rows:
            row[2] = self.renamed_fields.get(row[2], row[2])
        for name, (position, label) in self.added_fields.items():
            rows.insert(position - 1, [str(position), label, name, "", "", "", "실제 응답에서 확인"])
        if self.added_fields:
            for position, row in enumerate(rows, start=1):
                row[0] = str(position)
        return Fields(source.header, rows, source.notes)


@dataclass
class Endpoint:
    sheet: str
    name: str
    sheet_id: str
    purpose: str
    url: str
    remarks: list[Row]
    inputs: Fields
    outputs: Fields

    @classmethod
    def from_sheet(cls, sheet: Worksheet) -> Endpoint:
        rows = read_rows(sheet)
        request_start = marker(rows, "호출파라미터")
        response_start = marker(rows, "출력메시지")
        metadata = rows[:request_start]
        [sheet_id] = [row[1] for row in metadata if API_ID.fullmatch(row[1])]
        [name] = [row[1] for row in metadata if "".join(row[0].split()) == "API명" and row[1] != sheet_id]
        [purpose] = [row[1] for row in metadata if row[0] == "상세기능"]
        [url] = [row[1] for row in metadata if row[0] == "URL"]
        remarks = [
            [row[0], " ".join(value for value in row[1:] if value)]
            for row in metadata if row[1] not in {name, sheet_id, purpose, url}
        ]
        return cls(
            sheet.title, name, sheet_id, purpose, URL_KEY.sub(r"\1{SEIBRO_API_KEY}", url), remarks,
            Fields.from_rows(rows[request_start + 1:response_start]), Fields.from_rows(rows[response_start + 1:]),
        )

    @property
    def url_id(self) -> str:
        match = URL_ID.search(self.url)
        return match.group(1) if match else ""

    @property
    def api_id(self) -> str:
        return self.url_id if self.url_id.casefold() == self.sheet_id.casefold() else self.sheet_id

    def differences(self, listed_id: str) -> list[str]:
        notes = []
        if listed_id != self.api_id:
            notes.append(f"목록 ID `{listed_id}`")
        if self.sheet_id != self.api_id:
            notes.append(f"상세 시트 ID `{self.sheet_id}`")
        if not self.url_id:
            notes.append("엑셀 URL 예시의 `apiId`가 비어 있습니다.")
        elif self.url_id != self.api_id:
            notes.append(f"URL 예시 ID `{self.url_id}`")
        params = URL_PARAMS.search(self.url)
        if params:
            names = {part.partition(":")[0].strip() for part in params.group(1).split(",") if ":" in part}
            undocumented = sorted(names - {row[2] for row in self.inputs.rows})
            if undocumented:
                notes.append("엑셀 URL 예시에만 표시된 파라미터 " + ", ".join(f"`{name}`" for name in undocumented))
        return notes

    def markdown(self, listed_id: str, preview: Preview) -> str:
        parts = [
            f"## `{self.api_id}`",
            f"**{self.name}** · 원본 시트 `{self.sheet}`",
            self.purpose,
        ]
        if self.remarks:
            parts.append(table(["항목", "내용"], self.remarks))
        parts.extend(f"- {note}" for note in self.differences(listed_id))
        if preview.notes:
            parts.append("\n".join(f"- {note}" for note in preview.notes))
        parts.extend([
            "포털 미리보기 호출 예시" if preview.url else "원본 호출 예시",
            f"```text\n{preview.url or self.url}\n```",
            "### 요청 파라미터",
            preview.inputs(self.inputs).markdown(),
            "### 출력 필드",
        ])
        if preview.result_element:
            parts.append(
                f"포털 TEST의 XML 레코드 경로는 `vector/data/{preview.result_element}`입니다. "
                "HTTPS 응답에서는 `SeibroAPI` 안에 이 경로가 있습니다."
            )
        parts.append(preview.outputs(self.outputs).markdown())
        return "\n\n".join(parts)


def workbook_reference(name: str, label: str, previews: dict[str, Preview]) -> tuple[str, str, list[Row], list[Row]]:
    filename = f"Guide_{name}.xlsx"
    slug = name.lower()
    workbook = load_workbook(ROOT / "originals" / filename)
    overview = read_rows(workbook["목록"])
    history_marker = marker(overview, "작성이력관리")
    summary_header = overview[0][:4]
    summary_rows = overview[1:history_marker]
    history_header, *history = overview[history_marker + 1:]
    endpoints = [
        Endpoint.from_sheet(sheet) for sheet in workbook
        if sheet.title not in {"목록", "참고_국가코드"}
    ]
    if len(summary_rows) != len(endpoints):
        raise ValueError(f"{filename}에서 목록과 상세 시트의 개수가 다릅니다.")

    outline, details, index, differences = [], [], [], []
    category = ""
    for entry, api in zip(summary_rows, endpoints):
        listed_category, listed_name, listed_id, listed_purpose = entry[:4]
        if listed_id.casefold() != api.api_id.casefold() and listed_name != api.name:
            raise ValueError(f"{filename} 목록의 {listed_name}에 해당하는 상세 시트를 찾을 수 없습니다.")
        category = listed_category or category
        anchor = f"#{api.api_id.lower()}"
        preview = previews[api.api_id]
        outline.append([category, listed_name, f"[`{api.api_id}`]({anchor})", listed_purpose])
        details.append(api.markdown(listed_id, preview))
        link = f"[`{api.api_id}`]({slug}.md{anchor})"
        fields = ", ".join(f"`{row[2]}`" for row in api.inputs.rows if row[2])
        index.append([link, label, api.name, fields, str(len(preview.outputs(api.outputs).rows)), str(preview.records)])
        notes = api.differences(listed_id)
        if notes:
            differences.append([link, "\n".join(notes)])

    parts = [
        f"# {label} Open API 명세",
        f"[엑셀 원본](originals/{filename}) · [전체 API 색인](README.md)",
        f"엑셀 가이드와 포털 미리보기에서 대조한 API {len(endpoints)}개를 담았습니다. 요청 예시의 키는 변수명으로 표시했습니다.",
        "## 서비스 목록",
        table(summary_header, outline),
        "## 작성 이력",
        table(history_header[:3], history),
        *details,
    ]
    if "참고_국가코드" in workbook:
        [country_title, country_header, *countries] = read_rows(workbook["참고_국가코드"])
        parts.extend(["## 외화증권 국가코드", f"{country_title[0]} · 원본 시트 `참고_국가코드`", table(country_header[:4], countries)])

    return "\n\n".join(parts) + "\n", f"[`{filename}`](originals/{filename})", index, differences


def build() -> dict[str, str]:
    portal = json.loads((ROOT / "portal_preview.json").read_text(encoding="utf-8"))
    previews = {api_id: Preview(**details) for api_id, details in portal["apis"].items()}
    documents: dict[str, str] = {}
    guides, entries, differences = [], [], []
    for name, label in GUIDES.items():
        document, source, endpoints, notes = workbook_reference(name, label, previews)
        filename = f"{name.lower()}.md"
        documents[filename] = document
        guides.append([f"[{label}]({filename})", source, str(len(endpoints))])
        entries.extend(endpoints)
        differences.extend(notes)

    if len(previews) != len(entries):
        raise ValueError("포털 미리보기와 엑셀 가이드의 API 개수가 다릅니다.")
    with_records = sum(preview.records > 0 for preview in previews.values())
    documents["README.md"] = "\n\n".join([
        "# SEIBRO 공식 Open API 명세",
        f"한국예탁결제원 엑셀 가이드 5종의 API {len(entries)}개를 정리했습니다. API ID나 영문 필드명을 검색한 뒤 상세 페이지에서 자료형, 샘플, 필수여부, 코드표를 확인할 수 있습니다.",
        "공식 API에 필요한 조회가 없으면 [공공데이터포털 API 명세](data-go-kr/README.md)에서 서비스와 대표 호출을 확인합니다.",
        f"{portal['checked_on']} 포털의 5개 메뉴에서 각 API의 호출변수와 TEST URL·XML 응답을 대조했습니다. "
        f"첫 순회에서 {with_records}개 API가 레코드를 반환했습니다. 0건이었던 두 API는 메뉴를 새로고침하고 다시 TEST해 각각 1건을 확인했습니다. "
        f"[API 활용신청 포털]({portal['source']})",
        "## 가이드",
        table(["분야별 명세", "엑셀 원본", "API 수"], guides),
        "[외화증권 국가코드표](oversea.md#외화증권-국가코드)는 엑셀의 참고 시트를 옮겼습니다.",
        "## API 색인",
        table(["API ID", "분야", "API 명", "요청 파라미터", "출력 필드 수", "첫 순회 TEST 응답 건수"], entries),
        "## 원본 표기 차이",
        "엑셀의 목록, 상세 시트, 호출 예시가 서로 다른 곳입니다. 색인에는 포털에서 확인한 API ID를 사용했습니다.",
        table(["API ID", "차이"], differences),
        "## 읽는 법",
        "- `필수선택`의 입력 조건은 각 API의 요청 표와 주석을 함께 확인합니다. 자료형·코드표는 엑셀 가이드를 따릅니다.\n"
        "- 포털 미리보기 호출 예시는 화면에 표시된 URL입니다. HTTPS 전송과 키 처리는 [Python 클라이언트](../../seibro_api/openapi/client.py)에서 맡습니다. "
        "구현된 공개 함수는 [Python API 레퍼런스](../python_reference.md), 실측한 제약은 [데이터 소스](../data_sources.md)에 있습니다.\n"
        "- 파생결합증권 일부 API는 대문자 `RESULT`를 반환합니다. 현재 Python 클라이언트는 소문자 `result`를 찾으므로 해당 응답에서 파싱 오류가 납니다.\n"
        "- 문서는 엑셀 가이드와 [포털 확인 기록](portal_preview.json)에서 생성합니다. 자료를 갱신한 뒤 레포 루트에서 `python docs/reference/build_openapi_reference.py`를 실행합니다. "
        "`--check`는 저장 없이 생성 문서의 일치 여부를 검사합니다.",
    ]) + "\n"
    return documents


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify generated Markdown without writing it")
    args = parser.parse_args()
    stale = []
    for name, text in build().items():
        path = ROOT / name
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                stale.append(name)
        else:
            path.write_text(text, encoding="utf-8")
    if stale:
        raise SystemExit("생성 문서를 갱신하세요: " + ", ".join(stale))


if __name__ == "__main__":
    main()
