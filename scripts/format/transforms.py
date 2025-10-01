from typing import Callable, Dict
import base64
import binascii
import urllib.parse
import html
import codecs
import gzip
import zlib
import bz2
import lzma
import quopri

# --- Базовые преобразования ---

def noop(s: str) -> str:
    """Возвращает строку без изменений"""
    return s

def base64_std(s: str) -> str:
    """Стандартное Base64 кодирование"""
    return base64.b64encode(s.encode('utf-8')).decode('ascii')

def base64_urlsafe(s: str) -> str:
    """Base64 URL-safe (без '+' и '/')"""
    return base64.urlsafe_b64encode(s.encode('utf-8')).decode('ascii')

def base64_nopad(s: str) -> str:
    """Base64 без паддинга '='"""
    return base64.b64encode(s.encode('utf-8')).decode('ascii').rstrip('=')

def hex_lower(s: str) -> str:
    """Hex кодировка в нижнем регистре"""
    return binascii.hexlify(s.encode('utf-8')).decode('ascii')

def hex_upper(s: str) -> str:
    """Hex кодировка в верхнем регистре"""
    return binascii.hexlify(s.encode('utf-8')).decode('ascii').upper()

def backslash_x(s: str) -> str:
    """Побайтовое представление с экранированием '\\x'"""
    return ''.join('\\x{:02x}'.format(b) for b in s.encode('utf-8'))

def url_encode_all(s: str) -> str:
    """URL encode всех символов (safe='')"""
    return urllib.parse.quote(s, safe='')

def url_encode_safe_slash(s: str) -> str:
    """URL encode с сохранением слешей '/'"""
    return urllib.parse.quote(s, safe='/')

def double_url(s: str) -> str:
    """Двойное URL кодирование"""
    return urllib.parse.quote(urllib.parse.quote(s, safe=''), safe='')

def html_escape_named(s: str) -> str:
    """HTML escape с использованием именованных сущностей"""
    return html.escape(s, quote=True)

def html_numeric_dec(s: str) -> str:
    """HTML escape с десятичными числовыми сущностями"""
    out = ''.join(f'&#{ord(ch)};' if ord(ch) > 127 or ch in "<>&\"'" else ch for ch in s)
    return out

def html_numeric_hex(s: str) -> str:
    """HTML escape с шестнадцатеричными числовыми сущностями"""
    out = ''.join(f'&#x{ord(ch):x};' if ord(ch) > 127 or ch in "<>&\"'" else ch for ch in s)
    return out

def unicode_escape_python(s: str) -> str:
    """Unicode escape, как в Python"""
    return s.encode('unicode_escape').decode('ascii')

def js_escape(s: str) -> str:
    """JS-экранирование спецсимволов и юникода"""
    out = []
    for ch in s:
        code = ord(ch)
        if ch == '\n':
            out.append('\\n')
        elif ch == '\r':
            out.append('\\r')
        elif ch == '\t':
            out.append('\\t')
        elif ch in ("'", '"', '\\'):
            out.append('\\' + ch)
        elif 32 <= code < 127:
            out.append(ch)
        else:
            out.append('\\u{:04x}'.format(code))
    return ''.join(out)

def rot13(s: str) -> str:
    """ROT13 шифр"""
    return codecs.encode(s, 'rot_13')

def rot47(s: str) -> str:
    """ROT47 шифр"""
    return ''.join(chr(33 + ((ord(c) - 33 + 47) % 94)) if 33 <= ord(c) <= 126 else c for c in s)

def gzip_base64(s: str) -> str:
    """Сжатие gzip + Base64"""
    gz = gzip.compress(s.encode('utf-8'))
    return base64.b64encode(gz).decode('ascii')

def zlib_base64(s: str) -> str:
    """Сжатие zlib + Base64"""
    c = zlib.compress(s.encode('utf-8'))
    return base64.b64encode(c).decode('ascii')

def bz2_base64(s: str) -> str:
    """Сжатие bz2 + Base64"""
    c = bz2.compress(s.encode('utf-8'))
    return base64.b64encode(c).decode('ascii')

def lzma_base64(s: str) -> str:
    """Сжатие lzma + Base64"""
    c = lzma.compress(s.encode('utf-8'))
    return base64.b64encode(c).decode('ascii')

def base32_std(s: str) -> str:
    """Base32 кодирование"""
    return base64.b32encode(s.encode('utf-8')).decode('ascii')

def base85_std(s: str) -> str:
    """Base85 кодирование"""
    return base64.b85encode(s.encode('utf-8')).decode('ascii')

def ascii85_std(s: str) -> str:
    """ASCII85 кодирование"""
    return base64.a85encode(s.encode('utf-8')).decode('ascii')

