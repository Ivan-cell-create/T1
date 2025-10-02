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
