# Работа и реализация скрипта txt_to_html.py

## Описание

Этот скрипт предназначен для анализа XML‑экспорта из Burp Suite (например, результатов Intruder/Proxy), извлечения пейлоадов из параметра id в теге <path>, классификации техник обфускации (URL‑кодирование, Base64, HEX и их комбинации) и поиска индикаторов в ответах сервера (ошибки SQL, блокировки WAF, признаки успешной аутентификации и т.п.). Результаты агрегируются в текстовый отчет burp_payload_analysis_report.txt.

## Основные функции

1. Декодирование Base64 — очищает и декодирует строки Base64, возвращает текст для анализа.

2. Извлечение пейлоада — находит значение параметра id в поле <path> и очищает его от дополнительных параметров и якорей.

3. Определение техники обфускации — классифицирует пейлоад как URL, Base64, HEX, их комбинации или plain text.

4. Анализ ответа — декодирует содержимое ответа (если оно в base64) и ищет ключевые индикаторы (SQL‑ошибки, WAF, успех).

5. Обработка XML‑файлов — парсит каждый <item>, извлекает данные и записывает человекочитаемый отчет.

6. Пакетная обработка — поддерживает прием одного XML‑файла или папки с несколькими XML.

## Программный код

```python
import xml.etree.ElementTree as ET
import urllib.parse
import os
import re
import base64 as b64
from datetime import datetime
import argparse

def decode_base64(data):
    """Декодирует base64-строку для обработки Response."""
    try:
        data = data.replace(' ', '').replace('\n', '').replace('\r', '') 
        missing_padding = len(data) % 4
        if missing_padding != 0:
            data += '=' * (4 - missing_padding)
        return b64.b64decode(data).decode('utf-8', errors='ignore')
    except Exception:
        return None 

def extract_payload_from_path(path_content):
    """Извлекает сырое значение после '?id=' из содержимого тега <path>."""
    if not path_content:
        return None
    match = re.search(r'\?id=(.*)', path_content)
    if match:
        raw_payload = match.group(1)
        raw_payload = raw_payload.split('&')[0].split('#')[0]
        return raw_payload
    return None

def determine_technique(raw_payload, decoded_payload):
    """Определяет технику обфускации на основе сырого пейлоада."""
    if raw_payload is None:
        return "N/A (No ID parameter)"
    if raw_payload == "":
        return "Empty Payload"

    # URL-encoded
    if '%' in raw_payload:
        if raw_payload != decoded_payload:
            temp_hex = (decoded_payload or '').replace(' ', '').replace(':', '').upper()
            if temp_hex and all(c in '0123456789ABCDEF' for c in temp_hex) and len(temp_hex) % 2 == 0:
                return "URL + HEX Encoding"
            if decoded_payload and (len(decoded_payload) % 4 == 0 or ('=' in decoded_payload and len(decoded_payload) > 10)):
                try:
                    b64.b64decode(decoded_payload.replace(' ', ''), validate=True)
                    return "URL + Base64 Encoding"
                except:
                    pass
            return "URL Encoding"

    # Base64 plain
    if (len(raw_payload) % 4 == 0) or ('=' in raw_payload):
        try:
            b64.b64decode(raw_payload.replace(' ', ''), validate=True)
            return "Base64 Encoding"
        except:
            pass

    # HEX plain
    temp_hex = raw_payload.replace(' ', '').replace(':', '').upper()
    if temp_hex and all(c in '0123456789ABCDEF' for c in temp_hex) and len(temp_hex) % 2 == 0 and len(temp_hex) > 1:
        return "HEX Encoding"
        
    return "No Obfuscation (Plain Text)"

def analyze_response(response_base64):
    """Анализирует ответ для индикаторов."""
    decoded_response = decode_base64(response_base64) if response_base64 else None
    indicators = []
    if decoded_response:
        if ("You have an error in your SQL syntax" in decoded_response
            or "mysql_fetch_array" in decoded_response
            or "Error converting data type" in decoded_response):
            indicators.append("SQL Error (Injection Detected)")
        if "403 Forbidden" in decoded_response or "WAF" in decoded_response or "Blocked" in decoded_response:
            indicators.append("WAF/403 Block")
        if "Welcome" in decoded_response or "Logged in" in decoded_response or "admin" in decoded_response:
            indicators.append("Success/Auth Heuristic")
    return " / ".join(indicators) if indicators else "No obvious indicators."

def process_burp_file(file_path, output_file):
    """Обрабатывает XML-файл и записывает результаты в текстовый файл."""
    print(f"Обработка файла: {os.path.basename(file_path)}...")
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        results_count = 0
        with open(output_file, 'a', encoding='utf-8') as f:
            for item in root.findall('item'):
                path_content = item.find('path').text.strip() if item.find('path') is not None and item.find('path').text else None
                status = item.find('status').text if item.find('status') is not None else "N/A"
                response_base64 = item.find('response').text if item.find('response') is not None else None

                raw_payload = extract_payload_from_path(path_content)
                decoded_payload = urllib.parse.unquote(raw_payload) if raw_payload else "N/A"

                original_display = "EMPTY STRING" if raw_payload == "" else (raw_payload if raw_payload is not None else "N/A")
                payload_display = "EMPTY STRING" if decoded_payload == "" else decoded_payload

                technique = determine_technique(raw_payload, decoded_payload)
                indicators = analyze_response(response_base64)

                output_line = (
                    f"FILE: {os.path.basename(file_path)}\n"
                    f"  STATUS: {status}\n"
                    f"  TECHNIQUE: {technique}\n"
                    f"  ORIGINAL: {original_display}\n"
                    f"  PAYLOAD: {payload_display}\n"
                    f"  INDICATORS: {indicators}\n"
                    f"{'-'*70}\n"
                )
                f.write(output_line)
                results_count += 1
        print(f"  -> Извлечено {results_count} записей.")
    except ET.ParseError as e:
        print(f"Ошибка парсинга XML в файле {file_path}: {e}")
    except Exception as e:
        print(f"Непредвиденная ошибка при обработке {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Извлечение данных из Burp Suite XML-файлов и генерация отчета.")
    parser.add_argument("input_path", help="Путь к XML-файлу или папке с XML-файлами")
    args = parser.parse_args()
    
    input_path = args.input_path
    output_filename = "burp_payload_analysis_report.txt"
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(f"--- Сводный отчет по анализу Burp Suite Intruder ---\n")
        f.write(f"Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Критические поля: TECHNIQUE, ORIGINAL, PAYLOAD, STATUS, INDICATORS\n")
        f.write(f"{'='*70}\n")
    
    if os.path.isfile(input_path) and input_path.lower().endswith('.xml'):
        process_burp_file(input_path, output_filename)
    elif os.path.isdir(input_path):
        for file_name in os.listdir(input_path):
            file_path = os.path.join(input_path, file_name)
            if os.path.isfile(file_path) and file_name.lower().endswith('.xml'):
                process_burp_file(file_path, output_filename)
    else:
        print(f"Ошибка: Путь '{input_path}' не является XML-файлом или папкой с XML-файлами.")
        return

    print(f"\n✅ Обработка завершена. Результаты сохранены в файл: {output_filename}")

if __name__ == "__main__":
    main()
```

