# Работа и реализация скрипта burp_payload_analyzer.py

## Описание 

Этот скрипт используется для анализа данных, экспортированных из Burp Suite Intruder в формате XML. Скрипт извлекает информацию о пейлоадах, определяет технику их обфускации (например, URL-кодирование, Base64, HEX) и анализирует ответы серверов на наличие индикаторов таких атак, как SQL-инъекции или блокировки WAF. Результаты анализа сохраняются в текстовом файле, который включает статус, технику обфускации, пейлоады и индикаторы.

## Основные фуункции: 

1. **Декодирование Base64**: Декодирует строки, закодированные в Base64, чтобы облегчить анализ содержимого.

2. **Извлечение пейлоада**: Извлекает сырое значение из URL-параметра, если оно присутствует, и очищает его от лишних частей.

3. **Определение техники обфускации**: На основе исходного и декодированного пейлоада скрипт классифицирует технику обфускации, используя различные алгоритмы (URL-кодирование, Base64, HEX).

4. **Анализ ответа**: Скрипт анализирует ответ сервера на наличие индикаторов, таких как ошибки SQL-инъекций или блокировки WAF.

5. **Запись результатов в файл**: Итоговые данные о пейлоадах, технике обфускации и индикаторах записываются в текстовый отчет.

## Программный код:

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

    if '%' in raw_payload:
        if raw_payload != decoded_payload:
            temp_hex = decoded_payload.replace(' ', '').replace(':', '').upper()
            if all(c in '0123456789ABCDEF' for c in temp_hex) and len(temp_hex) % 2 == 0 and len(temp_hex) > 1:
                return "URL + HEX Encoding"
            if len(decoded_payload) % 4 == 0 or (len(decoded_payload) > 10 and '=' in decoded_payload):
                try:
                    b64.b64decode(decoded_payload.replace(' ', ''), validate=True)
                    return "URL + Base64 Encoding"
                except:
                    pass
            return "URL Encoding"

    if len(raw_payload) % 4 == 0 or '=' in raw_payload:
        try:
            b64.b64decode(raw_payload.replace(' ', ''), validate=True)
            return "Base64 Encoding"
        except:
            pass

    temp_hex = raw_payload.replace(' ', '').replace(':', '').upper()
    if all(c in '0123456789ABCDEF' for c in temp_hex) and len(temp_hex) % 2 == 0 and len(temp_hex) > 1:
        return "HEX Encoding"
        
    return "No Obfuscation (Plain Text)"

def analyze_response(response_base64):
    """Анализирует ответ для индикаторов."""
    decoded_response = decode_base64(response_base64)
    indicators = []
    
    if decoded_response:
        if "You have an error in your SQL syntax" in decoded_response or "mysql_fetch_array" in decoded_response or "Error converting data type" in decoded_response:
            indicators.append("SQL Error (Injection Detected)")
        if "403 Forbidden" in decoded_response or "WAF" in decoded_response or "Blocked" in decoded_response:
            indicators.append("WAF/403 Block")
        if "Welcome" in decoded_response or "Logged in" in decoded_response or "admin" in decoded_response:
            indicators.append("Success/Auth Heuristic")
    
    return " / ".join(indicators) if indicators else "No obvious indicators."

def process_burp_file(file_path, output_file):
    """Обрабатывает XML-файл и записывает результаты в текстовый файл."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        with open(output_file, 'a', encoding='utf-8') as f:
            for item in root.findall('item'):
                path_content = item.find('path').text.strip() if item.find('path') else None
                status = item.find('status').text if item.find('status') else "N/A"
                response_base64 = item.find('response').text if item.find('response') else None
                
                raw_payload = extract_payload_from_path(path_content)
                decoded_payload = urllib.parse.unquote(raw_payload) if raw_payload else "N/A"
                
                original_display = "EMPTY STRING" if raw_payload == "" else raw_payload
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

## Пояснение работы скрипта:

1. **decode_base64** — Эта функция принимает строку в формате Base64, очищает её от пробелов и символов новой строки, а затем декодирует. Если декодирование невозможно, функция возвращает None.

2. **extract_payload_from_path** — Функция извлекает значение параметра id из URL, присутствующего в теге <path>. Это значение используется как пейлоад для дальнейшего анализа.

3. **determine_technique** — Функция анализирует пейлоад и определяет, какая техника обфускации использована: URL-кодирование, Base64, HEX или же это обычный текст.

4. **analyze_response** — Функция принимает строку в формате Base64 (ответ от сервера), декодирует её и проверяет наличие индикаторов SQL-инъекций, блокировок WAF или успешных аутентификаций.

5. **process_burp_file** — Эта функция обрабатывает один XML-файл, извлекает данные, выполняет анализ и записывает результаты в отчет. Если файл не удается обработать, выводится ошибка.

6. **main** — Основная функция скрипта. Она запускает процесс обработки файла или папки с XML-файлами и записывает результаты в текстовый файл.

## Примечание 

**Обработка ошибок**: Скрипт включает обработку ошибок при парсинге XML и декодировании данных. Ошибки записываются в консоль, чтобы помочь диагностировать проблему.

**Запись отчета**: Скрипт генерирует отчет в формате текстового файла, в котором представлены результаты анализа каждого пейлоада, включая его технику обфускации и индикаторы.

## Пример использования:

1. Запустите скрипт, передав путь к XML-файлу или папке, содержащей XML-файлы:

```bash
python burp_payload_analyzer.py /path/to/burp/files
```
2. Результаты обработки будут записаны в файл burp_payload_analysis_report.txt в той же директории, откуда был запущен скрипт.