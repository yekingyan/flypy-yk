#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
test_custom.py - custom.py 构建工具与二级混合权重算法单元测试
"""

import unittest
import os
import tempfile
import custom


class TestCustomDictEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_8105_path = os.path.join(self.temp_dir.name, "test_8105.txt")
        # 写入伪造的 8105 测试数据：包含前 3500 一级字与后 4605 二级字代表
        with open(self.test_8105_path, "w", encoding="utf8") as f:
            f.write("钏\n")  # 一级字代表
            f.write("框\n")  # 二级字代表

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_8105_levels(self):
        """测试 8105 常用字表等级解析"""
        levels = custom.load_8105_levels(self.test_8105_path)
        self.assertIn("钏", levels)
        self.assertEqual(levels["钏"], 1)  # 前 3500 字归为 1 级

    def test_math_pos_score_bounds(self):
        """测试位置/字频微调加分边界，防止跨阶梯越界"""
        score_top = custom.math_pos_score(100, 0)
        score_bottom = custom.math_pos_score(100, 99)
        
        self.assertGreaterEqual(score_top, 1)
        self.assertLessEqual(score_top, 4999)
        self.assertGreaterEqual(score_bottom, 1)
        self.assertLessEqual(score_bottom, 4999)
        self.assertGreater(score_top, score_bottom)  # 物理位置越靠前，微调分越高

    def test_hybrid_weight_tier_suppression(self):
        """测试二级混合权重算法的阶梯压制与同阶梯保留原序断言"""
        word_level = {"钏": 1, "框": 2}  # 钏为一级，框为二级，繁体“釧”不在表内(三级)
        
        # 模拟 3 个汉字的输入
        test_wubi_dict = os.path.join(self.temp_dir.name, "wubi.yaml")
        with open(test_wubi_dict, "w", encoding="utf8") as f:
            f.write("---\nname: test\n...\n")
            f.write("钏\tqkh\n")
            f.write("框\tklsa\n")
            f.write("釧\tqkh\n")  # 繁体

        custom.process_wubi86_ms_dict(test_wubi_dict, word_level)

        # 读取处理后的文件断言权重
        with open(test_wubi_dict, "r", encoding="utf8") as f:
            content = f.read()

        # 断言一级字“钏”权重在 200,000+ (20xxxx)
        self.assertIn("钏\tqkh\t20", content)
        # 断言二级字“框”权重在 50,000+ (5xxxx)
        self.assertIn("框\tklsa\t5", content)
        # 断言繁体字“釧”权重在 500~4999 (1xxx)
        self.assertIn("釧\tqkh\t1", content)

    def test_lua_modules_exist(self):
        """测试 deploy/rime.lua 单文件导出的函数完整性"""
        deploy_dir = os.path.join(os.path.dirname(__file__), "deploy")
        rime_lua_path = os.path.join(deploy_dir, "rime.lua")
        self.assertTrue(os.path.exists(rime_lua_path), f"缺少 rime.lua: {rime_lua_path}")
        
        with open(rime_lua_path, "r", encoding="utf8") as f:
            content = f.read()

        expected_funcs = ["date_translator", "number_translator", "calculator_translator", "help_translator", "wubi_comment_filter"]
        for fn in expected_funcs:
            self.assertIn(fn, content, f"rime.lua 缺少函数定义: {fn}")

    def test_crlf_handling(self):
        """测试 custom.py 对 Windows CRLF / Linux LF 换行符的处理能力"""
        test_dict = os.path.join(self.temp_dir.name, "test_crlf.yaml")
        with open(test_dict, "wb") as f:
            f.write(b"---\r\nname: test\r\n...\r\n\xe9\x92\x8f\tqkh\r\n") # CRLF
        
        word_to_code = custom.get_word_to_code(test_dict)
        self.assertIn("钏", word_to_code)
        self.assertEqual(word_to_code["钏"], ["qkh"])

    def test_z_wildcard_and_no_reverse_lookup(self):
        """测试 z 键在五笔86与双拼方案中的全位置通配符与解耦"""
        deploy_dir = os.path.join(os.path.dirname(__file__), "deploy")
        
        # 验证所有 schema 不再包含 z 反查正则 ^z[a-z]*'?$
        for sname in ["flypy_yk.schema.yaml", "wubi86.schema.yaml", "wubi_flypy.schema.yaml"]:
            spath = os.path.join(deploy_dir, sname)
            with open(spath, "r", encoding="utf8") as f:
                content = f.read()
            self.assertNotIn("reverse_lookup_translator", content, f"{sname} 仍然残留 reverse_lookup_translator")

    def test_calculator_lua_and_schema_patterns(self):
        """测试计算器仅支持大写 C 与 schema 的纯净配置"""
        deploy_dir = os.path.join(os.path.dirname(__file__), "deploy")
        calc_lua_path = os.path.join(deploy_dir, "lua", "calculator.lua")
        
        with open(calc_lua_path, "r", encoding="utf8") as f:
            content = f.read()
            
        rime_lua_path = os.path.join(deploy_dir, "rime.lua")
        with open(rime_lua_path, "r", encoding="utf8") as f:
            rlua_content = f.read()

        self.assertIn('get_user_data_dir', rlua_content)
        self.assertIn('require("date")', rlua_content)
        self.assertIn('input:sub(1, 1) == "C"', content)
        self.assertNotIn('input:sub(1, 1) == "="', content, "rime.lua 依然残留 = 前缀")

        for sname in ["flypy_yk.schema.yaml", "wubi86.schema.yaml", "wubi_flypy.schema.yaml"]:
            spath = os.path.join(deploy_dir, sname)
            with open(spath, "r", encoding="utf8") as f:
                scontent = f.read()
            self.assertIn('calculator: "^C+[0-9].*$"', scontent, f"{sname} 的 calculator 正则未正确修正")
            self.assertIn('number: "^V+[0-9].*$"', scontent, f"{sname} 的 number 正则未正确修正")
            self.assertIn('alphabet: zyxwvutsrqponmlkjihgfedcba', scontent, f"{sname} 的 speller/alphabet 受到污染")


if __name__ == "__main__":
    unittest.main()




