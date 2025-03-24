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
