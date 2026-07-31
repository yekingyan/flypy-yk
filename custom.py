#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
custom.py - 小鹤双拼 + 五笔形码 词库构建与校验工具

用于从基础小鹤双拼词库与五笔86词库生成小鹤双拼加五笔形码的 dict.yaml 文件。
"""

import argparse
import collections
import os
import sys
from typing import Dict, List, Set, Tuple, Optional


FLYPY_WUBI_PREFIX = """# Rime dict
# encoding: utf-8
# 小鹤双拼加五笔形码
# 如"这"字，双拼码为ve，五笔码为yp，则加形后的码为vey

---
name: flypy_yk.wubi
version: "0.0.1"
sort: original
use_preset_vocabulary: false

...

"""


def is_chinese(uchar: str) -> bool:
    """判断一个字符是否为常用汉字"""
    return u'\u4e00' <= uchar <= u'\u9fa5'


def get_line_to_dict(filename: str, func) -> Dict[str, List[str]]:
    """读取 dict.yaml 文件提取 header 后 key-value 数据结构"""
    ret = collections.defaultdict(list)
    if not os.path.exists(filename):
        print(f"[ERROR] 文件不存在: {filename}", file=sys.stderr)
        return ret

    begin = False
    with open(filename, "r", encoding="utf8") as f:
        for line in f:
            if begin:
                line_str = line.strip()
                if not line_str or line_str.startswith("#"):
                    continue
                args = line_str.split("\t")
                if len(args) < 2:
                    continue
                key, value = func(args)
                if key is not None:
                    ret[key].append(value)
            else:
                if line.startswith("..."):
                    begin = True
    return ret


def get_word_to_code(filename: str) -> Dict[str, List[str]]:
    """获取 Word -> Code 映射"""
    def fn(args: List[str]) -> Tuple[str, str]:
        return args[0], args[1].strip()
    return get_line_to_dict(filename, fn)


def get_code_to_word(filename: str) -> Dict[str, List[str]]:
    """获取 Code -> Word 映射"""
    def fn(args: List[str]) -> Tuple[str, str]:
        return args[1].strip(), args[0]
    return get_line_to_dict(filename, fn)


def build_flypy_wubi(wubi_dict: str, flypy_base_dict: str, output_dict: str) -> Tuple[int, int]:
    """
    根据五笔词库和双拼基础词库生成加形词库
    返回: (成功生成的条目数, 缺失五笔编码的汉字数)
    """
    word_to_wubi = get_word_to_code(wubi_dict)
    word_to_py = get_word_to_code(flypy_base_dict)

    if not word_to_wubi or not word_to_py:
        print("[ERROR] 词库加载失败，请检查输入路径", file=sys.stderr)
        return 0, 0

    lines = [FLYPY_WUBI_PREFIX]
    generated_count = 0
    missing_wubi_words = []

    for word, pys in word_to_py.items():
        wubis = word_to_wubi.get(word)
        if not wubis:
            missing_wubi_words.append(word)
            continue

        for py in pys:
            # 选取最长五笔编码
            wubi = max(wubis, key=len)
            lines.append(f"{word}\t{py}{wubi[:1]}\n")
            lines.append(f"{word}\t{py}{wubi[:2]}\n")
            generated_count += 2

    with open(output_dict, "w", encoding="utf8") as f:
        f.writelines(lines)

    print(f"[INFO] 成功生成 {output_dict}: 包含 {generated_count} 条规则")
    if missing_wubi_words:
        print(f"[WARN] 有 {len(missing_wubi_words)} 个汉字未在五笔词库中找到编码 (例: {missing_wubi_words[:10]})")

    return generated_count, len(missing_wubi_words)


def main():
    parser = argparse.ArgumentParser(description="小鹤双拼+五笔形码 词库构建与校验工具")
    parser.add_argument("--deploy-dir", default="deploy", help="deploy 配置文件目录路径 (默认: deploy)")
    parser.add_argument("--build", action="store_true", help="自动构建 flypy_yk.wubi.dict.yaml 词库")
    parser.add_argument("--check-duplicates", action="store_true", help="检查重码分布")

    args = parser.parse_args()

    deploy_dir = args.deploy_dir
    wubi_dict = os.path.join(deploy_dir, "wubi86_ms.dict.yaml")
    flypy_base_dict = os.path.join(deploy_dir, "flypy_yk.base.dict.yaml")
    output_dict = os.path.join(deploy_dir, "flypy_yk.wubi.dict.yaml")

    # 默认若无特殊参数则执行 --build
    if not args.check_duplicates or args.build:
        print("[INFO] 开始构建双拼五笔形码词库...")
        build_flypy_wubi(wubi_dict, flypy_base_dict, output_dict)

    if args.check_duplicates:
        print("[INFO] 正在检查重码情况...")
        code_to_word = get_code_to_word(output_dict)
        duplicates = {k: v for k, v in code_to_word.items() if len(v) > 2}
        print(f"[INFO] 编码重码率统计: 超过2重码的编码组共有 {len(duplicates)} 组")


if __name__ == "__main__":
    main()
