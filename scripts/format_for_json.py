import re
import json
import argparse
from pathlib import Path

ENTRY_RE = re.compile(r'(?m)^\s*(\d+)\.\s*(.*?)\s*(?=^\s*\d+\.|\Z)', re.S) #Жесткая регулярка

def parse_numbered_list(text: str):
    """
    Находит записи вида:
    1. payload...
    2. payload...
    Каждая запись может быть многострочной — до следующего '<число>.'
    Возвращает список dict: {'id': int, 'payload': str}
    """
    items = []
    for match in ENTRY_RE.finditer(text):
        idx = int(match.group(1))
        payload = match.group(2)  
        payload = payload.strip()   # Убираем ведущие/концевые пробелы и переводы строк с сохр внутренних 
        items.append({'id': idx, 'payload': payload})
    return items

def main():
    parser = argparse.ArgumentParser(description='Парсит пронумерованный список в файл JSON')
    parser.add_argument('input_file', type=Path, help='Входной файл с пронумерованным списком')
    parser.add_argument('output_file', type=Path, help='Выходной JSON файл')
    parser.add_argument('--pretty', action='store_true', help='Форматировать JSON для удобочитаемости')
    args = parser.parse_args()

    if not args.input_file.exists():
        print(f"Ошибка: файл не найден: {args.input_file}")
        return

    text = args.input_file.read_text(encoding='utf-8')
    items = parse_numbered_list(text)

    if not items:
        print("Внимание: не найдено записей. Убедись, что формат: '1. payload' на отдельных строках.")
    with args.output_file.open('w', encoding='utf-8') as f:
        if args.pretty:
            json.dump(items, f, ensure_ascii=False, indent=4)
        else:
            json.dump(items, f, ensure_ascii=False)
    print(f"Готово: записано {len(items)} записей в {args.output_file}")

if __name__ == '__main__':
    main()
