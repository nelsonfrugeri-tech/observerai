# 📦 observerai – Structured Observability for Generative AI
> observerai is a Python library that enables runtime observability and evaluation Log-as-Metric for Generative AI applications.

It is designed to be multi-provider (OpenAI, Gemini, Claude, etc.) and multi-modal (text, image, embeddings).

All metrics are emitted as structured logs following the Log-as-Metric approach, allowing seamless integration with platforms like GCP, Datadog, New Relic, Elastic, and others.

## ✅ Features
- 📊 Structured metric logging for LLM usage  
- 🧵 Trace & span context via `contextvars` (thread-safe)  
- ⏱️ Latency & token usage tracking  
- 🧠 Prompt/response capture  
- 🚨 Exception tracing  
- 🧩 Flexible decorator interface  
- 🔧 Custom `metadata` support  
- 🧱 Built on top of `pydantic` and `structlog`

## ⚙️ Installation
```bash
pip install observerai[openai]
```
> Only the OpenAI dependency is included for now. Future versions will support gemini, claude, etc.

## 🚀 How to Use
>In your application, just decorate the function that makes OpenAI requests:
```python
import uuid
from openai import OpenAI
from observerai.openai import metric_chat_create
from observerai import set_ids

# Optionally set your trace IDs (thread-safe)
set_ids(trace_id=str(uuid.uuid4()))

client = OpenAI()

@metric_chat_create(metadata={"user_id": "123"})
def call_openai():
    return client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Qual a capital da França?"}]
    )

response = call_openai()
print(response.choices[0].message.content)
```

## 📤 Output (Structured Log)
The decorator logs all metrics as a single structured JSON object to stdout:
```bash
{
  "trace_id": "123",
  "flow_id": null,
  "span_id": null,
  "response": {
    "status_code": 200,
    "latency": {
      "time": 481,
      "unit": "ms"
    }
  },
  "exception": null,
  "version": "0.0.1",
  "metadata": {
    "user_id": "123"
  },
  "name": "gpt-3.5-turbo",
  "provider": "openai",
  "endpoint": "/chat/completions",
  "conversation": {
    "question": "Qual a capital da França?",
    "answer": "A capital da França é Paris."
  },
  "token": {
    "prompt": 14,
    "completion": 9,
    "total": 23
  },
  "evaluation": null,
  "event": "observerai.openai.completion",
  "level": "info",
  "timestamp": "2025-03-24T19:21:08.115226Z"
}
```

## 🧭 Roadmap
- [x] OpenAI support (text completions)
- [ ] Gemini & Claude providers
- [ ] RAG evaluations (RagasX)
- [ ] Plug-and-play LLM evaluations via TruLens

## 👥 Contributing
PRs and discussions are welcome. Stay tuned for contribution guidelines and plugin architecture.