package com.hwprice.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.hwprice.entity.AppConfig;
import com.hwprice.mapper.AppConfigMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

/**
 * AI 网关运行时配置服务：管理员在页面上"输入密钥即可完成"接入。
 *
 * 配置存 t_app_config（键：ai.apiKey / ai.baseUrl / ai.model），
 * 内存缓存 10 秒防每问查库；apiKey 为空时大模型网关自动回落本地 Mock 演示模型。
 * 接口地址与模型名**没有默认值**：填写密钥时必须同步填写 baseUrl 与 model
 * （任意 OpenAI 兼容网关，如 DeepSeek/通义/Kimi 等），否则拒绝保存。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AiConfigService {

    public static final String KEY_API_KEY = "ai.apiKey";
    public static final String KEY_BASE_URL = "ai.baseUrl";
    public static final String KEY_MODEL = "ai.model";

    private final AppConfigMapper appConfigMapper;

    private volatile Snapshot cache;
    private volatile long cacheAt;

    public record Snapshot(String apiKey, String baseUrl, String model) {
    }

    /** 当前生效配置（apiKey 为空 = 未接入云端大模型，使用 Mock 演示模型） */
    public Snapshot current() {
        long now = System.currentTimeMillis();
        Snapshot c = cache;
        if (c != null && now - cacheAt < 10_000) {
            return c;
        }
        Snapshot fresh = load();
        cache = fresh;
        cacheAt = now;
        return fresh;
    }

    /** 管理员保存配置（空字符串视为删除该项）。填密钥时必须同时填地址与模型名。 */
    public void save(String apiKey, String baseUrl, String model) {
        String key = trimToNull(apiKey);
        String url = trimToNull(baseUrl);
        String m = trimToNull(model);
        if (key != null) {
            if (url == null) {
                throw new com.hwprice.common.BizException(
                        com.hwprice.common.ErrorCode.PARAM_ERROR, "请填写接口地址（任意 OpenAI 兼容网关地址）");
            }
            if (m == null) {
                throw new com.hwprice.common.BizException(
                        com.hwprice.common.ErrorCode.PARAM_ERROR, "请填写模型名");
            }
        }
        upsert(KEY_API_KEY, key);
        upsert(KEY_BASE_URL, url);
        upsert(KEY_MODEL, m);
        cache = null; // 立即失效缓存，下个请求即生效
        log.info("AI 网关配置已更新（apiKey {}）", key == null ? "已清空" : "已设置");
    }

    public boolean hasApiKey() {
        String key = current().apiKey();
        return key != null && !key.isBlank();
    }

    /** 只从数据库读取，不做任何默认值兜底（无默认地址） */
    private Snapshot load() {
        return new Snapshot(find(KEY_API_KEY), find(KEY_BASE_URL), find(KEY_MODEL));
    }

    private String find(String key) {
        AppConfig cfg = appConfigMapper.selectOne(new QueryWrapper<AppConfig>().eq("cfg_key", key));
        return cfg == null ? null : trimToNull(cfg.getCfgValue());
    }

    private void upsert(String key, String value) {
        AppConfig cfg = appConfigMapper.selectOne(new QueryWrapper<AppConfig>().eq("cfg_key", key));
        if (value == null) {
            if (cfg != null) {
                appConfigMapper.deleteById(cfg.getId());
            }
            return;
        }
        if (cfg == null) {
            cfg = new AppConfig();
            cfg.setCfgKey(key);
            cfg.setCfgValue(value);
            appConfigMapper.insert(cfg);
        } else {
            cfg.setCfgValue(value);
            appConfigMapper.updateById(cfg);
        }
    }

    private String trimToNull(String v) {
        return v == null || v.isBlank() ? null : v.trim();
    }
}
