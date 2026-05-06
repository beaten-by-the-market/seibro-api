# Seibro Web Recorder

Manual recorder for discovering Seibro WebSquare calls.

It opens Chrome with Selenium, navigates to Seibro, and records Chrome DevTools
Protocol network events while you operate the site by hand. The output is meant
to be inspected later and converted into stable API-style Python functions.

## Install

```bash
pip install -r recorder/requirements.txt
```

Selenium Manager will try to find or download a compatible ChromeDriver
automatically. You need Chrome installed.

## Record A Session

```bash
python recorder/seibro_recorder.py
```

Chrome opens at:

```text
https://seibro.or.kr/
```

Use the browser manually. When you are done, return to the terminal and press
Enter. The recorder writes files under `recorder/sessions/<timestamp>/`.

Useful options:

```bash
python recorder/seibro_recorder.py --start-url "https://seibro.or.kr/websquare/control.jsp?w2xPath=/IPORTAL/user/company/BIP_CNTS01021V.xml&menuNo=19"
python recorder/seibro_recorder.py --filter-host seibro.or.kr --filter-host api.seibro.or.kr
python recorder/seibro_recorder.py --no-bodies
python recorder/seibro_recorder.py --body-limit 2000000
```

## Output

- `network_events.jsonl`: raw-ish CDP network events, one JSON object per line.
- `requests.json`: normalized request/response records keyed by CDP request id.
- `web_calls.json`: likely reusable Seibro calls, especially WebSquare XML POSTs.
- `cookies.json`: browser cookies at the end of the session.
- `replay_candidates.py`: generated starter snippets using `requests`.

## Workflow

1. Start the recorder.
2. Navigate the Seibro page by hand and trigger the data you want.
3. Stop the recorder with Enter in the terminal.
4. Inspect `web_calls.json` and `replay_candidates.py`.
5. Move the stable call into the main package once the payload is understood.

