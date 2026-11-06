package com.hwprice.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.hwprice.common.BizException;
import com.hwprice.common.ErrorCode;
import com.hwprice.entity.AppConfig;
import com.hwprice.mapper.AppConfigMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.stereotype.Service;

/**
 * AI 网关运行时配置服务（免费 / 付费两档**分开管理**）：
 * <ul>
 *   <li>免费账户走免费档配置（键：ai.free.apiKey / ai.free.baseUrl / ai.free.model）；</li>
 *   <li>付费账户走付费档配置（键：ai.paid.apiKey / ai.paid.baseUrl / ai.paid.model）；</li>
 *   <li>两档各自独立：某档 apiKey 为空 = 该档未接入云端大模型，仅该档回落本地 Mock 演示模型；</li>
 *   <li>接口地址与模型名**没有默认值**：填密钥时必须同步填写 baseUrl 与 model，否则拒绝保存；</li>
 *   <li>启动时一次性迁移：旧版单档键（ai.apiKey 等）自动迁移为付费档配置，免费档留空待配。</li>
 * </ul>
 * 配置存 t_app_config，内存缓存 10 秒防每问查库；保存即时生效，无需重启。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AiConfigService implements InitializingBean {

    // 免费档配置键
    public static final String KEY_FREE_API_KEY = "ai.free.apiKey";
    public static final String KEY_FREE_BASE_URL = "ai.free.baseUrl";
    public static final String KEY_FREE_MODEL = "ai.free.model";
    // 付费档配置键
    public static final String KEY_PAID_API_KEY = "ai.paid.apiKey";
    public static final String KEY_PAID_BASE_URL = "ai.paid.baseUrl";
    public static final String KEY_PAID_MODEL = "ai.paid.model";
    // 旧版单档键（仅用于启动时一次性迁移到付费档）
    private static final String KEY_LEGACY_API_KEY = "ai.apiKey";
    private static final String KEY_LEGACY_BASE_URL = "ai.baseUrl";
    private static final String KEY_LEGACY_MODEL = "ai.model";

    private final AppConfigMapper appConfigMapper;

    private volatile Snapshot cacheFree;
    private volatile Snapshot cachePaid;
    private volatile long cacheAt;

    public record Snapshot(String apiKey, String baseUrl, String model) {
    }

    /**
     * 当前生效配置。paid=false 免费档，paid=true 付费档；
     * apiKey 为空 = 该档未接入云端大模型，路由层回落 Mock 演示模型。
     */
    public Snapshot current(boolean paid) {
        long now = System.currentTimeMillis();
        Snapshot c = paid ? cachePaid : cacheFree;
        if (c != null && now - cacheAt < 10_000) {
            return c;
        }
        Snapshot fresh = load(paid);
        if (paid) {
            cachePaid = fresh;
        } else {
            cacheFree = fresh;
        }
        cacheAt = now;
        return fresh;
    }

    public boolean hasApiKey(boolean paid) {
        String key = current(paid).apiKey();
        return key != null && !key.isBlank();
    }

    /**
     * 保存某档配置（空字符串视为清空该档）。填密钥时必须同时填接口地址与模型名。
     *
     * @param paid false=免费档，true=付费档
     */
    public void save(boolean paid, String apiKey, String baseUrl, String model) {
        String key = trimToNull(apiKey);
        String url = trimToNull(baseUrl);
        String m = trimToNull(model);
        if (key != null) {
            if (url == null) {
                throw new BizException(ErrorCode.PARAM_ERROR, "请填写接口地址（任意 OpenAI 兼容网关地址）");
            }
            if (m == null) {
                throw new BizException(ErrorCode.PARAM_ERROR, "请填写模型名");
            }
        }
        String prefix = paid ? "ai.paid" : "ai.free";
        upsert(prefix + ".apiKey", key);
        upsert(prefix + ".baseUrl", url);
        upsert(prefix + ".model", m);
        if (paid) {
            cachePaid = null; // 立即失效缓存，下个请求即生效
        } else {
            cacheFree = null;
        }
        log.info("AI 网关配置已更新（{}档，apiKey {}）",
                paid ? "付费" : "免费", key == null ? "已清空" : "已设置");
    }

    /**
     * 启动时一次性迁移：旧版单档配置（ai.apiKey 等）→ 付费档。
     * 付费档已有密钥则不动旧键；免费档默认未配置（回落本地演示模型），由管理员另行填写。
     */
    @Override
    public synchronized void afterPropertiesSet() {
        try {
            if (find(KEY_PAID_API_KEY) != null || find(KEY_LEGACY_API_KEY) == null) {
                return;
            }
            upsert(KEY_PAID_API_KEY, find(KEY_LEGACY_API_KEY));
            upsert(KEY_PAID_BASE_URL, find(KEY_LEGACY_BASE_URL));
            upsert(KEY_PAID_MODEL, find(KEY_LEGACY_MODEL));
            upsert(KEY_LEGACY_API_KEY, null);
            upsert(KEY_LEGACY_BASE_URL, null);
            upsert(KEY_LEGACY_MODEL, null);
            log.info("旧版单档 AI 网关配置已迁移到付费档（免费档未配置，回落本地演示模型）");
        } catch (Exception e) {
            log.warn("旧版 AI 网关配置迁移跳过：{}", e.getMessage());
        }
    }

    /** 只从数据库读取，不做任何默认值兜底（无默认地址） */
    private Snapshot load(boolean paid) {
        String prefix = paid ? "ai.paid" : "ai.free";
        return new Snapshot(find(prefix + ".apiKey"), find(prefix + ".baseUrl"), find(prefix + ".model"));
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
