from google import genai

from observerai.gemini import metric_generate_content

client = genai.Client()


@metric_generate_content(metadata={"feature": "demo"})
def ask(q: str):
    return client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[q],
    )


print(ask("Hello Gemini").text)
