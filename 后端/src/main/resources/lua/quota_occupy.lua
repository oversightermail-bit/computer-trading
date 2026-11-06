-- 日/月两级 AI 额度原子校验与扣减（任一维度不足则整体不扣）
-- KEYS[1] = quota:{userId}:{planId}:day:{yyyyMMdd}
-- KEYS[2] = quota:{userId}:{planId}:month:{yyyyMM}
-- ARGV[1] = 本次消耗 cost（文本 1 / 图片 2）
-- ARGV[2] = 日额度上限（<=0 表示每日不限，付费方案只限每月）
-- ARGV[3] = 月额度上限
-- ARGV[4] = 日 key 剩余 TTL（秒，到当日结束）
-- ARGV[5] = 月 key 剩余 TTL（秒，到当月结束）
local d = tonumber(redis.call('GET', KEYS[1]) or '0')
local m = tonumber(redis.call('GET', KEYS[2]) or '0')
local c = tonumber(ARGV[1])
local dq = tonumber(ARGV[2])
if (dq <= 0 or d + c <= dq) and m + c <= tonumber(ARGV[3]) then
  redis.call('INCRBY', KEYS[1], c)
  redis.call('INCRBY', KEYS[2], c)
  -- 每次调用按剩余时间刷新 TTL：key 到日/月末自动过期，无需定时任务重置
  redis.call('EXPIRE', KEYS[1], ARGV[4])
  redis.call('EXPIRE', KEYS[2], ARGV[5])
  return 1
end
return 0
