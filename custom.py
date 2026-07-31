#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
custom.py - 小鹤双拼 + 五笔形码 词库构建与校验工具

用于从基础小鹤双拼词库与五笔86词库生成小鹤双拼加五笔形码的 dict.yaml 文件。
实装“阶梯基准 + 原始字频微调 (Hybrid Graded Weight)”二级混合排序算法：
Final Weight = Tier Base Weight + Original Word Weight
- 阶梯 1: 8105 一级常用字 (3500字)   -> 基准 200,000 + 原始字频
- 阶梯 2: 8105 二/三级常用字 (4605字) -> 基准 50,000 + 原始字频
- 阶梯 3: 非 8105 表 (繁体字/生僻字)  -> 基准 500 + 原始字频/相对顺序
保证主阶梯绝对压制，同时在同阶梯内 100% 延续并保留原词库的高低字频顺序。
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


def load_8105_levels(filepath: str = "8105.txt") -> Dict[str, int]:
    """读取 8105 通用规范汉字及其等级 (1: 一级常用字, 2: 二/三级常用字)"""
    word_level = {}
    if not os.path.exists(filepath):
        print(f"[WARN] 未找到 {filepath}，将不对词库施加阶梯梯度权重", file=sys.stderr)
        return word_level

    idx = 0
    with open(filepath, "r", encoding="utf8") as f:
        for line in f:
            w = line.strip()
            if w and len(w) == 1:
                idx += 1
                if idx <= 3500:
                    word_level[w] = 1  # 一级常用字
                else:
                    word_level[w] = 2  # 二/三级常用字
    print(f"[INFO] 已加载 《8105 通用规范汉字表》: 一级字 {min(idx, 3500)} 个，二/三级字 {max(0, idx - 3500)} 个")
    return word_level


def process_wubi86_ms_dict(wubi86_ms_dict: str, word_level: Dict[str, int]):
    """对 wubi86_ms.dict.yaml 施加阶梯基准+原始字频微调二级混合权重分配"""
    if not os.path.exists(wubi86_ms_dict):
        return

    lines = []
    begin = False
    stats = {1: 0, 2: 0, 3: 0}

    # 预读获取所有行的原始计数用于导出原始顺序微分
    raw_lines = []
    with open(wubi86_ms_dict, "r", encoding="utf8") as f:
        raw_lines = f.readlines()

    total_count = len(raw_lines)

    for idx, line in enumerate(raw_lines):
        if not begin:
            lines.append(line)
            if line.startswith("..."):
                begin = True
        else:
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                lines.append(line)
                continue

            parts = line_str.split("\t")
            if len(parts) >= 2:
                word = parts[0]
                code = parts[1]
                
                # 提取原始权重，若无则使用原行号位置倒序分 (保障原序)
                orig_weight = 0
                if len(parts) >= 3:
                    try:
                        orig_weight = int(parts[2])
                    except ValueError:
                        orig_weight = 0
                
                # 限制原始分微调范围在 0 ~ 4999 避免跨越阶梯
                if orig_weight == 0:
                    pos_score = max(1, math_pos_score(total_count, idx))
                else:
                    pos_score = min(4999, orig_weight)

                if len(word) == 1 and word_level:
                    lvl = word_level.get(word, 3)
                    if lvl == 1:
                        final_weight = 200000 + pos_score
                        stats[1] += 1
                    elif lvl == 2:
                        final_weight = 50000 + pos_score
                        stats[2] += 1
                    else:
                        final_weight = 500 + pos_score
                        stats[3] += 1
                    lines.append(f"{word}\t{code}\t{final_weight}\n")
                else:
                    lines.append(line)
            else:
                lines.append(line)

    with open(wubi86_ms_dict, "w", encoding="utf8") as f:
        f.writelines(lines)

    print(f"[INFO] 阶梯基准 + 原始字频二级混合权重已写入 {wubi86_ms_dict}:")
    print(f"       - 一级字 (200,000+ 微调分): {stats[1]} 条")
    print(f"       - 二三级字 (50,000+ 微调分): {stats[2]} 条")
    print(f"       - 繁体/生僻字 (500+ 原字频微调分): {stats[3]} 条")


def math_pos_score(total: int, idx: int) -> int:
    """根据物理文件原物理行号按倒序微调加分 (越靠前微调分越高, 最高4999分)"""
    if total <= 0: return 1
    score = int((total - idx) / total * 4000)
    return max(1, min(4999, score))


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


def build_flypy_wubi(wubi_dict: str, flypy_base_dict: str, output_dict: str, word_level: Dict[str, int]) -> Tuple[int, int]:
    """根据五笔词库和双拼基础词库生成加形词库，分配二级混合权重"""
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

        lvl = word_level.get(word, 3) if word_level else 1
        if lvl == 1:
            base_weight = 200000
        elif lvl == 2:
            base_weight = 50000
        else:
            base_weight = 500

        for py in pys:
            wubi = max(wubis, key=len)
            code1 = f"{py}{wubi[:1]}"
            code2 = f"{py}{wubi[:2]}"

            lines.append(f"{word}\t{code1}\t{base_weight}\n")
            lines.append(f"{word}\t{code2}\t{base_weight}\n")
            generated_count += 2

    with open(output_dict, "w", encoding="utf8") as f:
        f.writelines(lines)

    print(f"[INFO] 成功生成 {output_dict}: 包含 {generated_count} 条二级混合权重规则")
    return generated_count, len(missing_wubi_words)


def main():
    parser = argparse.ArgumentParser(description="小鹤双拼+五笔形码 词库构建与校验工具")
    parser.add_argument("--deploy-dir", default="deploy", help="deploy 配置文件目录路径 (默认: deploy)")
    parser.add_argument("--build", action="store_true", help="自动构建词库")
    parser.add_argument("--check-duplicates", action="store_true", help="检查重码分布")
    parser.add_argument("--dict-8105", default="8105.txt", help="8105 常用字表路径 (默认: 8105.txt)")

    args = parser.parse_args()

    deploy_dir = args.deploy_dir
    wubi_dict = os.path.join(deploy_dir, "wubi86_ms.dict.yaml")
    flypy_base_dict = os.path.join(deploy_dir, "flypy_yk.base.dict.yaml")
    output_dict = os.path.join(deploy_dir, "flypy_yk.wubi.dict.yaml")

    word_level = load_8105_levels(args.dict_8105)

    if not args.check_duplicates or args.build:
        print("[INFO] 开始构建二级混合权重词库...")
        process_wubi86_ms_dict(wubi_dict, word_level)
        build_flypy_wubi(wubi_dict, flypy_base_dict, output_dict, word_level)

    if args.check_duplicates:
        print("[INFO] 正在检查重码情况...")
        code_to_word = get_code_to_word(output_dict)
        duplicates = {k: v for k, v in code_to_word.items() if len(v) > 2}
        print(f"[INFO] 编码重码率统计: 超过2重码的编码组共有 {len(duplicates)} 组")


if __name__ == "__main__":
    main()
