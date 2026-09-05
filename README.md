# Enterprise Sales Copilot

<p align="center">
  <a href="https://github.com/SalesforceAIResearch/enterprise-sales-copilot"><img src="https://img.shields.io/badge/GitHub-Repository-blue?logo=github" alt="GitHub"></a>
  <a href="Tech-Report/main.pdf"><img src="https://img.shields.io/badge/Paper-PDF-red?logo=adobeacrobatreader" alt="Paper"></a>
  <a href="https://www.apache.org/licenses/LICENSE-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-green.svg" alt="License: Apache 2.0"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" alt="Python 3.11+"></a>
  <a href="https://react.dev"><img src="https://img.shields.io/badge/React-19-blue?logo=react" alt="React 19"></a>
  <a href="https://nextjs.org"><img src="https://img.shields.io/badge/Next.js-16-black?logo=nextdotjs" alt="Next.js 16"></a>
</p>

On a live call, a customer asks about a product and the rep digs in CRM or a knowledge base for 25-65 seconds. This app listens, detects product questions, retrieves answers, and puts a short reply on screen in about 3 seconds. On our 20-question GPT-4o benchmark that is about 14× faster than manual search.

- Streaming STT (Deepgram) + LLM question detection
- FAQ match and LLM-written SQL over a product DB
- OpenAI, Anthropic, or Gemini
- Demo mode with ElevenLabs TTS
- Swap domains by swapping the product database

## Architecture

```
Browser Mic ──→ WebSocket ──→ FastAPI ──→ Deepgram (streaming STT)
                                               │
                                     Conversation Manager (buffer)
                                               │
                                     Question Detector (LLM)
                                               │
                                     Knowledge Retriever (FAQ + SQL)
                                               │
                                     Answer Generator (LLM)
                                               │
                                     WebSocket ──→ React Dashboard
```

## Quick start

Needs Python 3.11+ ([uv](https://docs.astral.sh/uv/)), [Bun](https://bun.sh/) 1.1+, and API keys for [Deepgram](https://deepgram.com), an LLM ([OpenAI](https://openai.com) / Anthropic / Gemini), and optionally [ElevenLabs](https://elevenlabs.io) for demo TTS.

```bash
git clone https://github.com/SalesforceAIResearch/enterprise-sales-copilot.git
cd enterprise-sales-copilot
uv sync
cd frontend && bun install && cd ..
```

Create `credentials.env` in the project root:

```bash
export DEEPGRAM_API_KEY="your-deepgram-key"

export LLM_PROVIDER="openai"       # openai | anthropic | gemini
export LLM_MODEL="gpt-4o"

export OPENAI_API_KEY="your-openai-key"
# export ANTHROPIC_API_KEY="your-anthropic-key"
# export GEMINI_API_KEY="your-gemini-key"

# optional demo TTS
# export ELEVENLABS_API_KEY="your-elevenlabs-key"

# optional OpenAI-compatible gateway
# export OPENAI_BASE_URL="https://your-gateway.com/v1"
```

```bash
# Terminal 1: backend
source credentials.env
uv run uvicorn backend.main:app --reload --port 8000

# Terminal 2: frontend
cd frontend && bun run dev
```

Open http://localhost:3000.

For a remote backend, set `NEXT_PUBLIC_BACKEND_URL` in `frontend/.env.local` to the API HTTP origin (WebSocket URL is derived from it).

| Mode | How |
|------|-----|
| Live | Start Mic, speak. Suggestions appear on the right. |
| Demo | Demo runs a scripted insurance call with voice + suggestions. |
| Text | Type a question in the bottom box (no mic). |

Lint / typecheck:

```bash
uv run ruff check .
uv run ruff format .
uv run ty check
cd frontend && bun run lint
```

## Benchmark

20 questions, 6 categories, GPT-4o, vs an internal CRM study for manual search:

| Metric | Manual | Copilot |
|--------|--------|---------|
| Avg response time | 39.7s | 2.8s |
| Std. dev. | 12-18s | 0.5s |
| Questions detected | — | 20/20 |

## Sample data (insurance)

50 products across 10 categories (life, health, auto, home, travel, disability, dental, vision, pet, business): ~2,490 FAQs, 290 coverage rows, 162 pricing tiers.

```bash
source credentials.env && uv run python scripts/generate_large_db.py
```

Other domain: replace `seed_data/insurance_products.json`.

## Citation

```bibtex
@article{qiu2025salescopliot,
  title={Enterprise Sales Copilot: Enabling Real-Time AI Support with Automatic Information Retrieval in Live Sales Calls},
  author={Qiu, Jielin and Yang, Liangwei and Zhu, Ming and Zhao, Wenting and Liu, Zhiwei and Tan, Juntao and Chen, Zixiang and Ram, Roshan and Prabhakar, Akshara and Murthy, Rithesh and Heinecke, Shelby and Xiong, Caiming and Savarese, Silvio and Wang, Huan},
  year={2025},
  institution={Salesforce AI Research}
}
```

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.

## Deployed hackathon demo

Open https://enterprise-sales-copilot-gamma.vercel.app and select Demo, or type a question. Live microphone mode requires browser microphone permission.

The deployed LLM is Gemini `gemini-3.5-flash-lite`, traced through PRISMtrace. Set `GEMINI_API_KEY` or `GOOGLE_API_KEY`, `LLM_PROVIDER=gemini`, and `LLM_MODEL=gemini-3.5-flash-lite` in `credentials.env`. The OpenAI key previously returned an exhausted-credit error.

After changing credentials, update the Modal secret and redeploy from the repository root:

```bash
uv run --with modal modal secret create sales-copilot --from-dotenv credentials.env --force
uv run --with modal modal deploy backend/modal_app.py
bunx vercel@latest --prod --yes
```

Run the Vercel command from the repository root because the linked project uses `frontend` as its root directory. PRISMtrace is LLM tracing; this repository uses SQLite directly and does not include Prisma ORM.
