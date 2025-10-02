# Работа и реализация скрипта format_for_json.py

## Описание

Скрипт format_for_json.py предназначен для преобразования текста с пронумерованными списками в формат JSON. Преобразует входной текстовый файл, где каждая строка начинается с номера (например, 1., 2., и так далее), в файл JSON, где каждая строка представлена как объект с полями id и payload.

## Программный код: 

```python
import re
import json
import argparse
from pathlib import Path

# Регулярное выражение для поиска записей в формате '1. payload'
ENTRY_RE = re.compile(r'(?m)^\s*(\d+)\.\s*(.*?)\s*(?=^\s*\d+\.|\Z)', re.S)  # Жесткая регулярка

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
        idx = int(match.group(1))  # Извлекаем номер записи
        payload = match.group(2)   # Извлекаем текст payload
        payload = payload.strip()  # Убираем лишние пробелы и символы новой строки
        items.append({'id': idx, 'payload': payload})  # Добавляем в список
    return items

def main():
    parser = argparse.ArgumentParser(description='Парсит пронумерованный список в файл JSON')
    parser.add_argument('input_file', type=Path, help='Входной файл с пронумерованным списком')
    parser.add_argument('output_file', type=Path, help='Выходной JSON файл')
    parser.add_argument('--pretty', action='store_true', help='Форматировать JSON для удобочитаемости')
    args = parser.parse_args()

    # Проверяем, существует ли файл
    if not args.input_file.exists():
        print(f"Ошибка: файл не найден: {args.input_file}")
        return

    # Читаем текст из файла
    text = args.input_file.read_text(encoding='utf-8')
    items = parse_numbered_list(text)

    # Если нет данных, выводим предупреждение
    if not items:
        print("Внимание: не найдено записей. Убедись, что формат: '1. payload' на отдельных строках.")
    
    # Записываем результаты в файл
    with args.output_file.open('w', encoding='utf-8') as f:
        if args.pretty:
            json.dump(items, f, ensure_ascii=False, indent=4)  # Форматируем JSON для удобочитаемости
        else:
            json.dump(items, f, ensure_ascii=False)  # Без форматирования

    print(f"Готово: записано {len(items)} записей в {args.output_file}")

if __name__ == '__main__':
    main()
```

## Описание работы скрипта


1. **Чтение входного файла**: Скрипт ожидает файл с текстом, где каждая строка начинается с номера, например:

```markdown
1. Запрос 1  
2. Запрос 2  
3. Запрос 3 
```

2. **Парсинг данных**: Скрипт использует регулярное выражение для поиска строк, которые начинаются с числа и точки, после которых идет сам текст записи (payload). Все данные сохраняются в формате:

```json
{
  "id": "номер записи",
  "payload": "содержимое строки"
}
```

3. **Запись в выходной файл JSON**: После обработки все записи выводятся в формате JSON в указанный выходной файл. В случае использования флага --pretty форматирование JSON будет сделано для удобочитаемости (с отступами).

### Пример формата JSON:

```json
[
    {
        "id": 1,
        "payload": "Запрос 1"
    },
    {
        "id": 2,
        "payload": "Запрос 2"
    },
    {
        "id": 3,
        "payload": "Запрос 3"
    }
]
```

### Параметры командной строки

input_file (обязательный параметр): Путь к входному файлу с пронумерованным списком.

output_file (обязательный параметр): Путь к выходному JSON файлу, куда будут записаны результаты.

--pretty (необязательный параметр): Если указан, JSON будет отформатирован для лучшей читаемости (с отступами).

### Пример использования

1. Без форматирования:

```bash
python format_for_json.py input.txt output.json
```
2. С форматированием:

```bash
python format_for_json.py input.txt output.json --pretty
```

### Примечания

Важно, чтобы входной файл следовал формату номер. текст, где текст может быть как однострочным, так и многострочным (до следующего числа с точкой).

Скрипт также проверяет наличие входного файла и выводит предупреждения, если входные данные не соответствуют ожидаемому формату.