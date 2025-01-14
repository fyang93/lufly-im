# encoding=utf8
import re
import sys
from datetime import datetime
from typing import List

from toolz.curried import filter, curry

from common import full_to_two, get_exists_words
from common import get_full_to_bingji_transformer, get_full_to_xhe_transformer, get_full_to_zrm_transformmer, \
    get_full_to_lu_transformmer, get_full
from tables import db, TangshiTable


def cols_to_tangshi_item(cols: List[str], xhe_transformer, zrm_transformer,
                         bingji_transformer, lu_transformer) -> TangshiTable:
    if len(cols) == 1:
        word = cols[0]
        priority = 100
        full = get_full(word)
    elif len(cols) == 2:
        word = cols[0]
        priority = cols[1]
        full = get_full(word)
    elif len(cols) == 2 + len(cols[0]):
        word = cols[0]
        priority = cols[1]
        full = list(filter(lambda e: len(e) > 0,
                           [e.strip() for e in cols[2:]]))
    else:
        raise RuntimeError("word item should be: 你好 [priority ni hao]")

    item = TangshiTable(
        word=word,
        full=' '.join(full),
        xhe=''.join([full_to_two(e, xhe_transformer) for e in full]),
        zrm=''.join([full_to_two(e, zrm_transformer) for e in full]),
        lu=''.join([full_to_two(e, lu_transformer) for e in full]),
        priority=priority,
        updatedt=datetime.now(),
        bingji=''.join(
            full_to_two(e, bingji_transformer, bingji=True) for e in full))
    print("add ", item)
    return item


def contain_alpha(word: str) -> bool:
    for c in word:
        if c.lower() in "abcdefghijklmnopqrstuvwxyz":
            return True

    return False


def contain_symbols(word: str) -> bool:
    if re.match(
            '[1234567890’!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~，。！@#$%^&*………_+}{}]+',
            word) is None:
        return False
    else:
        return True


def load_words(filepath: str):
    exist_words = get_exists_words()

    xhe_transformer = get_full_to_xhe_transformer()
    zrm_transformer = get_full_to_zrm_transformmer()
    lu_transformer = get_full_to_lu_transformmer()
    bingji_transformer = get_full_to_bingji_transformer()

    words = []
    with open(filepath, 'r', encoding='utf8') as fin:
        for line in fin:
            line = line.strip()
            if len(line) == 0: continue
            cols = line.split(" ")
            if len(cols) > 5:
                print(f"wrong line {line}")
                continue
            if contain_alpha(cols[0]) or contain_symbols(cols[0]):
                print(f"contains num or symbols {line}")
                continue
            if cols[0] in exist_words: continue
            words.append(
                cols_to_tangshi_item(cols, xhe_transformer, zrm_transformer, bingji_transformer, lu_transformer))
            exist_words.add(cols[0])

    return words


def main():
    if len(sys.argv) != 2:
        print(f"使用方法: python3 {sys.argv[0]} words.txt", file=sys.stderr)
        print("文件行格式:word [prioroty w1_yin w2_yin ...]")
        print("举例:你好 [10 ni hao]")
        print("中括号内为可选内容")
        sys.exit(1)

    _, words_path = sys.argv

    add_words = load_words(words_path)
    print(add_words)
    with db.atomic():
        TangshiTable.bulk_create(add_words, batch_size=100)

    print(f'done, add {len(add_words)} items')


if __name__ == "__main__":
    main()
