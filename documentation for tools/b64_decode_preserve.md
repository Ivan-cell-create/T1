# Работа и реализация скрипта b64_decode_preserve.py

## Описание

Утилита b64_decode_preserve.py предназначена для декодирования строк в формате Base64 из входного файла в байты, с сохранением их точной структуры (без изменений в данных). Результат можно записать в один агрегатный файл или сохранить каждый payload в отдельный файл.

## Опции:

-i / --input: Путь к входному файлу, который содержит строки в формате base64. Каждая строка должна быть закодирована в base64.

-o / --output: Путь к выходному файлу или директории. Если указан флаг --one-file-per-payload, то каждая строка будет записана в отдельный файл.

--one-file-per-payload: Если этот флаг установлен, каждый декодированный payload будет сохранён в отдельный файл внутри выходной директории.

--ext: Указывает расширение для файлов, если используется --one-file-per-payload (по умолчанию .bin).

--no-strip: Если установлен, строки base64 не будут очищаться от пробелов и символов новой строки перед декодированием.

--sep: Разделитель, добавляемый между декодированными payload-ами в агрегатный файл (по умолчанию это \\n).

--no-sep: Отключает добавление разделителя между payload-ами (эквивалентно --sep "").

--quiet: Отключает вывод прогресса в процессе выполнения.

###  Примеры: 

1. Декодирование в один агрегатный файл:

```bash
python3 b64_decode_preserve.py -i encoded.txt -o decoded_all.bin
```

2. Декодирование с сохранением каждого payload в отдельный файл:

```bash
python3 b64_decode_preserve.py -i encoded.txt -o decoded_dir/ --one-file-per-payload --ext .txt
```

3. Декодирование с добавлением конкретного разделителя:

```bash
python3 b64_decode_preserve.py -i encoded.txt -o decoded_all.txt --sep "\\n"
```

4. Декодирование без разделителя между payload-ами:

```bash
python3 b64_decode_preserve.py -i encoded.txt -o decoded_all.bin --no-sep
```

## Программный код с документацией

