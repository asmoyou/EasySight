-- 修复user_login_logs表中的NULL user_id值
-- 删除user_id为NULL的记录
DELETE FROM user_login_logs WHERE user_id IS NULL;

-- 或者如果需要保留这些记录，可以设置一个默认值
-- UPDATE user_login_logs SET user_id = 0 WHERE user_id IS NULL;