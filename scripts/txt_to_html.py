import os
import re
from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt
import argparse
import base64 as b64
from io import BytesIO
import textwrap


def load_test_values(folder_path):
    """
    Загружает все строки (контрольные пейлоады) из всех TXT-файлов 
    в указанной папке в одно множество для быстрого сравнения.
    """
    test_values = set()
    if not folder_path:
        return test_values
        
    if not os.path.isdir(folder_path):
        print(f"⚠️ Предупреждение: Папка для сравнения не найдена: '{folder_path}'. Будут обработаны все запросы без выделения контрольных.")
        return test_values
        
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path) and file_name.lower().endswith('.txt'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # Читаем все строки, удаляем пробелы и пустые строки, добавляем в множество
                    for line in f:
                        stripped_line = line.strip()
                        # Контрольный список имеет пейлоады без обфускации.
                        # Дополнительно очищаем, если они в стиле TXT-примера (%255Cx27...)
                        # Для чистоты сравнения здесь не декодируем, но оставляем 
                        # возможность, что пейлоад может быть сложным.
                        if stripped_line:
                            test_values.add(stripped_line)
            except Exception as e:
                print(f"Ошибка при чтении файла для сравнения {file_path}: {e}")

    print(f"Загружено {len(test_values)} уникальных значений для сравнения из '{folder_path}'.")
    return test_values


def parse_txt_to_data(file_path, test_values):
    """
    Читает и парсит один TXT-файл, извлекая все необходимые поля, 
    и определяет цвет статуса, учитывая контрольные значения.
    """
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        entries = re.split(r'-{70,}', content)
        
        index_counter = 1
        
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
                
            match_file = re.search(r'FILE: (.+)', entry)
            match_status = re.search(r'STATUS: (.+)', entry)
            match_technique = re.search(r'TECHNIQUE: (.+)', entry)
            match_original = re.search(r'ORIGINAL: (.+)', entry)
            match_payload = re.search(r'PAYLOAD: (.+)', entry)
            match_indicators = re.search(r'INDICATORS: (.+)', entry)
            
            if match_status and match_technique:
                status = match_status.group(1).strip()
                payload = match_payload.group(1).strip() if match_payload else "N/A"

                is_test_value = False
                status_color = "black"
                
                # 1. Проверяем, является ли это значением из контрольного списка
                if test_values and payload in test_values:
                    is_test_value = True
                    # 2. Определяем цвет для контрольных значений
                    if status == "200":
                        status_color = "green"  # УСПЕХ: Прошёл WAF!
                    elif status in ["403", "500"]:
                        status_color = "red"    # БЛОКИРОВКА/ОШИБКА: Заблокирован WAF
                    elif status.startswith("3"):
                        status_color = "darkorange" # Редирект
                    else:
                        status_color = "purple" # Неожиданный контрольный статус
                else:
                    # 3. Определяем цвет для обычных значений (фоновые)
                    if status == "200":
                        status_color = "darkgreen" 
                    elif status in ["403", "500"]:
                        status_color = "darkred"   
                    elif status.startswith("3"):
                        status_color = "orange"
                    else:
                        status_color = "black"
                # --------------------------------------------

                data.append({
                    "index": index_counter,
                    "file": match_file.group(1).strip() if match_file else "N/A",
                    "status": status,
                    "status_color": status_color, 
                    "technique": match_technique.group(1).strip(),
                    "original": match_original.group(1).strip() if match_original else "N/A",
                    "payload": payload,
                    "indicators": match_indicators.group(1).strip() if match_indicators else "N/A",
                    "response_length": 0,
                    "is_test_value": is_test_value # Флаг для потенциальной стилизации всей строки
                })
                index_counter += 1
                
        return data
    except Exception as e:
        print(f"Ошибка при парсинге файла {file_path}: {e}")
        return []


def generate_statistics(results):
    """Генерирует статистику по запросам."""
    total_requests = len(results)
    status_counts = Counter(item['status'] for item in results)
    technique_counts = Counter(item['technique'] for item in results)
    
    # Подсчет контрольных/неконтрольных значений
    test_passed_count = sum(1 for item in results if item['is_test_value'] and item['status'] == "200")
    test_blocked_count = sum(1 for item in results if item['is_test_value'] and item['status'] in ["403", "500"])
    
    stats = f"""
    <div class="statistics">
        <h2>Общая статистика</h2>
        <p><strong>Дата и время генерации:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}</p>
        <p><strong>Всего запросов:</strong> {total_requests}</p>
        
        <h3>Статистика контрольных пейлоадов:</h3>
        <ul>
            <li><span style="color: green; font-weight: bold;">УСПЕХ (200)</span>: {test_passed_count} (Пропущено WAF)</li>
            <li><span style="color: red; font-weight: bold;">БЛОКИРОВКА (403/500)</span>: {test_blocked_count} (Заблокировано WAF)</li>
        </ul>
        
        <h3>Распределение по статусам (Общее):</h3>
        <ul>
    """
    for status, count in sorted(status_counts.items(), key=lambda item: item[1], reverse=True):
        color = "green" if status == "200" else "red" if status in ["403", "500"] else "orange" if status.startswith("3") else "black"
        stats += f'<li><span style="color: {color}">HTTP {status}</span>: {count} ({(count/total_requests)*100:.1f}%)</li>'
    stats += """
        </ul>
        <h3>Распределение по техникам обфускации:</h3>
        <ul>
    """
    for technique, count in sorted(technique_counts.items(), key=lambda item: item[1], reverse=True):
        stats += f'<li>{technique}: {count} ({(count/total_requests)*100:.1f}%)</li>'
    stats += """
        </ul>
    </div>
    """
    return stats, technique_counts

def generate_chart(technique_counts):
    """Создаёт круговую диаграмму техник и возвращает ее как base64-строку."""
    if not technique_counts:
        return None
    
    labels = technique_counts.keys()
    sizes = technique_counts.values()
    
    plt.figure(figsize=(10, 8))
    
    def absolute_value(val):
        a = sum(sizes)
        return f'{(val/a)*100:.1f}%\n({int(round(val))})'
        
    plt.pie(sizes, labels=labels, autopct=absolute_value, startangle=140, 
                textprops={'fontsize': 10, 'color': 'black'}, wedgeprops={'edgecolor': 'white'})
    
    plt.title("Распределение использованных техник обфускации", pad=20)
    plt.axis('equal') 
    plt.tight_layout()
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    plt.close()
    buffer.seek(0)
    img_base64 = b64.b64encode(buffer.getvalue()).decode('utf-8')
    return img_base64

def generate_html(results, stats_html, chart_base64):
    """Генерирует финальную HTML-страницу."""
    
    MAX_PAYLOAD_LEN = 100
    
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Финальный Отчёт по Анализу Атак Burp Suite</title>
        <style>
            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                margin: 40px;
                background-color: #f5f6fa;
                color: #333;
                overflow-x: auto;
            }
            h1 { text-align: center; color: #2c3e50; font-size: 2.5em; margin-bottom: 20px; }
            h2 { color: #34495e; font-size: 1.8em; margin-top: 30px; }
            .statistics { background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); margin: 20px 0; }
            .statistics ul { list-style: none; padding: 0; }
            .statistics li { margin: 10px 0; font-size: 1.1em; }
            img { display: block; margin: 30px auto; max-width: 100%; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); }
            
            /* Стили для таблицы */
            .table-wrapper {
                width: 100%;
                overflow: auto; 
                max-height: 70vh; 
                margin-top: 20px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }

            table {
                width: 100%;
                min-width: 1600px; 
                border-collapse: collapse;
                background-color: #fff;
            }
            
            th, td {
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #e0e0e0;
                word-wrap: break-word;
                max-width: 150px; 
                white-space: nowrap; 
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            th {
                background-color: #3498db;
                color: white;
                font-weight: 600;
                position: sticky; 
                top: 0;
                z-index: 2;
            }
            tr:nth-child(even) { background-color: #f8f9fb; }
            tr:hover { background-color: #e8ecef; transition: background-color 0.2s; }
            
            /* Стиль для выделения контрольных строк */
            .test-row-pass { background-color: #e6ffe6; } /* Светло-зеленый */
            .test-row-block { background-color: #ffe6e6; } /* Светло-красный */
            .test-row-pass:hover { background-color: #ccffcc; }
            .test-row-block:hover { background-color: #ffcccc; }
            
            /* Стили для Tooltip */
            .tooltip {
                position: relative;
                display: block;
                cursor: help; 
                height: 100%;
            }
            .tooltip .tooltiptext {
                visibility: hidden;
                width: 600px; 
                background-color: #555;
                color: #fff;
                text-align: left;
                border-radius: 6px;
                padding: 10px;
                position: absolute;
                z-index: 10;
                top: 120%; 
                left: 0;
                opacity: 0;
                transition: opacity 0.3s;
                white-space: pre-wrap; 
                word-break: break-word;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            }
            .tooltip:hover .tooltiptext {
                visibility: visible;
                opacity: 1;
            }
        </style>
    </head>
    <body>
        <h1>Финальный Сводный Отчёт по Анализу Атак Burp Suite</h1>
        <p style="text-align: center; font-style: italic;">Данные агрегированы из всех предоставленных TXT-отчетов. <span style="font-weight: bold;">Строки с контрольными пейлоадами выделены цветом.</span></p>
    """
    
    html_content += stats_html
    
    if chart_base64:
        html_content += f"""
        <h2>Распределение Техник Обфускации (График)</h2>
        <div style="overflow-x: auto; margin-top: 20px; padding: 10px; background-color: #fff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); text-align: center;">
            <img src="data:image/png;base64,{chart_base64}" alt="Obfuscation Techniques Pie Chart" style="width: 100%; max-width: 800px; display: inline-block;">
        </div>
        """
        
    html_content += """
        <h2>Детализация Запросов (Сырые и Декодированные Пейлоады)</h2>
        <div class="table-wrapper">
        <table>
            <tr>
                <th>#</th>
                <th style="min-width: 150px;">File</th>
                <th>Status</th>
                <th style="min-width: 180px;">Technique</th>
                <th style="min-width: 400px;">Original (Сырой)</th>
                <th style="min-width: 400px;">Payload (Декодированный)</th>
                <th style="min-width: 300px;">Indicators</th>
            </tr>
    """
    for item in results:
        original_full = item['original']
        payload_full = item['payload']
        indicators_full = item['indicators']

        original_short = original_full[:MAX_PAYLOAD_LEN] + ('...' if len(original_full) > MAX_PAYLOAD_LEN else '')
        payload_short = payload_full[:MAX_PAYLOAD_LEN] + ('...' if len(payload_full) > MAX_PAYLOAD_LEN else '')
        
        indicators_short = textwrap.shorten(indicators_full, width=30, placeholder='...')
        
        # Определяем CSS класс для всей строки, если это контрольный пейлоад
        row_class = ""
        if item['is_test_value']:
            if item['status'] == "200":
                row_class = "test-row-pass"
            elif item['status'] in ["403", "500"]:
                row_class = "test-row-block"


        html_content += f"""
            <tr class="{row_class}">
                <td>{item['index']}</td>
                <td style="word-break: break-all;">{item['file']}</td>
                <td style="color: {item['status_color']}; font-weight: bold;">{item['status']}</td>
                <td>{item['technique']}</td>
                <td>
                    <div class="tooltip">{original_short}
                        <span class="tooltiptext">{original_full}</span>
                    </div>
                </td>
                <td>
                    <div class="tooltip">{payload_short}
                        <span class="tooltiptext">{payload_full}</span>
                    </div>
                </td>
                <td>
                    <div class="tooltip">{indicators_short}
                        <span class="tooltiptext">{indicators_full}</span>
                    </div>
                </td>
            </tr>
        """
    
    html_content += """
        </table>
        </div>
    """
    
    html_content += """
    </body>
    </html>
    """
    
    return html_content


def main():
    parser = argparse.ArgumentParser(description="Генерация HTML-отчета на основе TXT-выгрузок Burp Suite.")
    parser.add_argument("input_path", help="Путь к TXT-файлу или папке с TXT-файлами Burp Intruder.")

    parser.add_argument("-t", "--tests_dir", 
                        help="Путь к папке, содержащей TXT-файлы с 'контрольными' пейлоадами для сравнения (например, tests/sql).", 
                        required=False, 
                        default=None)
    
    args = parser.parse_args()
    
    input_path = args.input_path
    tests_dir = args.tests_dir 
    output_filename = "burp_final_report.html"
    
    # 1. Загрузка контрольных значений
    test_values = load_test_values(tests_dir)
    
    all_results = []

    # 2. Обработка входных файлов/папок
    if os.path.isfile(input_path) and input_path.lower().endswith('.txt'):
        all_results.extend(parse_txt_to_data(input_path, test_values))
    elif os.path.isdir(input_path):
        for file_name in os.listdir(input_path):
            file_path = os.path.join(input_path, file_name)
            if os.path.isfile(file_path) and file_name.lower().endswith('.txt'):
                all_results.extend(parse_txt_to_data(file_path, test_values))
    else:
        print(f"Ошибка: Путь '{input_path}' не является TXT-файлом или папкой с TXT-файлами.")
        return

    if not all_results:
        print("Не найдено данных для обработки.")
        return

    # 3. Генерация отчета
    stats_html, technique_counts = generate_statistics(all_results)
    chart_base64 = generate_chart(technique_counts)

    html_content = generate_html(all_results, stats_html, chart_base64)
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n✅ Обработка завершена. Финальный, красивый HTML-отчёт сохранён как: {output_filename}")

if __name__ == "__main__":
    main()