## Пояснение работы скрипта

1. **decode_base64** — очищает входную строку (удаляет пробелы и переводы), добавляет недостающие символы выравнивания (=) при необходимости и пытается декодировать в UTF‑8. При ошибке возвращает None.

2. **extract_payload_from_path** — ищет в строке path_content шаблон ?id= и возвращает всё, что идёт после него до следующего & или #. Если path отсутствует или параметр id не найден — возвращает None.

3. **determine_technique** — принимает исходный (raw_payload) и URL‑декодированный (decoded_payload) пейлоады и:

определяет URL‑кодирование (включая случаи, когда после декодирования получился HEX или Base64);

распознаёт чистый Base64 и чистый HEX;

иначе помечает как plain text или Empty Payload/N/A.

4. **analyze_response** — декодирует response (если присутствует) и ищет явные маркеры:

SQL‑ошибки (You have an error in your SQL syntax, mysql_fetch_array, Error converting data type);

блокировки/WAF (403 Forbidden, WAF, Blocked);

возможный успех/авторизация (Welcome, Logged in, admin).
Возвращает строку с перечислением индикаторов или No obvious indicators.

5. **process_burp_file** — парсит XML, проходит по каждому <item>, извлекает path, status, response, выполняет извлечение/декодирование/классификацию и записывает форматированный блок в выходной файл. Логирует количество обработанных записей и ошибки парсинга.

6. **main** — CLI‑обёртка: принимает путь к файлу или папке, инициализирует отчет (перезаписывая старый), затем обрабатывает указанный файл или все .xml в папке.

## Примечание

**Обработка ошибок**: скрипт логирует ошибки парсинга XML и общие исключения в консоль. При некорректных или отсутствующих полях (path, response) соответствующие значения помечаются как N/A.

**Кодировка**: при декодировании Base64 используется utf-8 с игнорированием ошибок; если в ответе есть бинарные данные, они будут отброшены/игнорированы.

**Формат входа**: ожидается стандартный Burp‑подобный XML с элементами <item> и вложенными тегами path, response, status и т.п.

**Выход**: burp_payload_analysis_report.txt — человекочитаемый агрегированный отчет.

## Пример использования

Запуск для одного файла:

```bash
python burp_payload_analyzer.py /path/to/file.xml
```

Запуск для папки:

```bash
python burp_payload_analyzer.py /path/to/folder_with_xmls
```

После выполнения в текущей директории появится burp_payload_analysis_report.txt с результатами анализа.