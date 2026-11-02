-- AI 调用失败时返还额度：日/月计数器同步扣回，下限 0
-- KEYS[1] = quota:{userId}:{planId}:day:{yyyyMMdd}
-- KEYS[2] = quota:{userId}:{planId}:month:{yyyyMM}
-- ARGV[1] = 返还额度
local d = tonumber(redis.call('GET', KEYS[1]) or '0')
local m = tonumber(redis.call('GET', KEYS[2]) or '0')
local c = tonumber(ARGV[1])
local nd = math.max(0, d - c)
local nm = math.max(0, m - c)
redis.call('SET', KEYS[1], nd)
redis.call('SET', KEYS[2], nm)
return 1
