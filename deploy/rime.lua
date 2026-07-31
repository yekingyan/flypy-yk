-- rime.lua - Rime Lua 扩展入口 (模块化架构)
-- 各子模块放置于 deploy/lua/ 目录下

date_translator = require("lua/date")
number_translator = require("lua/number")
calculator_translator = require("lua/calculator")
help_translator = require("lua/help")
wubi_comment_filter = require("lua/wubi_comment")
