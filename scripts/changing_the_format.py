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
    with open(json_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

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
