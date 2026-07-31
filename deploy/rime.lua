-- rime.lua - Rime Lua 动态模块化加载入口

-- 1. 动态注入用户配置目录至 Lua package.path 搜寻路径 (解决 Weasel 搜寻路径缺失问题)
if rime_api and rime_api.get_user_data_dir then
    local user_data_dir = rime_api:get_user_data_dir()
    package.path = package.path .. ";" .. user_data_dir .. "/lua/?.lua;" .. user_data_dir .. "/lua/?/init.lua"
end

-- 2. 模块化安全加载子脚本
date_translator = require("date")
number_translator = require("number")
calculator_translator = require("calculator")
help_translator = require("help")
wubi_comment_filter = require("wubi_comment")
