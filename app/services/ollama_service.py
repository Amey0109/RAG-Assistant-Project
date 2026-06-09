import ollama
import json
from app.config import OLLAMA_MODEL


def call_ollama(prompt: str, stream: bool = False):
    ollama_options = {
        "temperature": 0.15,
        "num_predict": 350
    }

    if stream:
        def generate():
            try:
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

                for chunk in ollama_stream:
                    content = chunk["message"]["content"]

                    if content:
                        yield content.encode("utf-8")

                yield b"\n"

            except GeneratorExit:
                print("\nClient disconnected from stream.")

            except Exception as error:
                error_message = f"\n\n[Streaming error: {str(error)}]"
                print(error_message)
                yield error_message.encode("utf-8")

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


def call_ollama_sse(prompt: str):
    ollama_options = {
        "temperature": 0.15
    }

    def generate():
        try:
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

            for chunk in ollama_stream:
                content = chunk["message"]["content"]

                if content:
                    yield f"data: {json.dumps({'content': content})}\n\n"

            yield "event: done\ndata: {}\n\n"

        except Exception as error:
            yield f"event: error\ndata: {json.dumps({'error': str(error)})}\n\n"

    return generate()