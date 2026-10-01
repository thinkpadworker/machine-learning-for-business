# ML for Business — samshomelab.dev

> A proof-of-skill project built to demonstrate AI agent development using the Anthropic API.

**Live at:** [samshomelab.dev](https://samshomelab.dev)  
**Built by:** King — Computer Information Systems, Simpson College · Indianola, IA

---

## What This Is

An interactive ML agent that solves four real business problems using large language models and prompt engineering — without training a single custom model.

### Capabilities

| Module | Input | Output |
|---|---|---|
| **Sentiment Analysis** | Customer feedback / reviews | Scored sentiment, themes, action items |
| **Report Generator** | Raw data points / meeting notes | Polished executive business report |
| **Risk Scanner** | Business scenario or strategy | Risk rating, top risks, opportunities |
| **KPI Narrative** | Raw metrics / KPIs | Plain-English stakeholder narrative |

---

## Tech Stack

- **Frontend:** HTML, CSS, Vanilla JavaScript (zero dependencies)
- **AI Model:** Claude Sonnet 4.6 via Anthropic API (`/v1/messages`)
- **Production Path:** Python / Flask server-side proxy (see `production/` notes below)
- **Styling:** Simpson College Red (`#C8102E`) & Gold (`#E8A800`)

---

## How It Works

```
User Input → System Prompt + Input → Anthropic API → Structured Output
```

Each capability has a dedicated system prompt that defines:
- The agent's role and expertise
- Expected input format
- Output structure and labeled sections
- Tone (business/stakeholder-ready)

This is the core engineering skill in LLM-based systems: prompt architecture as the ML layer.

---

## Running Locally

Since this is a single HTML file with no build step:

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/ml-for-business.git
cd ml-for-business

# Open directly in browser
open index.html

# Or serve it (optional)
python3 -m http.server 8080
# → http://localhost:8080
```

> **Note:** The demo calls the Anthropic API directly from the browser. For production, move the API call to a server-side proxy to protect your key (see below).

---

## Production Deployment (Flask Proxy)

```python
# app.py
from flask import Flask, request, jsonify
import anthropic, os

app    = Flask(__name__)
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_KEY"])

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json
    msg  = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=data["system"],
        messages=[{"role": "user", "content": data["input"]}]
    )
    return jsonify({"result": msg.content[0].text})
```

Set `ANTHROPIC_KEY` as an environment variable — never hardcode it.

---

## Skills Demonstrated

`API Integration` · `Prompt Engineering` · `Agent Architecture` · `JavaScript async/await` · `HTML & CSS` · `LLM System Design` · `UI/UX Design` · `Python / Flask` · `Error Handling` · `Business Intelligence`

---

## Project Context

Built as part of my portfolio at **samshomelab.dev** while studying Computer Information Systems at **Simpson College** in Indianola, Iowa.

This project proves I can:
- Design and implement a multi-capability AI agent from scratch
- Write production-ready prompt engineering across different business domains
- Build clean, dependency-free frontends
- Architect the production path from prototype to deployed API

---

*Simpson College · The Storm · Est. 1860*
