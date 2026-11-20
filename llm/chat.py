#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.getenv("LLAMA_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
MODEL = os.getenv("LLAMA_MODEL", "gemma-4-26b-a4b-it")
SYSTEM_PROMPT_FILE = Path(__file__).resolve().with_name("system_prompt.txt")



def read_system_prompt() -> str:
    try:
        return SYSTEM_PROMPT_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise SystemExit(f"Не найден файл системного промта: {SYSTEM_PROMPT_FILE}") from exc


def stream_chat(messages: list[dict[str, str]]) -> str:
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": True,
    }
    request = Request(
        f"{BASE_URL}/v1/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    answer_parts: list[str] = []
    try:
        with urlopen(request, timeout=3600) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue

                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                if not data:
                    continue

                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue

                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                piece = delta.get("content")
                if isinstance(piece, str) and piece:
                    print(piece, end="", flush=True)
                    answer_parts.append(piece)

    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {details}") from exc
    except URLError as exc:
        raise RuntimeError(
            f"Не удалось подключиться к {BASE_URL}. Подробности: {exc}"
        ) from exc

    print()
    return "".join(answer_parts).strip()


def main() -> None:
    system_prompt = read_system_prompt()
    history: list[dict[str, str]] = []

    print(f"Подключение к {BASE_URL}")
    print(f"Системный промт: {SYSTEM_PROMPT_FILE.name}")
    print("Команды: /reset — очистить диалог, /reload — перечитать промт, /exit — выйти")

    while True:
        try:
            user_text = input("Ты: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break

        if not user_text:
            continue
        command = user_text.lower()
        if command in {"/exit", "/quit"}:
            break
        if command == "/reset":
            history.clear()
            continue
        if command == "/reload":
            system_prompt = read_system_prompt()
            continue

        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": user_text},
        ]

        print("ИИ-агент: ", end="", flush=True)
        try:
            answer = stream_chat(messages)
        except RuntimeError as exc:
            print(f"\nОшибка: {exc}\n", file=sys.stderr)
            continue

        if answer:
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": answer})
        print()


if __name__ == "__main__":
    main()
