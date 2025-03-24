# 📊 observerai

**ObserverAI** is a lightweight observability library for applications using Generative AI models. It focuses on capturing, logging, and structuring metrics from LLM calls — starting with OpenAI support.

Designed for extensibility and simplicity, ObserverAI requires minimal setup while enabling rich insights through structured logging (Log-as-Metric pattern).

---

## ✨ Features

- ✅ Easy-to-use `decorator` to monitor any function calling an LLM
- ⚙️ Native support for **OpenAI ChatCompletion**
- 📊 Structured logs with `structlog` (JSON format)
- 🔎 Captures:
  - Model name
  - Prompt and completion
  - Token usage (prompt, completion, total)
  - Response latency
  - HTTP status
  - Exceptions
- 🌐 Designed for cloud-native logging tools (e.g., GCP Logging, Datadog, Loki)
- 🧩 Future support for RAG pipelines, vector stores, and evaluation frameworks

---

## 🚀 Installation

```bash
pip install observerai[openai]
