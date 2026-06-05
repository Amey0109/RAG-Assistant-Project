import ollama

from app.config import OLLAMA_MODEL


def call_ollama(prompt: str, stream: bool = False):
    ollama_options = {
        "temperature": 0.15
    }

    if stream:
        ollama_stream = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            stream=True,
            options=ollama_options,
            keep_alive="10m"
        )

        def generate():
            for chunk in ollama_stream:
                content = chunk["message"]["content"]
                yield content

        return generate()

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        stream=False,
        options=ollama_options,
        keep_alive="10m"
    )

    return response["message"]["content"]