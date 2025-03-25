import uuid
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from observerai.openai import metric_chat_create
from observerai.context import TraceContext

client = OpenAI()

TraceContext.set_trace_id(str(uuid.uuid4()))
TraceContext.set_span_id(str(uuid.uuid4()))
TraceContext.set_flow_id(str(uuid.uuid4()))


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


@metric_chat_create()
def test_openai_with_tool_calls():
    return client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Qual a temperatura atual em Curitiba?"}],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "obter_previsao_tempo",
                    "description": "Obtem a previsão do tempo para uma cidade",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cidade": {
                                "type": "string",
                                "description": "Nome da cidade",
                            }
                        },
                        "required": ["cidade"],
                    },
                },
            }
        ],
        tool_choice="auto",
    )


@metric_chat_create(metadata={"user_id": "456"})
def test_openai_with_full_parameters():
    return client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente contábil."},
            {"role": "user", "content": "Como faço para emitir uma nota fiscal?"},
        ],
        temperature=0.7,
        max_tokens=150,
        top_p=0.95,
        n=1,
        stop=["\n"],
        frequency_penalty=0.2,
        presence_penalty=0.3,
    )


resposta = test_openai_with_metadata()
print(resposta.choices[0].message.content)

resposta = test_openai_without_metadata()
print(resposta.choices[0].message.content)

resposta = test_openai_with_tool_calls()
print(
    resposta.choices[0].message.content if resposta.choices[0].message else "No content"
)

resposta = test_openai_with_full_parameters()
print(
    resposta.choices[0].message.content if resposta.choices[0].message else "No content"
)
