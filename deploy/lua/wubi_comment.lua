-- lua/wubi_comment.lua - 候选词提示滤镜 (安全实现)

local function wubi_comment_filter(input, env)
    for cand in input:iter() do
        yield(cand)
    end
end

return wubi_comment_filter