def quoted_printable(s: str) -> str:
    """Quoted-printable кодирование"""
    return quopri.encodestring(s.encode('utf-8')).decode('ascii')

def punycode(s: str) -> str:
    """Punycode кодирование"""
    try:
        return s.encode('punycode').decode('ascii')
    except Exception:
        return s

# --- Генераторы на базе различных байтовых кодировок ---

BYTE_ENCODINGS = ['utf-8', 'latin1', 'cp1251', 'cp1252', 'utf-16le', 'utf-16be', 'utf-7']

def make_bytes_transform(encoding: str, output: str) -> Callable[[str], str]:
    """Генерирует функцию преобразования строки в указанную байтовую кодировку с последующим выводом в hex/base64/percent"""
    def f_hex(s: str) -> str:
        try:
            b = s.encode(encoding, errors='replace')
            return binascii.hexlify(b).decode('ascii')
        except Exception:
            return s
    def f_b64(s: str) -> str:
        try:
            b = s.encode(encoding, errors='replace')
            return base64.b64encode(b).decode('ascii')
        except Exception:
            return s
    def f_pct(s: str) -> str:
        try:
            b = s.encode(encoding, errors='replace')
            return ''.join('%%%02X' % byte for byte in b)
        except Exception:
            return s

    if output == 'hex':
        return f_hex
    if output == 'base64':
        return f_b64
    if output == 'percent':
        return f_pct
    raise ValueError('unknown')



# 1. base64 без символов '+' и '/' (замена на '_' и '-')
def base64_custom_chars(s: str) -> str:
    b64 = base64.b64encode(s.encode('utf-8')).decode('ascii')
    return b64.replace('+', '_').replace('/', '-')

# 2. base64 с точками вместо '='
def base64_dot_pad(s: str) -> str:
    b64 = base64.b64encode(s.encode('utf-8')).decode('ascii')
    return b64.rstrip('=').ljust(len(b64), '.')

# 3. Base16 (hex) с разделителями ':'
def hex_colon(s: str) -> str:
    return ':'.join(f'{b:02x}' for b in s.encode('utf-8'))

# 4. Base16 с пробелами
def hex_space(s: str) -> str:
    return ' '.join(f'{b:02x}' for b in s.encode('utf-8'))

# 5. Обратный порядок байт в hex
def hex_reverse(s: str) -> str:
    b = s.encode('utf-8')
    return binascii.hexlify(b[::-1]).decode('ascii')

# 6. ROT5 для цифр
def rot5_digits(s: str) -> str:
    return ''.join(chr((ord(c) - ord('0') + 5) % 10 + ord('0')) if c.isdigit() else c for c in s)

# 7. ROT13 + base64
def rot13_base64(s: str) -> str:
    r = codecs.encode(s, 'rot_13')
    return base64.b64encode(r.encode('utf-8')).decode('ascii')

# 8. Base64 с переносами строк через 76 символов (стандарт MIME)
def base64_mime(s: str) -> str:
    return '\n'.join(base64.b64encode(s.encode('utf-8')).decode('ascii')[i:i+76] for i in range(0, len(s)*2, 76))

# 9. URL encode с пробелами как '+'
def url_encode_plus(s: str) -> str:
    return urllib.parse.quote_plus(s)

# 10. URL decode (на случай, если уже закодировано)
def url_decode(s: str) -> str:
    try:
        return urllib.parse.unquote(s)
    except Exception:
        return s

# 11. HTML escape с использованием только числовых ссылок (десятиричных)
def html_escape_num_only(s: str) -> str:
    return ''.join(f'&#{ord(c)};' if c in ['&', '<', '>', '"', "'"] else c for c in s)

# 12. Hex с префиксом 0x
def hex_0x_prefix(s: str) -> str:
    return ''.join(f'0x{b:02x}' for b in s.encode('utf-8'))

# 13. Unicode escape с заглавными X (например \uABCD)
def unicode_escape_upper(s: str) -> str:
    return ''.join(f'\\u{ord(c):04X}' if ord(c) > 127 else c for c in s)

# 14. Перемешать символы строки (shuffled)
def shuffle_string(s: str) -> str:
    import random
    lst = list(s)
    random.shuffle(lst)
    return ''.join(lst)

# 15. Повторить строку 2 раза
def repeat_2x(s: str) -> str:
    return s * 2

# 16. Повторить строку 3 раза
def repeat_3x(s: str) -> str:
    return s * 3

# 17. Добавить префикс 'ENC:' ко всем строкам
def prefix_enc(s: str) -> str:
    return 'ENC:' + s

