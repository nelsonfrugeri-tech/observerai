from openai import OpenAI
from observerai import openai_completion

client = OpenAI()

@openai_completion
def chamar_openai(client=None):
    return client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Qual a capital da França?"}]
    )

resposta = chamar_openai(client=client)
print(resposta.choices[0].message.content)
