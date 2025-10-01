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

# Инструкция по использованию скрипта run_all_transforms.py

## Описание

Этот скрипт автоматически запускает все доступные преобразования из модуля format.transforms над указанным JSON-файлом с данными и сохраняет результаты в папку tests (создаваемую на уровень выше директории основного скрипта преобразования). Для каждого преобразования вызывается внешний скрипт, который принимает путь к JSON и имя преобразования.

## Программный код: 

```python
import subprocess
from format.transforms import TRANSFORMS

def main(json_path, script_path):
    transform_names = sorted(TRANSFORMS.keys())
    for transform in transform_names:
        print(f"Запускаем преобразование: {transform}")
        # Формируем команду
        cmd = ['python', script_path, json_path, transform]
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"Ошибка при выполнении трансформации {transform}:")
            print(result.stderr)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Использование: python run_all_transforms.py путь_к_json путь_к_скрипту")
        sys.exit(1)
    json_file = sys.argv[1]
    script = sys.argv[2]
    main(json_file, script)
```

## Требования !!!

Наличие модуля format.transforms с словарём TRANSFORMS

Основной скрипт преобразования (например, changing_the_format.py), который принимает на вход JSON и имя преобразованияя.

## Использование

```bash
python run_all_transforms.py путь_к_json путь_к_скрипту_преобразования
```

путь_к_json — путь к JSON-файлу с данными (список словарей с ключами id и payload)

путь_к_скрипту_преобразования — путь к скрипту, который принимает два аргумента: JSON и имя преобразования

## Что происходит? (Это уже вопрос от меня)

Скрипт получает список всех доступных трансформаций из TRANSFORMS.

Поочерёдно вызывает внешний скрипт для каждой трансформации.

Выводит результат выполнения каждой трансформации в консоль.

Если происходит ошибка при выполнении какой-либо трансформации, выводит сообщение об ошибке.

## Пример запуска 

```bash
python run_all_transforms.py ../json/sql.json ../changing_the_format.py
```

# url_generato

Компактная документация и примеры использования для скрипта, который:

читает словарь (txt) — по одному слову/пейлоаду в строке;

подставляет {word} и {time} в URL‑шаблон;

сохраняет сгенерированные URL в файл;

опционально — выполняет GET‑запросы с управлением задержек/rate‑limit и параллелизмом;

логирует код возврата и размер ответа.

Важно (этика): включайте --send только на тестовых/собственных системах или при явном разрешении владельца ресурса. Не сканируйте чужие сервисы.

## Требования

Python 3.7+

Рекомендуется установить requests для отправки HTTP:

```bash
pip install requests
```

### Быстрый пример

Простой генератор URL (только запись в файл):

```bash
python url_generator.py -w words.txt -t "http://dvwa.local/vulnerabilities/sqli?id={word}&time={time}" -o out.txt
```


```bash
python url_generator.py -w words.txt -t "http://dvwa.local/vulnerabilities/sqli?id={word}&time={time}" --send --delay 2.0 --delay-mode 1 --workers 4
```

## Опции / Аргументы

```bash
-w, --wordlist       путь к txt (по одному слову в строке) (обязательно)
-t, --template       URL-шаблон с {word} и {time} (обязательно)
-T, --time           время: 'now' (по умолчанию), unix epoch или ISO (YYYY-MM-DDTHH:MM:SS) или literal
-f, --time-format    формат strftime для подстановки времени (по умолчанию "%Y-%m-%dT%H:%M:%S")
-o, --out            файл для записи сгенерированных URL (по умолчанию generated_urls.txt)
--send               если указан — выполнять GET запросы (по умолчанию OFF)
--delay              задержка в секундах (по умолчанию 1.0) — смысл зависит от --delay-mode
--delay-mode         режим задержки: 0=no delay, 1=per-thread pre-request sleep, 2=global strict rate limit (по умолчанию 2)
--workers            число параллельных потоков (по умолчанию 4)
--max-urls           максимум URL для генерации/отправки (0 = все)
```

## О задержках / rate limiting

--delay-mode 0: нет дополнительных пауз — запросы выполняются без искусственных задержек.

--delay-mode 1: каждый поток делает time.sleep(delay) перед своим GET. При --workers>1 одновременно может выполняться несколько запросов (каждый с собственной паузой).

--delay-mode 2 (рекомендуется при строгих лимитах): глобальный лимит — между любыми двумя фактическими GET будет минимум delay секунд. Работает корректно при многопоточности.

## Как обрабатываются слова (payloads)

Слова читаются построчно и очищаются (strip()).

Перед подстановкой в URL каждое слово проходит URL‑кодирование (urllib.parse.quote_plus) — спецсимволы преобразуются в %XX, чтобы параметры были корректными.

{time} подставляется согласно --time и --time-format.

Пример:
```arduino
word:  QlDa8P`)(;ajAK6W>0_/0I2CG%G]8Bl@l@/H
quote_plus(word) -> QlDa8P%60%29%28%3BajAK6W%3E0_%2F0I2CG%25G%5D8Bl%40l%40%2FH
```

## Вывод / логирование

При --send скрипт печатает строки вида:

```php-template
<URL> <status_code> <size_or_error>
```
Примеры:

```arduino
http://... 200 1582
http://... 500 821
http://... ERR HTTPConnectionPool(...)
```

Если нужно логировать в файл, можно добавить простой append в код:

```puthon
log_line = f"{url} | status: {status} | info: {info}"
with open("url_log.txt", "a", encoding="utf-8") as logf:
    logf.write(log_line + "\n")
```

(Для продвинутого логирования — используйте модуль logging.)

## Частые улучшения (опции для добавления)

Retry с экспоненциальным backoff для ошибок сети.

Фильтрация результатов (только 2xx или только ошибки).

Поддержка POST, кастомных заголовков и авторизации.

Асинхронная версия с asyncio + aiohttp для высокой производительности.

GUI (tkinter) или Web UI для визуального контроля.


### Пример вордлиста

Формат — один payload на строку. Пример строк с любыми спецсимволами (скрипт корректно обработает и URL‑кодирует их):

```diff
-Ql2_+>H#6/M-
-Ql2_+=3DAlk4XVr
-QlDa8P`)(;ajAK6W>0_/0I2CG%G]8Bl@l@/H
...
```

## Лицензия

MIT (используй и модифицируй, соблюдая этические ограничения).