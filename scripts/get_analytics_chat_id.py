#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Получить chat id для ANALYTICS_CHAT_ID из последних getUpdates.

Требуется в .env корректный BOT_TOKEN (тот же, с которым запущен бот).
Запуск из корня проекта:

  PYTHONPATH=src python scripts/get_analytics_chat_id.py

Или без правки .env (токен только в окружении этой сессии):

  BOT_TOKEN='ваш_токен' PYTHONPATH=src python scripts/get_analytics_chat_id.py

Опционально — искать сообщение с точным текстом:

  PYTHONPATH=src python scripts/get_analytics_chat_id.py --match "ыаыаыаываываываыаыав"

Перед getUpdates снимается webhook (если был), иначе очередь апдейтов пустая.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def _load_bot_token() -> str | None:
    if os.getenv("BOT_TOKEN"):
        return os.getenv("BOT_TOKEN")
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip() == "BOT_TOKEN":
                return val.strip().strip('"').strip("'") or None
    return os.getenv("BOT_TOKEN")


def _api(token: str, method: str, params: dict | None = None) -> dict:
    from urllib.parse import urlencode

    base = f"https://api.telegram.org/bot{token}/{method}"
    url = base + ("?" + urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"User-Agent": "ProjectUnicorn-get-chat-id"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main() -> int:
    parser = argparse.ArgumentParser(description="Получить chat id для ANALYTICS_CHAT_ID")
    parser.add_argument(
        "--match",
        metavar="TEXT",
        help="Точное совпадение текста входящего сообщения (последнее совпадение)",
    )
    args = parser.parse_args()

    token = _load_bot_token()
    if not token or "replace_with" in token.lower() or len(token) < 20:
        print(
            "Ошибка: не найден настоящий BOT_TOKEN от @BotFather.\n"
            "Задайте в .env строку BOT_TOKEN=123456789:AAH... или один раз в терминале:\n"
            "  BOT_TOKEN='...' PYTHONPATH=src python scripts/get_analytics_chat_id.py",
            file=sys.stderr,
        )
        return 1

    try:
        _api(token, "deleteWebhook", {"drop_pending_updates": "false"})
    except urllib.error.HTTPError:
        pass

    try:
        data = _api(token, "getUpdates", {"limit": "100"})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"Ошибка Telegram API ({e.code}): {body[:500]}", file=sys.stderr)
        return 1

    if not data.get("ok"):
        print("Ответ API не ok:", data, file=sys.stderr)
        return 1

    updates = data.get("result") or []
    if not updates:
        print(
            "Апдейтов нет. Напишите боту любое сообщение в нужном чате и запустите скрипт снова.",
            file=sys.stderr,
        )
        return 2

    needle = args.match
    chosen = None
    if needle is not None:
        for u in reversed(updates):
            msg = u.get("message") or u.get("edited_message") or {}
            if (msg.get("text") or "").strip() == needle:
                chosen = msg.get("chat")
                break
        if chosen is None:
            print(
                f"Сообщение с текстом {needle!r} не найдено в последних апдейтах. "
                "Показываю последний апдейт.",
                file=sys.stderr,
            )

    if chosen is None:
        last = updates[-1]
        msg = last.get("message") or last.get("edited_message") or {}
        chosen = msg.get("chat") or {}

    cid = chosen.get("id")
    ctype = chosen.get("type")
    title = chosen.get("title") or chosen.get("username") or chosen.get("first_name") or ""

    if cid is None:
        print("Не удалось извлечь chat id из апдейтов.", file=sys.stderr)
        return 3

    print()
    print("Добавьте в .env (или Railway Variables):")
    print()
    print(f"ANALYTICS_CHAT_ID={cid}")
    print()
    print(f"# chat_type={ctype!r}  label={title!r}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
