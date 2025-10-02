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
    """
    Извлекает сырое значение, находящееся после '?id=' из содержимого тега <path>.
    """
    # Ищет '?id=' и захватывает все символы до конца строки (или до другого параметра)
    match = re.search(r'\?id=(.*)', path_content)
    
    if match:
        raw_payload = match.group(1)
        # Очистка от потенциальных якорей (#) или следующих параметров (&)
        raw_payload = raw_payload.split('&')[0].split('#')[0]
        
        return raw_payload
    else:
        return None

def determine_technique(raw_payload, decoded_payload):
    """Определяет технику обфускации на основе сырого пейлоада."""
    
    if raw_payload is None:
        return "N/A (No ID parameter)"
    
    if raw_payload == "":
        return "Empty Payload"

    # 1. Проверка на URL-кодирование
    if '%' in raw_payload:
        if raw_payload != decoded_payload:
            
            # Проверка на вложенный HEX
            temp_hex = decoded_payload.replace(' ', '').replace(':', '').upper()
            if all(c in '0123456789ABCDEF' for c in temp_hex) and len(temp_hex) % 2 == 0 and len(temp_hex) > 1:
                return "URL + HEX Encoding"
            
            # Проверка на вложенный Base64
            if len(decoded_payload) % 4 == 0 or (len(decoded_payload) > 10 and '=' in decoded_payload):
                try:
                    b64.b64decode(decoded_payload.replace(' ', ''), validate=True)
                    return "URL + Base64 Encoding"
                except:
                    pass
            
            return "URL Encoding"

    # 2. Проверка на чистое Base64 (без URL-кодирования)
    if len(raw_payload) % 4 == 0 or '=' in raw_payload:
        try:
            b64.b64decode(raw_payload.replace(' ', ''), validate=True)
            return "Base64 Encoding"
        except:
            pass

    # 3. Проверка на чистый HEX
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
    """Парсит один XML-файл и записывает результаты в TXT-файл."""
    print(f"Обработка файла: {os.path.basename(file_path)}...")
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        results_count = 0
        
        with open(output_file, 'a', encoding='utf-8') as f:
            for item in root.findall('item'):
                # Извлечение данных
                path_content = item.find('path').text.strip() if item.find('path') is not None and item.find('path').text else None
                status = item.find('status').text if item.find('status') is not None else "N/A"
                response_base64 = item.find('response').text if item.find('response') is not None else None
                
                # 1. Извлечение RAW_PAYLOAD (Original)
                raw_payload = extract_payload_from_path(path_content)
                
                # 2. Минимальное декодирование (URL-декодирование) для PAYLOAD
                if raw_payload is not None:
                    decoded_payload = urllib.parse.unquote(raw_payload)
                else:
                    decoded_payload = "N/A"
                    raw_payload = "N/A"
                
                # Заменяем пустые строки на явное обозначение
                original_display = "EMPTY STRING" if raw_payload == "" else raw_payload
                payload_display = "EMPTY STRING" if decoded_payload == "" else decoded_payload
                
                # 3. Классификация и анализ
                technique = determine_technique(raw_payload, decoded_payload)
                indicators = analyze_response(response_base64)
                
                # 4. Запись в файл
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
    parser = argparse.ArgumentParser(description="Извлечение данных из Burp Suite XML-файлов и генерация сводного отчета.")
    parser.add_argument("input_path", help="Путь к XML-файлу или папке с XML-файлами")
    args = parser.parse_args()
    
    input_path = args.input_path
    output_filename = "burp_payload_analysis_report.txt"
    
    # Создание/перезапись заголовочного файла
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(f"--- Сводный отчет по анализу Burp Suite Intruder ---\n")
        f.write(f"Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Критические поля: TECHNIQUE, ORIGINAL (сырой), PAYLOAD (URL-декодированный), STATUS, INDICATORS\n")
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