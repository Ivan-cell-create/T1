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