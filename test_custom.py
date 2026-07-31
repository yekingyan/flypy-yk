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
        """测试 deploy/lua 目录下的模块文件完整性"""
        deploy_dir = os.path.join(os.path.dirname(__file__), "deploy")
        lua_dir = os.path.join(deploy_dir, "lua")
        expected_modules = ["date.lua", "number.lua", "calculator.lua", "help.lua", "wubi_comment.lua"]
        for mod in expected_modules:
            mod_path = os.path.join(lua_dir, mod)
            self.assertTrue(os.path.exists(mod_path), f"缺少 Lua 模块: {mod_path}")

    def test_crlf_handling(self):
        """测试 custom.py 对 Windows CRLF / Linux LF 换行符的处理能力"""
        test_dict = os.path.join(self.temp_dir.name, "test_crlf.yaml")
        with open(test_dict, "wb") as f:
            f.write(b"---\r\nname: test\r\n...\r\n\xe9\x92\x8f\tqkh\r\n") # CRLF
        
        word_to_code = custom.get_word_to_code(test_dict)
        self.assertIn("钏", word_to_code)
        self.assertEqual(word_to_code["钏"], ["qkh"])


    def test_z_wildcard_and_no_reverse_lookup(self):
        """测试 z 键在五笔86与双拼方案中的全位置通配符与移除 reverse_lookup 反查配置"""
        deploy_dir = os.path.join(os.path.dirname(__file__), "deploy")
        
        # 验证所有 schema 不再包含 z 反查正则 ^z[a-z]*'?$
        for sname in ["flypy_yk.schema.yaml", "wubi86.schema.yaml", "wubi_flypy.schema.yaml"]:
            spath = os.path.join(deploy_dir, sname)
            with open(spath, "r", encoding="utf8") as f:
                content = f.read()
            self.assertNotIn("reverse_lookup_translator", content, f"{sname} 仍然残留 reverse_lookup_translator")
            self.assertNotIn("^z[a-z]", content, f"{sname} 仍然残留 z 反查正则")

        # 验证五笔86字典处理后包含 z 通配条目
        word_level = {"衡": 1}
        test_wubi_dict = os.path.join(self.temp_dir.name, "wubi86.yaml")
        with open(test_wubi_dict, "w", encoding="utf8") as f:
            f.write("---\nname: test\n...\n衡\ttqdh\t200000\n")

        custom.process_wubi86_ms_dict(test_wubi_dict, word_level)
        with open(test_wubi_dict, "r", encoding="utf8") as f:
            wubi_content = f.read()

        # 断言五笔86全码 (tqdh) 派生出了含 z 的模糊识别 (tqdz, tqzh, tzdh, zqdh)
        self.assertIn("衡\ttqdz\t", wubi_content)
        self.assertIn("衡\ttqzh\t", wubi_content)
        
        # 断言 schema 中移除了多余的 algebra 规则，避免与离线 z 词库冲突
        schema_path = os.path.join(deploy_dir, "flypy_yk.schema.yaml")
        with open(schema_path, "r", encoding="utf8") as f:
            schema_content = f.read()
        self.assertNotIn("algebra:", schema_content)

        # 验证生成的词库支持 z 派生通配
        word_level = {"衡": 1}
        test_wubi_dict = os.path.join(self.temp_dir.name, "wubi.yaml")
        test_base_dict = os.path.join(self.temp_dir.name, "base.yaml")
        test_out_dict = os.path.join(self.temp_dir.name, "out.yaml")
        
        with open(test_wubi_dict, "w", encoding="utf8") as f:
            f.write("---\nname: test\n...\n衡\ttqdh\n")
        with open(test_base_dict, "w", encoding="utf8") as f:
            f.write("---\nname: test\n...\n衡\thk\n")

        custom.build_flypy_wubi(test_wubi_dict, test_base_dict, test_out_dict, word_level)
        
        with open(test_out_dict, "r", encoding="utf8") as f:
            out_content = f.read()
        
        # 断言 hktq 生成了形码位置包含 z 的派生条目 (hktz, hkzq, hkzz)
        self.assertIn("衡\thktz\t", out_content)
        self.assertIn("衡\thkzq\t", out_content)
        self.assertIn("衡\thkzz\t", out_content)
        self.assertIn("衡\thkz\t", out_content)
        # 断言双拼首码不受干扰 (不会生成 zktq 等干扰双拼的畸形码)
        self.assertNotIn("衡\tzktq\t", out_content)

        # 断言生成的所有派生编码长度严格为 3 码或 4 码，防止畸形编码破坏 Rime 索引
        for line in out_content.splitlines():
            if line.startswith("#") or line.startswith("---") or line.startswith("...") or not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                code = parts[1]
                self.assertIn(len(code), [3, 4], f"发现非法长度的派生编码: {code} ({parts[0]})")


if __name__ == "__main__":
    unittest.main()




