import tkinter as tk
from tkinter import filedialog
import random

def select_files():
    root = tk.Tk()
    root.withdraw()
    file_paths = filedialog.askopenfilenames(filetypes=[("Text files", "*.txt")])
    return list(file_paths)

def read_files(file_paths):
    all_lines = []
    for path in file_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                all_lines.extend(f.readlines())
        except Exception as e:
            print(f"Ошибка при чтении файла {path}: {e}")
    return all_lines

def write_output(lines, output_path='combined_shuffled.txt'):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"Готово! Итог сохранён в: {output_path}")

def main():
    files = select_files()
    if not files:
        print("Файлы не выбраны.")
        return

    all_lines = read_files(files)
    random.shuffle(all_lines)
    write_output(all_lines)

if __name__ == "__main__":
    main()
