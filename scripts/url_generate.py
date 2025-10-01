#!/usr/bin/env python3
"""
url_generator.py

Читает словарь (txt), подставляет слова в URL-шаблон с {word} и {time},
сохраняет сгенерированные URL в файл. Опционально — выполняет GET-запросы
с несколькими режимами задержки и глобальным rate-limit.

Этическое предупреждение: по умолчанию запросы НЕ отправляются. Включайте --send
только для тестирования на ресурсах, где у вас есть разрешение.
"""

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import List
import concurrent.futures
from threading import Lock
from urllib.parse import quote_plus

try:
    import requests
except Exception:
    requests = None

# для глобального rate limit
_last_call = 0.0
_last_lock = Lock()

def read_wordlist(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return [line.strip() for line in f if line.strip()]

def format_time(user_time: str, time_format: str) -> str:
    if user_time.lower() == "now":
        return datetime.now().strftime(time_format)
    try:
        epoch = int(user_time)
        return datetime.fromtimestamp(epoch).strftime(time_format)
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(user_time, fmt).strftime(time_format)
        except Exception:
            continue
    return user_time  # literal

def generate_urls(words: List[str], url_template: str, time_str: str) -> List[str]:
    urls = []
    for w in words:
        safe_word = quote_plus(w, encoding="utf-8", errors="ignore")
        u = url_template.replace("{word}", safe_word).replace("{time}", time_str)
        urls.append(u)
    return urls

def save_urls(urls: List[str], out_path: Path):
    with out_path.open("w", encoding="utf-8") as f:
        for u in urls:
            f.write(u + "\n")

def fetch_url(session, url, timeout=10, delay_mode=0, delay=0.0):
    """
    delay_mode:
      0 - no extra delay (fire immediately)
      1 - per-thread delay before request (time.sleep(delay) inside each task)
      2 - global strict rate limit (ensure at least `delay` seconds between real GETs)
    """
    global _last_call
    try:
        if delay_mode == 1 and delay:
            time.sleep(delay)
        elif delay_mode == 2 and delay:
            with _last_lock:
                now = time.time()
                wait = delay - (now - _last_call)
                if wait > 0:
                    time.sleep(wait)
                _last_call = time.time()

        r = session.get(url, timeout=timeout)
        return url, r.status_code, len(r.content)
    except Exception as e:
        return url, "ERR", str(e)

def main():
    p = argparse.ArgumentParser(description="Генератор URL из словаря и времени.")
    p.add_argument("--wordlist", "-w", required=True, help="путь к txt (по одному слову в строке)")
    p.add_argument("--template", "-t", required=True,
                   help="URL-шаблон с {word} и {time}, напр.: 'http://dvwa.local/vulnerabilities/sqli?id={word}&ts={time}'")
    p.add_argument("--time", "-T", default="now",
                   help="время: 'now', unix epoch или ISO (YYYY-MM-DDTHH:MM:SS) или literal")
    p.add_argument("--time-format", "-f", default="%Y-%m-%dT%H:%M:%S",
                   help="strftime формат для подстановки времени")
    p.add_argument("--out", "-o", default="generated_urls.txt", help="файл для записи URL")
    p.add_argument("--send", action="store_true", help="выполнять GET запросы (по умолчанию OFF)")
    p.add_argument("--delay", type=float, default=1.0, help="пауза в секундах (см. --delay-mode)")
    p.add_argument("--workers", type=int, default=4, help="параллельных потоков для отправки")
    p.add_argument("--max-urls", type=int, default=0, help="максимум URL для генерации (0 = все)")
    p.add_argument("--delay-mode", type=int, choices=[0,1,2], default=2,
                   help="0=no delay, 1=per-thread pre-request sleep, 2=global strict rate limit (default)")
    args = p.parse_args()

    wl = Path(args.wordlist)
    if not wl.exists():
        print("Файл словаря не найден:", wl)
        return

    words = read_wordlist(wl)
    if args.max_urls > 0:
        words = words[:args.max_urls]

    time_str = format_time(args.time, args.time_format)
    urls = generate_urls(words, args.template, time_str)
    save_urls(urls, Path(args.out))
    print(f"Сгенерировано {len(urls)} URL, сохранено в {args.out}")

    if args.send:
        if requests is None:
            print("requests не установлен. Установите: pip install requests")
            return

        print("=== ВНИМАНИЕ: отправка запросов включена (--send). Убедитесь, что у вас есть разрешение! ===")
        session = requests.Session()
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = [ex.submit(fetch_url, session, u, 10, args.delay_mode, args.delay) for u in urls]
            for fut in concurrent.futures.as_completed(futures):
                url, status, info = fut.result()
                results.append((url, status, info))
                print(url, status, info)
        print("Отправлено. Всего:", len(results))

if __name__ == "__main__":
    main()
