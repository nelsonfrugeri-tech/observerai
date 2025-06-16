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
from observerai.context import TraceContext

client = OpenAI()
TraceContext.set_trace_id(str(uuid.uuid4()))


@metric_chat_create(metadata={"user_id": "123"})
def test_openai_with_metadata():
    return client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Qual a capital da França?"}],
    )


@metric_chat_create()
def test_openai_without_metadata():
    return client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Qual a capital da Argentina?"}],
    )


resposta = test_openai_with_metadata()
print(resposta.choices[0].message.content)

resposta = test_openai_without_metadata()
print(resposta.choices[0].message.content)

```

## 📤 Output (Structured Log)
The decorator logs all metrics as a single structured JSON object to stdout:
```bash
{
  "trace_id": "fadfd7d6-9150-4327-961f-dad5f048add1",
  "span_id": "c346b100-30d8-4eea-91e3-ddcc67d8d5e0",
  "flow_id": "d52f542f-2211-45e6-94ca-a6d55617787e", 
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
  "name": "gpt-4o",
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
  "event": "observerai.openai.completion.chat_create",
  "level": "info",
  "timestamp": "2025-03-24T19:21:08.115226Z"
}
```

Conversation example when use tools
```bash
{
  "conversation": {
    "question": {
      "content": "Como está o clima em São Paulo hoje?",
      "role": "user",
      "tools": [
        {
          "type": "function",
          "function": {
            "name": "get_clima",
            "description": "Obtém informações meteorológicas de uma cidade",
            "parameters": {
              "type": "object",
              "properties": {
                "cidade": {
                  "type": "string",
                  "description": "Nome da cidade"
                }
              },
              "required": ["cidade"]
            }
          }
        }
      ]
    },
    "answer": {
      "content": null,
      "role": "assistant",
      "tool_calls": [
        {
          "id": "call_123456789",
          "type": "function",
          "function": {
            "name": "get_clima",
            "arguments": "{\"cidade\": \"São Paulo\"}"
          }
        }
      ]
    }
  }
}
```

## 🧭 Roadmap
- [x] OpenAI support (chat completions)
- [x] Gemini provider
- [ ] RAG evaluations (RagasX)
- [ ] Models evaluations (OpenAI and Gemini)
- [ ] Async suport
- [ ] Anthropic providers
- [ ] OpenSource models

[Pypi Project](https://pypi.org/project/observerai/0.1.0a2/)

## 👥 Contributing
PRs and discussions are welcome. Stay tuned for contribution guidelines and plugin architecture.