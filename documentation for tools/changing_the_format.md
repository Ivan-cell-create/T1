# Работа и реализация скрипта changing_the_format.py

## Описание 

Этот скрипт предназначен для конвертации текстового файла с пронумерованным списком (1. payload, 2. payload, …) в структурированный JSON-файл, где каждая запись будет представлена как объект с id и payload.

## Программный код:

```python
import json
import os
from format.transforms import TRANSFORMS  

def transform_payloads(json_data, transform_name):
    transform_func = TRANSFORMS.get(transform_name)
    if transform_func is None:
        raise ValueError(f"Преобразование {transform_name} не найдено")
    outputs = []
    for entry in json_data:
        payload = entry.get('payload', '')
        try:
            transformed = transform_func(payload)
        except Exception:
            transformed = payload
        outputs.append(transformed)
    return outputs

def main(json_filepath, transform_name):
    # Читаем json
    with open(json_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Преобразуем payloads
    transformed_payloads = transform_payloads(data, transform_name)

    # Создаем папку tests на уровень выше текущей директории скрипта
    tests_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tests'))
    os.makedirs(tests_dir, exist_ok=True)

    # Формируем имя файла и путь
    filename = f"json_{transform_name}.txt"
    filepath = os.path.join(tests_dir, filename)

    # Записываем построчно
    with open(filepath, 'w', encoding='utf-8') as f:
        for line in transformed_payloads:
            f.write(line + '\n')

    print(f"Готово! Результат сохранен в {filepath}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Использование: python script.py путь_к_json имя_преобразования")
        sys.exit(1)
    json_file = sys.argv[1]
    transform = sys.argv[2]
    main(json_file, transform)
```

## Кусок кода из прибавочного модуля:

```python
def noop(s: str) -> str:
    """Возвращает строку без изменений"""
    return s

def base64_std(s: str) -> str:
    """Стандартное Base64 кодирование"""
    return base64.b64encode(s.encode('utf-8')).decode('ascii')

def base64_urlsafe(s: str) -> str:
    """Base64 URL-safe (без '+' и '/')"""
    return base64.urlsafe_b64encode(s.encode('utf-8')).decode('ascii')

def base64_nopad(s: str) -> str:
    """Base64 без паддинга '='"""
    return base64.b64encode(s.encode('utf-8')).decode('ascii').rstrip('=')

def hex_lower(s: str) -> str:
    """Hex кодировка в нижнем регистре"""
    return binascii.hexlify(s.encode('utf-8')).decode('ascii')

def hex_upper(s: str) -> str:
    """Hex кодировка в верхнем регистре"""
    return binascii.hexlify(s.encode('utf-8')).decode('ascii').upper()
```

## Описание работы скрипта

1. **Чтение входного JSON-файла**
Скрипт ожидает JSON-файл с массивом объектов, где каждый объект имеет, как минимум, поле "payload". Например:

```json
[
    {"id": 1, "payload": "текст запроса 1"},
    {"id": 2, "payload": "текст запроса 2"}
]
```

2. **Преобразование payload**
Для каждого объекта из JSON применяется выбранное пользователем преобразование из модуля format.transforms.
Имя преобразования передается в качестве второго аргумента скрипта (например, base64, hex, url_pct_lower и др).

Если выбранное преобразование отсутствует, скрипт выдаст ошибку.
В случае ошибки при применении преобразования к конкретному payload, он остается без изменений

3. **Сохранение результата**
Все преобразованные payload записываются в текстовый файл, где каждая строка — это один преобразованный payload.
Имя файла формируется как json_<имя_преобразования>.txt.
Папка для сохранения — tests, которая создается на уровень выше каталога, где находится сам скрипт.

## Пример запуска

```bash
python changing_the_format.py ../json/sql.json base64
```

После выполнения появится файл

```bash
../tests/json_base64.txt
```

с преобразованными строками.