# 18. Добавить суффикс ':END'
def suffix_end(s: str) -> str:
    return s + ':END'

# 19. Обратная строка
def reverse_string(s: str) -> str:
    return s[::-1]

# 20. Перевернуть байты UTF-8 и вернуть в hex
def reverse_bytes_hex(s: str) -> str:
    b = s.encode('utf-8')[::-1]
    return binascii.hexlify(b).decode('ascii')

# 21. Encode в UTF-16LE с BOM, потом base64
def utf16le_bom_base64(s: str) -> str:
    b = b'\xff\xfe' + s.encode('utf-16le')
    return base64.b64encode(b).decode('ascii')

# 22. Encode в UTF-16BE с BOM, потом base64
def utf16be_bom_base64(s: str) -> str:
    b = b'\xfe\xff' + s.encode('utf-16be')
    return base64.b64encode(b).decode('ascii')

# 23. Zlib compress с уровнем 9, base64
def zlib_max_base64(s: str) -> str:
    c = zlib.compress(s.encode('utf-8'), level=9)
    return base64.b64encode(c).decode('ascii')

# 24. Gzip compress с уровнем 9, base64
def gzip_max_base64(s: str) -> str:
    gz = gzip.compress(s.encode('utf-8'), compresslevel=9)
    return base64.b64encode(gz).decode('ascii')

# 25. Преобразовать строку в последовательность ASCII кодов через '-'
def ascii_codes_dash(s: str) -> str:
    return '-'.join(str(ord(c)) for c in s)

# 26. Преобразовать в ASCII коды, затем hex (например "65 66" -> "4146")
def ascii_codes_to_hex(s: str) -> str:
    codes = ''.join(str(ord(c)) for c in s)
    return binascii.hexlify(codes.encode('ascii')).decode('ascii')

# 27. Base64 encode и удалить все символы '='
def base64_no_pad(s: str) -> str:
    return base64.b64encode(s.encode('utf-8')).decode('ascii').rstrip('=')

# 28. Base85 encode, потом rot13
def base85_rot13(s: str) -> str:
    b85 = base64.b85encode(s.encode('utf-8')).decode('ascii')
    return codecs.encode(b85, 'rot_13')

# 29. Base32 encode с удалением '='
def base32_no_pad(s: str) -> str:
    return base64.b32encode(s.encode('utf-8')).decode('ascii').rstrip('=')

# 30. Удалить все пробелы и табы из строки
def remove_whitespace(s: str) -> str:
    return s.replace(' ', '').replace('\t', '')

# 31. Преобразовать в Unicode codepoints через пробел
def unicode_codepoints_space(s: str) -> str:
    return ' '.join(f'U+{ord(c):04X}' for c in s)

# 32. Экранировать кавычки (")
def escape_quotes(s: str) -> str:
    return s.replace('"', '\\"')

# 33. Экранировать апострофы (')
def escape_apostrophes(s: str) -> str:
    return s.replace("'", "\\'")

# 34. Base64 encode, но заменить 'A' на '@'
def base64_replace_a(s: str) -> str:
    return base64.b64encode(s.encode('utf-8')).decode('ascii').replace('A', '@')

# 35. Quoted-printable с заменой '_' на '=5F'
def qp_custom(s: str) -> str:
    qp = quopri.encodestring(s.encode('utf-8')).decode('ascii')
    return qp.replace('_', '=5F')

# 36. hex encode, затем base64 encode
def hex_then_base64(s: str) -> str:
    h = binascii.hexlify(s.encode('utf-8'))
    return base64.b64encode(h).decode('ascii')

# 37. base64 encode, потом hex encode
def base64_then_hex(s: str) -> str:
    b64 = base64.b64encode(s.encode('utf-8'))
    return binascii.hexlify(b64).decode('ascii')

# 38. zlib compress, затем hex encode
def zlib_then_hex(s: str) -> str:
    c = zlib.compress(s.encode('utf-8'))
    return binascii.hexlify(c).decode('ascii')

# 39. lzma compress, затем hex encode
def lzma_then_hex(s: str) -> str:
    c = lzma.compress(s.encode('utf-8'))
    return binascii.hexlify(c).decode('ascii')

