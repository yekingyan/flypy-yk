-- lua/wubi_comment.lua - 候选单字附带五笔86全码提示
-- 数据来自 lua/wubi_table.txt（由 wubi86_ms.dict.yaml 提取：字<TAB>全码<TAB>简码,简码）

local M = {}

-- 码表：字 -> 注释文本
local hints = {}

local function load_table(path)
    local f = io.open(path, "r")
    if not f then
        -- 找不到码表时不静默吞掉：写日志，候选照常输出
        log.error("wubi_comment: 无法打开码表 " .. path)
        return false
    end
    for line in f:lines() do
        local ch, full, shorts = line:match("^([^\t]+)\t([^\t]*)\t?(.*)$")
        if ch and full ~= "" then
            if shorts ~= "" then
                hints[ch] = full .. " (简 " .. shorts:gsub(",", " ") .. ")"
            else
                hints[ch] = full
            end
        end
    end
    f:close()
    return true
end

function M.init(env)
    local dir = rime_api:get_user_data_dir()
    load_table(dir .. "/lua/wubi_table.txt")
end

function M.func(input, env)
    for cand in input:iter() do
        -- 只给单字候选加提示，词组不处理
        if utf8.len(cand.text) == 1 then
            local hint = hints[cand.text]
            if hint then
                cand:get_genuine().comment = hint
            end
        end
        yield(cand)
    end
end

return M
