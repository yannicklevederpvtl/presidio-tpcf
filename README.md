# presidio-webhook

Flask webhook that anonymizes PII in OpenAI-style chat completion payloads using [Microsoft Presidio](https://microsoft.github.io/presidio/) and spaCy (`en_core_web_lg`).

Intended for use as a request/response interceptor (for example, with an AI gateway) that rewrites message content before it reaches a model or client.

## Endpoints

| Method | Path | Behavior |
|--------|------|----------|
| `POST` | `/prompt` | Anonymizes `messages[].content` in a chat completion **request** |
| `POST` | `/response` | Anonymizes `choices[].message.content` in a chat completion **response** |

Both endpoints expect JSON and return the same structure with sensitive spans replaced (for example names, phone numbers, emails).

### Example — `/prompt`

```bash
curl -s -X POST "http://localhost:8080/prompt" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Call John Smith at +1-555-0100 or email john@example.com"}
    ]
  }'
```

## Requirements

- Python **3.10** only (`requires-python` and `runtime.txt` → `3.10.20`)
- [uv](https://docs.astral.sh/uv/) for local install and CF staging

> spaCy 3.7 / thinc need **numpy 1.x**. Do not allow Python ≥3.11 or numpy 2 — that causes `numpy.dtype size changed` crashes at startup.

## Local development

```bash
uv sync
uv run python presidio-webhook.py
```

App listens on `0.0.0.0:$PORT` (default **8080**).

First sync downloads `en_core_web_lg` (~560 MB); later runs reuse the lockfile and cache.

## Deploy to Cloud Foundry

This project uses **uv mode** for the Python buildpack:

| Uploaded | Purpose |
|----------|---------|
| `pyproject.toml` + `uv.lock` | Dependencies (`uv sync`) |
| `runtime.txt` | Python `3.10.20` |
| `Procfile` | `uv run python presidio-webhook.py` |
| `.cfignore` | Excludes `requirements.txt` so CF does not mix pip and uv |

```bash
cf target   # confirm org/space
cf push
```

Manifest defaults (`manifest.yml`):

- App name: `presidio-webhook`
- Memory: **2G** (needed for spaCy large model at staging/runtime)
- Disk: **4G**
- Buildpack: `python_buildpack`

After push:

```bash
cf apps
cf logs presidio-webhook --recent
curl -s -X POST "https://presidio-webhook.apps.<domain>/prompt" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"My SSN is 123-45-6789"}]}'
```

## Project layout

```
presidio-webhook.py   # Flask app
pyproject.toml        # Dependencies (uv)
uv.lock               # Locked versions
runtime.txt           # CF Python version
Procfile              # Start command
manifest.yml          # CF app sizing
.cfignore             # Keep pip requirements.txt off the droplet
requirements.txt      # Local/legacy reference only (not uploaded)
```

## Notes

- Engines load at process start; cold start can take a while on first request after deploy.
- If staging OOMs while fetching `en_core_web_lg`, raise memory in `manifest.yml` (2G has worked) or switch to `en_core_web_sm` / `en_core_web_md`.
- If the CF API returns 503/404 mid-push after a successful stage, retry `cf push` — that is platform connectivity, not an app packaging error.
