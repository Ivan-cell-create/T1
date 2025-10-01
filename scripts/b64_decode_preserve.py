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
    """
    s = b64_line if not strip else b64_line.strip()
    # Пропускаем пустые строки (возвращаем None)
    if s == "":
        return None
    try:
        data = base64.b64decode(s, validate=True)
        return data
    except binascii.Error as e:
        # пробуем более толерантно (в случае, если нет паддинга '=' и т.д.)
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
    """
    if sep_str is None:
        return b''
    s = sep_str.strip()
    if s == '':
        return b''
    # hex form
    if s.lower().startswith('0x'):
        hexpart = s[2:]
        # допустим нечётное количество символов — дополняем ведущим нулём
        if len(hexpart) % 2 == 1:
            hexpart = '0' + hexpart
        try:
            return bytes.fromhex(hexpart)
        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid hex separator: {sep_str}")
    # interpret escape sequences like '\n', '\r\n', '\t' using unicode_escape
    try:
        decoded = codecs.decode(s, 'unicode_escape')
        return decoded.encode('utf-8')
    except Exception:
        # fallback: raw bytes of the string
        return s.encode('utf-8')

def main():
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
        if out.parent != Path(''):
            out.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    errors = 0

    with inp.open('r', encoding='utf-8', errors='replace') as fh:
        for idx, raw_line in enumerate(fh, start=1):
            try:
                decoded = decode_line(raw_line, strip=args.strip)
            except ValueError as e:
                print(f"[{idx}] decode error: {e}", file=sys.stderr)
                errors += 1
                continue

            if decoded is None:
                # пустая строка — пропускаем (не создаём файл)
                if not args.quiet:
                    print(f"[{idx}] empty line -> skipped")
                continue

            if args.one_file_per_payload:
                fname = out / f"payload_{idx:05d}{args.ext}"
                # Записываем точные байты
                fname.write_bytes(decoded)
                if not args.quiet:
                    print(f"[{idx}] written {len(decoded)} bytes -> {fname}")
            else:
                # В агрегатный файл — дозаписываем байты и затем сепаратор (если он задан)
                with out.open('ab') as ofh:
                    ofh.write(decoded)
                    if sep_bytes:
                        ofh.write(sep_bytes)
                if not args.quiet:
                    sdisplay = sep_bytes.decode('utf-8', errors='replace') if sep_bytes else '<none>'
                    print(f"[{idx}] appended {len(decoded)} bytes + sep({sdisplay}) to {out}")
            written += 1

    print(f"Done. Decoded: {written}, Errors: {errors}. Output: {out}")

if __name__ == '__main__':
    main()