TRANSFORMS: Dict[str, Callable[[str], str]] = {
    'noop': noop,
    'base64': base64_std,
    'base64_urlsafe': base64_urlsafe,
    'base64_nopad': base64_nopad,
    'hex_lower': hex_lower,
    'hex_upper': hex_upper,
    'backslash_x': backslash_x,
    'url_all': url_encode_all,
    'url_safe_slash': url_encode_safe_slash,
    'double_url': double_url,
    'html_named': html_escape_named,
    'html_num_dec': html_numeric_dec,
    'html_num_hex': html_numeric_hex,
    'unicode_escape': unicode_escape_python,
    'js_escape': js_escape,
    'rot13': rot13,
    'rot47': rot47,
    'gzip_base64': gzip_base64,
    'zlib_base64': zlib_base64,
    'bz2_base64': bz2_base64,
    'lzma_base64': lzma_base64,
    'base32': base32_std,
    'base85': base85_std,
    'ascii85': ascii85_std,
    'quoted_printable': quoted_printable,
    'punycode': punycode,
    'base64_custom_chars': base64_custom_chars,
    'base64_dot_pad': base64_dot_pad,
    'hex_colon': hex_colon,
    'hex_space': hex_space,
    'hex_reverse': hex_reverse,
    'rot5_digits': rot5_digits,
    'rot13_base64': rot13_base64,
    'base64_mime': base64_mime,
    'url_encode_plus': url_encode_plus,
    'url_decode': url_decode,
    'html_escape_num_only': html_escape_num_only,
    'hex_0x_prefix': hex_0x_prefix,
    'unicode_escape_upper': unicode_escape_upper,
    'shuffle_string': shuffle_string,
    'repeat_2x': repeat_2x,
    'repeat_3x': repeat_3x,
    'prefix_enc': prefix_enc,
    'suffix_end': suffix_end,
    'reverse_string': reverse_string,
    'reverse_bytes_hex': reverse_bytes_hex,
    'utf16le_bom_base64': utf16le_bom_base64,
    'utf16be_bom_base64': utf16be_bom_base64,
    'zlib_max_base64': zlib_max_base64,
    'gzip_max_base64': gzip_max_base64,
    'ascii_codes_dash': ascii_codes_dash,
    'ascii_codes_to_hex': ascii_codes_to_hex,
    'base64_no_pad': base64_no_pad,
    'base85_rot13': base85_rot13,
    'base32_no_pad': base32_no_pad,
    'remove_whitespace': remove_whitespace,
    'unicode_codepoints_space': unicode_codepoints_space,
    'escape_quotes': escape_quotes,
    'escape_apostrophes': escape_apostrophes,
    'base64_replace_a': base64_replace_a,
    'qp_custom': qp_custom,
    'hex_then_base64': hex_then_base64,
    'base64_then_hex': base64_then_hex,
    'zlib_then_hex': zlib_then_hex,
    'lzma_then_hex': lzma_then_hex,
}

for enc in BYTE_ENCODINGS:
    for out in ('hex', 'base64', 'percent'):
        name = f'{enc.replace("-", "")}_{out}'
        TRANSFORMS[name] = make_bytes_transform(enc, out)

def url_pct_lower(s: str) -> str:
    return urllib.parse.quote(s, safe='').lower()

def percent_bytes_lower(s: str) -> str:
    b = s.encode('utf-8')
    return ''.join('%%%02x' % byte for byte in b)

TRANSFORMS['url_pct_lower'] = url_pct_lower
TRANSFORMS['percent_bytes_lower'] = percent_bytes_lower

def _nested_quote(s: str, n: int) -> str:
    t = s
    for _ in range(n):
        t = urllib.parse.quote(t, safe='')
    return t

for i in range(2, 6):
    TRANSFORMS[f'double_url_{i}x'] = (lambda n=i: (lambda s: _nested_quote(s, n)))()

existing_keys = list(TRANSFORMS.keys())
N_pairs = 30
for i in range(min(N_pairs, len(existing_keys))):
    for j in range(i+1, min(i+4, len(existing_keys))):
        a = existing_keys[i]
        b = existing_keys[j]
        name = f'{a}__then__{b}'
        f_a = TRANSFORMS[a]
        f_b = TRANSFORMS[b]
        def make_chain(f1, f2):
            def chain(s: str) -> str:
                try:
                    return f2(f1(s))
                except Exception:
                    return s
            return chain
        TRANSFORMS[name] = make_chain(f_a, f_b)

# --- Утилиты ---
def list_transforms() -> list:
    return sorted(TRANSFORMS.keys())

# запуск как модуль: python -m transforms --list
if __name__ == '__main__':
    import argparse, sys
    parser = argparse.ArgumentParser(description='Помощник модуля transforms')
    parser.add_argument('--list', action='store_true', help='Показать список доступных трансформаций и выйти')
    args = parser.parse_args()
    if args.list:
        print("Доступные трансформации:")
        for name in list_transforms():
            print(f" - {name}")
        sys.exit(0)
    print('Запустите: python -m transforms --list, чтобы увидеть список доступных трансформаций')
