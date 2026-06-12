import ollama
import json
from app.config import OLLAMA_MODEL, OLLAMA_HOST


def _get_client():
    return ollama.Client(host=OLLAMA_HOST)


def call_ollama(prompt: str, stream: bool = False):
    client = _get_client()
    ollama_options = {
        "temperature": 0.15,
        "num_predict": 350
    }

    if stream:
        def generate():
            try:
                ollama_stream = client.chat(
                    model=OLLAMA_MODEL,
                    messages=[{"role": "user", "content": prompt}],
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
                yield f"\n\n[Streaming error: {str(error)}]".encode("utf-8")
        return generate()

    response = client.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        options=ollama_options,
        keep_alive="10m"
    )
    return response["message"]["content"]


def call_ollama_sse(prompt: str):
    client = _get_client()
    ollama_options = {
        "temperature": 0.15
    }

    def generate():
        try:
            ollama_stream = client.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
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