```python
#!/usr/bin/env python3
# coding: utf-8
"""
b64_decode_preserve.py

Читает входной файл со строками base64 и декодирует каждую строку в точные байты.
Опции:
  -i / --input                 input file (base64 lines)
  -o / --output                output file path OR output directory (if --one-file-per-payload)
  --one-file-per-payload       сохранять каждый декодированный payload в отдельный файл
  --ext                       расширение для отдельных файлов (по умолчанию .bin)
  --no-strip                  НЕ обрезать ведущие/хвостовые пробелы в строках base64 (по умолчанию обрезаем)
  --sep                       разделитель, добавляемый между payload'ами в агрегатном файле.
                              Поддерживает escape-последовательности: "\\n", "\\r\\n", "\\t" и т.д.
                              Также допускается hex: "0x0A" или "0x0D0A" (без пробелов).
                              По умолчанию: "\\n".
  --no-sep                    не добавлять никакого разделителя между payload'ами (эквивалент --sep '')
  --quiet                     не печатать прогресс
Примеры:
  python3 b64_decode_preserve.py -i encoded.txt -o decoded_all.bin
  python3 b64_decode_preserve.py -i encoded.txt -o decoded_dir/ --one-file-per-payload --ext .txt
  python3 b64_decode_preserve.py -i encoded.txt -o decoded_all.txt --sep "\\n"
  python3 b64_decode_preserve.py -i encoded.txt -o decoded_all.bin --no-sep
"""

import argparse
import base64
import binascii
import codecs
from pathlib import Path
import sys

def decode_line(b64_line: str, strip: bool = True):
    """
    Декодирует одну строку base64 в байты.
    Если strip=True, предварительно обрезаем пробелы и перевод строки.
    Возвращает байты или возбуждает ValueError при ошибке декодирования.
    
    :param b64_line: Строка, закодированная в base64.
    :param strip: Обрезать ли пробелы и символы новой строки.
    :return: Декодированные байты.
    """
    s = b64_line if not strip else b64_line.strip()
    # Пропускаем пустые строки
    if s == "":
        return None
    try:
        # Стандартное декодирование base64
        data = base64.b64decode(s, validate=True)
        return data
    except binascii.Error as e:
        # Если ошибка (например, отсутствие паддинга), пробуем добавить паддинг '=' и снова декодировать
        try:
            padded = s + ("=" * ((4 - len(s) % 4) % 4))
            data = base64.b64decode(padded, validate=False)
            return data
        except Exception:
            raise ValueError(f"Invalid base64 data: {e!s}")

def parse_sep(sep_str: str) -> bytes:
    """
    Преобразует строковое представление разделителя в байты.
    Поддерживает:
      - escape-последовательности (например "\\n", "\\r\\n", "\\t") через unicode_escape
      - hex-представление: "0x0A" или "0x0D0A"
      - пустая строка -> b''
    
    :param sep_str: Строка, представляющая разделитель.
    :return: Декодированный байтовый разделитель.
    """
    if sep_str is None:
        return b''
    s = sep_str.strip()
    if s == '':
        return b''
    # Если разделитель в hex-формате (например, "0x0A")
    if s.lower().startswith('0x'):
        hexpart = s[2:]
        # Дополняем ведущим нулём, если количество символов нечётное
        if len(hexpart) % 2 == 1:
            hexpart = '0' + hexpart
        try:
            return bytes.fromhex(hexpart)
        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid hex separator: {sep_str}")
    # Если это escape-последовательности типа '\n', '\r\n', '\t'
    try:
        decoded = codecs.decode(s, 'unicode_escape')
        return decoded.encode('utf-8')
    except Exception:
        # В случае ошибки — возвращаем сырые байты строки
        return s.encode('utf-8')

def main():
    """
    Основная функция утилиты. Обрабатывает аргументы командной строки, открывает входной файл,
    декодирует строки и сохраняет результат в указанный выходной файл или директорию.
    """
    p = argparse.ArgumentParser(description="Decode file of base64 lines and preserve exact decoded bytes.")
    p.add_argument('-i', '--input', required=True, help='Input file path (one base64 entry per line)')
    p.add_argument('-o', '--output', required=True,
                   help='Output file path (aggregate) OR output directory (when --one-file-per-payload)')
    p.add_argument('--one-file-per-payload', action='store_true',
                   help='Save each decoded payload into a separate file inside output directory')
    p.add_argument('--ext', default='.bin', help='File extension for per-payload files (default: .bin)')
    p.add_argument('--no-strip', dest='strip', action='store_false',
                   help='Do NOT strip whitespace/newline from each base64 input line before decoding')
    p.add_argument('--sep', default='\\n',
                   help='Separator to insert between payloads in aggregate file. Default "\\n". Use --no-sep to disable.')
    p.add_argument('--no-sep', dest='sep', action='store_const', const='', 
                   help='Do NOT add any separator between payloads (equivalent to --sep "").')
    p.add_argument('--quiet', action='store_true', help='Suppress progress prints')
    args = p.parse_args()

    inp = Path(args.input)
    if not inp.exists():
        print(f"Input file not found: {inp}", file=sys.stderr)
        sys.exit(2)

    # parse separator into bytes
    try:
        sep_bytes = parse_sep(args.sep)
    except argparse.ArgumentTypeError as e:
        print(f"Separator parse error: {e}", file=sys.stderr)
        sys.exit(2)

    out = Path(args.output)
    if args.one_file_per_payload:
        out.mkdir(parents=True, exist_ok=True)
    else:
        # Ensure parent dir exists for single output file
        if out
```

## Уточнения

Аргументы командной строки:

-i/--input: Путь к файлу, содержащему строки base64.

-o/--output: Путь к выходному файлу или директории.

--one-file-per-payload: Если активирован, каждый payload будет сохранён в отдельный файл.

--ext: Указывает расширение для отдельных файлов.

--sep: Разделитель для добавления между декодированными данными.

--no-sep: Отключает добавление разделителя.

--quiet: Убирает вывод прогресса.