from __future__ import annotations

import argparse
import base64
import json
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DEFAULT_START_URL = "https://seibro.or.kr/"
TEXTUAL_MIME_HINTS = (
    "application/json",
    "application/xml",
    "text/",
    "xml",
    "json",
    "javascript",
    "x-www-form-urlencoded",
)


@dataclass
class RequestRecord:
    request_id: str
    url: str = ""
    method: str = ""
    request_headers: dict[str, Any] = field(default_factory=dict)
    request_post_data: str | None = None
    response_status: int | None = None
    response_headers: dict[str, Any] = field(default_factory=dict)
    response_mime_type: str = ""
    response_body: str | None = None
    response_body_base64: bool = False
    error: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "url": self.url,
            "method": self.method,
            "request_headers": self.request_headers,
            "request_post_data": self.request_post_data,
            "response_status": self.response_status,
            "response_headers": self.response_headers,
            "response_mime_type": self.response_mime_type,
            "response_body": self.response_body,
            "response_body_base64": self.response_body_base64,
            "error": self.error,
            "events": self.events,
        }


class SeibroWebRecorder:
    def __init__(
        self,
        out_dir: Path,
        start_url: str,
        filter_hosts: list[str],
        include_bodies: bool,
        body_limit: int,
        poll_interval: float,
        keep_browser_open: bool,
    ) -> None:
        self.out_dir = out_dir
        self.start_url = start_url
        self.filter_hosts = filter_hosts
        self.include_bodies = include_bodies
        self.body_limit = body_limit
        self.poll_interval = poll_interval
        self.keep_browser_open = keep_browser_open

        self.driver: Any | None = None
        self.records: dict[str, RequestRecord] = {}
        self.raw_events_path = self.out_dir / "network_events.jsonl"
        self._stop = threading.Event()
        self._poller: threading.Thread | None = None

    def start(self) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.driver = self._build_driver()
        self.driver.execute_cdp_cmd(
            "Network.enable",
            {
                "maxTotalBufferSize": self.body_limit * 4,
                "maxResourceBufferSize": self.body_limit,
            },
        )
        self._poller = threading.Thread(target=self._poll_loop, daemon=True)
        self._poller.start()
        self.driver.get(self.start_url)

    def stop(self) -> None:
        self._stop.set()
        self._flush_performance_logs()
        if self._poller:
            self._poller.join(timeout=5)
        self._write_outputs()
        if self.driver and not self.keep_browser_open:
            self.driver.quit()

    def _build_driver(self) -> Any:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
        except ModuleNotFoundError as exc:
            raise SystemExit(
                "selenium is not installed. Run: pip install -r recorder/requirements.txt"
            ) from exc

        options = Options()
        options.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"})
        options.add_experimental_option(
            "perfLoggingPrefs",
            {
                "enableNetwork": True,
                "enablePage": True,
            },
        )
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        return webdriver.Chrome(options=options)

    def _poll_loop(self) -> None:
        while not self._stop.is_set():
            self._flush_performance_logs()
            time.sleep(self.poll_interval)

    def _flush_performance_logs(self) -> None:
        if not self.driver:
            return
        try:
            entries = self.driver.get_log("performance")
        except Exception:
            return

        with self.raw_events_path.open("a", encoding="utf-8") as f:
            for entry in entries:
                try:
                    message = json.loads(entry["message"])["message"]
                except (KeyError, json.JSONDecodeError):
                    continue

                method = message.get("method", "")
                params = message.get("params", {})
                event = {
                    "wall_time": entry.get("timestamp"),
                    "method": method,
                    "params": params,
                }
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
                self._handle_event(method, params)

    def _handle_event(self, method: str, params: dict[str, Any]) -> None:
        request_id = params.get("requestId")
        if not request_id:
            return

        if method == "Network.requestWillBeSent":
            request = params.get("request", {})
            url = request.get("url", "")
            if not self._url_in_scope(url):
                return
            record = self.records.setdefault(request_id, RequestRecord(request_id=request_id))
            record.url = url
            record.method = request.get("method", "")
            record.request_headers = request.get("headers", {}) or {}
            record.request_post_data = request.get("postData")
            record.events.append({"method": method, "timestamp": params.get("timestamp")})

        elif method == "Network.requestWillBeSentExtraInfo":
            record = self.records.get(request_id)
            if record:
                record.request_headers.update(params.get("headers", {}) or {})
                record.events.append({"method": method, "timestamp": params.get("timestamp")})

        elif method == "Network.responseReceived":
            response = params.get("response", {})
            url = response.get("url", "")
            if not self._url_in_scope(url):
                return
            record = self.records.setdefault(request_id, RequestRecord(request_id=request_id))
            record.url = record.url or url
            record.response_status = response.get("status")
            record.response_headers = response.get("headers", {}) or {}
            record.response_mime_type = response.get("mimeType", "") or ""
            record.events.append({"method": method, "timestamp": params.get("timestamp")})

        elif method == "Network.responseReceivedExtraInfo":
            record = self.records.get(request_id)
            if record:
                record.response_headers.update(params.get("headers", {}) or {})
                record.events.append({"method": method, "timestamp": params.get("timestamp")})

        elif method == "Network.loadingFinished":
            record = self.records.get(request_id)
            if not record:
                return
            record.events.append({"method": method, "timestamp": params.get("timestamp")})
            if self.include_bodies and self._should_capture_body(record):
                self._capture_body(record)

        elif method == "Network.loadingFailed":
            record = self.records.get(request_id)
            if record:
                record.error = params.get("errorText")
                record.events.append({"method": method, "timestamp": params.get("timestamp")})

    def _capture_body(self, record: RequestRecord) -> None:
        if not self.driver or record.response_body is not None:
            return
        try:
            body_info = self.driver.execute_cdp_cmd(
                "Network.getResponseBody",
                {"requestId": record.request_id},
            )
        except Exception as exc:
            record.error = f"getResponseBody failed: {exc}"
            return

        body = body_info.get("body", "")
        base64_encoded = bool(body_info.get("base64Encoded"))

        if base64_encoded:
            raw = base64.b64decode(body)
            if len(raw) > self.body_limit:
                record.response_body = base64.b64encode(raw[: self.body_limit]).decode("ascii")
                record.error = "response body truncated"
            else:
                record.response_body = body
            record.response_body_base64 = True
            return

        if len(body.encode("utf-8", errors="ignore")) > self.body_limit:
            record.response_body = body[: self.body_limit]
            record.error = "response body truncated"
        else:
            record.response_body = body

    def _should_capture_body(self, record: RequestRecord) -> bool:
        mime = (record.response_mime_type or "").lower()
        if any(hint in mime for hint in TEXTUAL_MIME_HINTS):
            return True
        url = record.url.lower()
        return any(token in url for token in ("callservletservice", ".xml", ".json", ".jsp"))

    def _url_in_scope(self, url: str) -> bool:
        if not self.filter_hosts:
            return True
        host = urlparse(url).netloc.lower()
        return any(host == item or host.endswith("." + item) for item in self.filter_hosts)

    def _write_outputs(self) -> None:
        records = [record.to_dict() for record in self.records.values()]
        records.sort(key=lambda item: item.get("url", ""))

        (self.out_dir / "requests.json").write_text(
            json.dumps(records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        web_calls = [record for record in records if self._looks_like_replay_candidate(record)]
        (self.out_dir / "web_calls.json").write_text(
            json.dumps(web_calls, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        cookies = []
        if self.driver:
            try:
                cookies = self.driver.get_cookies()
            except Exception:
                cookies = []
        (self.out_dir / "cookies.json").write_text(
            json.dumps(cookies, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        (self.out_dir / "replay_candidates.py").write_text(
            self._build_replay_script(web_calls),
            encoding="utf-8",
        )

        summary = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "start_url": self.start_url,
            "filter_hosts": self.filter_hosts,
            "request_count": len(records),
            "web_call_count": len(web_calls),
        }
        (self.out_dir / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _looks_like_replay_candidate(self, record: dict[str, Any]) -> bool:
        url = (record.get("url") or "").lower()
        method = (record.get("method") or "").upper()
        post_data = record.get("request_post_data") or ""
        if "callservletservice.jsp" in url:
            return True
        if "websquare" in url and method == "POST":
            return True
        if post_data.lstrip().startswith("<reqParam"):
            return True
        return False

    def _build_replay_script(self, web_calls: list[dict[str, Any]]) -> str:
        lines = [
            "import requests",
            "",
            "session = requests.Session()",
            "ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36'",
            "",
        ]

        for i, call in enumerate(web_calls, 1):
            headers = dict(call.get("request_headers") or {})
            for noisy in ("Cookie", "Host", "Content-Length", "Accept-Encoding"):
                headers.pop(noisy, None)
            headers.setdefault("User-Agent", "ua")

            post_data = call.get("request_post_data")
            lines.extend(
                [
                    f"# Candidate {i}: {call.get('method')} {call.get('url')}",
                    f"url_{i} = {call.get('url')!r}",
                    f"headers_{i} = {headers!r}",
                ]
            )
            if headers.get("User-Agent") == "ua":
                lines.append(f"headers_{i}['User-Agent'] = ua")

            if post_data is not None:
                lines.extend(
                    [
                        f"payload_{i} = {post_data!r}",
                        f"resp_{i} = session.request({call.get('method')!r}, url_{i}, headers=headers_{i}, data=payload_{i}.encode('utf-8'))",
                    ]
                )
            else:
                lines.append(
                    f"resp_{i} = session.request({call.get('method')!r}, url_{i}, headers=headers_{i})"
                )
            lines.extend([f"print('candidate {i}', resp_{i}.status_code, resp_{i}.text[:500])", ""])

        if not web_calls:
            lines.append("# No WebSquare replay candidates were detected in this session.")
        return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record Seibro browser network calls.")
    parser.add_argument("--start-url", default=DEFAULT_START_URL)
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory. Defaults to recorder/sessions/YYYYmmdd_HHMMSS.",
    )
    parser.add_argument(
        "--filter-host",
        action="append",
        default=None,
        help="Host to record. Repeat for multiple hosts. Use --filter-host '' to record all.",
    )
    parser.add_argument("--no-bodies", action="store_true", help="Do not capture response bodies.")
    parser.add_argument("--body-limit", type=int, default=1_000_000)
    parser.add_argument("--poll-interval", type=float, default=0.5)
    parser.add_argument(
        "--keep-browser-open",
        action="store_true",
        help="Leave Chrome open after stopping the recorder.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.filter_host is None:
        filter_hosts = ["seibro.or.kr", "api.seibro.or.kr"]
    elif any(item == "" for item in args.filter_host):
        filter_hosts = []
    else:
        filter_hosts = [item.lower() for item in args.filter_host]

    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = Path(__file__).resolve().parent / "sessions" / stamp

    recorder = SeibroWebRecorder(
        out_dir=out_dir,
        start_url=args.start_url,
        filter_hosts=filter_hosts,
        include_bodies=not args.no_bodies,
        body_limit=args.body_limit,
        poll_interval=args.poll_interval,
        keep_browser_open=args.keep_browser_open,
    )

    print(f"[recorder] output: {out_dir}")
    print(f"[recorder] opening: {args.start_url}")
    recorder.start()
    print("[recorder] Chrome is recording. Use the browser manually.")
    input("[recorder] Press Enter here when you are done...")
    recorder.stop()
    print(f"[recorder] saved: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
