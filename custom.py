import collections


def is_chinese(uchar):
    """判断一个unicode是否是汉字"""
    return uchar >= u'\u4e00' and uchar <= u'\u9fa5'


def is_can_stay(uchar):
    if is_chinese(uchar) and len(uchar) > 1:
        return False
    if uchar.startswith("?"):
        return False
    return True


def is_line_can_stay(line):
    first = str(line.split("\t")[0])
    if not is_can_stay(first):
        print("trim", line)
        return False
    return True


def get_single_char_line(line):
    if not is_line_can_stay(line):
        return
    return line


def simp_file(name, out):
    simp_file_fn(name, out, get_single_char_line)


def simp_file_fn(name, out, fn):
    mark="..."
    lines = []
    begin = False
    with open(name, "r", encoding="utf8") as f:
        for line in f:
            if begin:
                line = fn(line)
            else:
                if line.startswith(mark):
                    begin = True
            if line:
                lines.append(line)

    if not begin:
        print("never begin")
        return
    with open(out, "w+", encoding="utf8") as f:
        f.writelines(lines)


def get_flypy_no_end_line():
    word_to_py = collections.defaultdict(set)
    def fn(line):
        args = line.split("\t")
        word = args[0]
        if not is_chinese(word):
            return

        py = args[1]
        if len(py) > 2:
            py = py[:2]

        if py in word_to_py[word]:
            return
        word_to_py[word].add(py) 

        args[1] = py
        return "\t".join(args) + "\n"
    return fn



def flypy_no_end(filename):
    """小鹤双拼去掉加形"""
    simp_file_fn(filename, filename + ".no_end", get_flypy_no_end_line())
    

def get_word_to_code(filename):
    word_to_code = collections.defaultdict(list)
    begin = False
    with open(filename, "r", encoding="utf8") as f:
        for line in f:
            if begin:
                args = line.split("\t")
                if len(args) < 2:
                    continue
                word = args[0]
                code = args[1].strip()
                word_to_code[word].append(code)
            else:
                if line.startswith("..."):
                    begin = True
    return word_to_code


FLYPY_WUBI_PREFIX = """
# Rime dict
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


def to_flypy_wubi(filename="flypy_yk.wubi.dict.yaml"):
    word_to_wubi = get_word_to_code("wubi86_jidian.dict.yaml")
    word_to_py = get_word_to_code("flypy_yk.base.dict.yaml")
    print("wubi", len(word_to_wubi))
    print("flypy", len(word_to_py))

    lines = [FLYPY_WUBI_PREFIX]
    for word, pys in word_to_py.items():
        wubis = word_to_wubi.get(word)
        if not wubis:
            continue
        for py in pys:
            wubi = max(wubis, key=len)
            lines.append(word + "\t" + py + wubi[:1] + "\n")
            lines.append(word + "\t" + py + wubi[:2] + "\n")

    with open(filename, "w", encoding="utf8") as f:
        f.writelines(lines)


def code_word_swap(filename):
    def fn(line):
        args = line.split("\t")
        if len(args) < 2:
            return
        code = args[0].strip()
        word = args[1].strip()
        return word + "\t" + code + "\n"
    simp_file_fn(filename, filename + ".swap", fn)


def main():
    # simp_file("wubi86_jidian.dict.yaml.org", "wubi86_jidian.dict.yaml")
    # simp_file("double_pinyin_flypy.dict.yaml.org", "double_pinyin_flypy.dict.yaml")

    code_word_swap("x.yaml")
    # flypy_no_end("x.yaml.swap")
    # to_flypy_wubi("flypy_yk.wubi.dict.yaml")
    print("done")


if __name__ == "__main__":
    main()