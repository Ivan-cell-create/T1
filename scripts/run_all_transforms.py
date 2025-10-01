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
