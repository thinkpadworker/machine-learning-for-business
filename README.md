# ML for Business — samshomelab.dev

> A proof-of-skill project built to demonstrate AI agent development with a free, open-source model, a Flask backend, and prompt engineering.

**Live at:** [samshomelab.dev](https://samshomelab.dev)
**Built by:** King — Computer Information Systems, Simpson College · Indianola, IA

---

## What This Is

An interactive agent that solves business problems with a large language model and prompt engineering — without training a custom model. The featured demo is a **Senior Health Risk Scanner** for health insurers.

| Module | Input | Output |
|---|---|---|
| **Senior Health Risk** (featured) | A fictional senior member or member group | Risk tier, top drivers, cost pain points, care-management moves, next steps |
| **Sentiment Analysis** | Customer feedback / reviews | Scored sentiment, themes, action items |
| **Report Generator** | Raw data points / meeting notes | Executive business report |
| **KPI Narrative** | Raw metrics / KPIs | Plain-English stakeholder narrative |

The scanner is framed as outreach and care-management support. It is not for coverage, eligibility, or pricing decisions, and the demo should only be given fictional scenarios.

---

## Tech Stack

- **Frontend:** HTML, CSS, vanilla JavaScript (no dependencies)
- **Backend:** Python / Flask
- **Model:** any model served by [Ollama](https://ollama.com), default `llama3.2:3b`
- **Styling:** Simpson College Red (`#C8102E`) and Gold (`#E8A800`)

---

## How It Works

```
Browser → Flask (/api/analyze) → Ollama (localhost:11434) → streamed text → Browser
```

- The browser sends only `{ module, input }`. The system prompts live in `prompts.py`, so visitors can't turn the endpoint into a free general chatbot.
- Flask validates input, rate-limits per IP, caps simultaneous generations, and streams tokens back as they're written.
- `/api/health` tells the page whether the agent is actually up; the status chip in the hero reflects it.

---

## Running Locally

```bash
# 1. Install Ollama (https://ollama.com), then pull a model
ollama pull llama3.2:3b

# 2. Install the Python dependencies
pip install -r requirements.txt

# 3. Start the site
python app.py
# → http://localhost:5000
```

Open the site through Flask. Opening `index.html` directly or through Live Server won't work, because the page calls `/api/...` on the same origin.

### Settings (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_MODEL` | `llama3.2:3b` | Model to use. Any model you've pulled works. |
| `OLLAMA_URL` | `http://localhost:11434` | Where Ollama is listening |
| `RATE_LIMIT_PER_MIN` | `6` | Requests per visitor per minute |
| `MAX_CONCURRENT` | `2` | Generations allowed at once |
| `MAX_INPUT_CHARS` | `3000` | Longest input accepted |
| `MAX_NEW_TOKENS` | `800` | Longest response |
| `READ_TIMEOUT_SECONDS` | `120` | How long to wait on the model |
| `TRUST_PROXY` | `0` | Set to `1` behind Cloudflare Tunnel or nginx so rate limits use the real visitor IP |
| `PORT` | `5000` | Port Flask listens on |

---

## Making It Public

Flask and Ollama must run on a machine you control, so the site can't be hosted on a static host such as GitHub Pages.

```bash
TRUST_PROXY=1 gunicorn -w 1 --threads 8 -b 127.0.0.1:5000 app:app
```

- Keep `-w 1`. The rate limiter and concurrency cap live in memory inside one process.
- Keep Ollama on `localhost`. Only expose Flask, for example through a Cloudflare Tunnel pointed at `127.0.0.1:5000`.
- If you use nginx, turn off response buffering for `/api/analyze` so streaming works (the app already sends `X-Accel-Buffering: no`).

### Picking a model

| Hardware | Suggested model |
|---|---|
| CPU only, 8 GB RAM | `llama3.2:3b` (default) |
| CPU or small GPU, 16 GB RAM | `qwen2.5:7b` or `llama3.1:8b` |
| GPU with 8 GB+ VRAM | `llama3.1:8b` — noticeably faster and better at following the format |

The server loads the model into memory at startup, so the first visitor doesn't wait on it.

---

## Project Files

```
app.py            Flask server: routes, validation, rate limit, streaming
prompts.py        System prompt for each module
index.html        The whole frontend
requirements.txt  Python dependencies
```

---

## Skills Demonstrated

`Python / Flask` · `API Design` · `Streaming Responses` · `Prompt Engineering` · `Open-Source LLMs (Ollama)` · `Rate Limiting` · `Agent Architecture` · `JavaScript async/await` · `HTML & CSS` · `Error Handling` · `Business Intelligence`

---

*Simpson College · The Storm · Est. 1860*
