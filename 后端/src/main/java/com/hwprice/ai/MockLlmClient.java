package com.hwprice.ai;

import com.hwprice.service.PriceService;
import com.hwprice.vo.SearchResultVO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 本地内置演示模型（app.ai.provider=mock）：
 * 无需外网与密钥，基于网站真实价格数据用规则生成"简短大白话"推荐，
 * 用于比赛演示与无 LLM 环境的本地开发调试。
 */
@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "app.ai", name = "provider", havingValue = "mock", matchIfMissing = true)
public class MockLlmClient implements LlmClient {

    private final PriceService priceService;

    @Override
    public String chat(String systemPrompt, String userText, String imageUrl) {
        // 图片问答：演示模式未接入视觉模型
        if (imageUrl != null && !imageUrl.isBlank()) {
            return "（本地演示模式）已收到你的图片。当前后端运行在 Mock 模型下，还没接入多模态视觉识别；"
                    + "接入云端多模态大模型后即可直接识别配置单/硬件照片。"
                    + "现在先把预算和需求用文字发我，我马上结合网站价格给你推荐。";
        }
        // 硬件对比
        if (userText.contains("对比") || userText.contains("比较") || userText.contains("区别")) {
            String compare = tryCompare(userText);
            if (compare != null) {
                return compare;
            }
        }
        // 装机推荐
        return buildConfig(userText);
    }

    /** 从输入里找已知型号，输出多平台最低价对比 */
    private String tryCompare(String text) {
        List<SearchResultVO.ProductHit> hits = priceService.searchModels(text);
        if (hits.isEmpty()) {
            return null;
        }
        StringBuilder sb = new StringBuilder("对比结果（各平台最低价，按最新采集日）：\n");
        int count = 0;
        for (SearchResultVO.ProductHit hit : hits) {
            if (count >= 5) {
                break;
            }
            sb.append("- ").append(hit.getBrand()).append(" ").append(hit.getModel());
            if (hit.getSpec() != null && !hit.getSpec().isBlank()) {
                sb.append(" ").append(hit.getSpec());
            }
            sb.append("：¥").append(price(hit.getLatestPrice()));
            if (hit.getPlatform() != null) {
                sb.append("（").append(hit.getPlatform()).append("）");
            }
            sb.append("\n");
            count++;
        }
        sb.append("建议：预算充足选贵的型号；追求实惠看性价比指数，同价位优先性能分高的型号。");
        return sb.toString();
    }

    /** 按预算与需求生成装机配置推荐（大白话） */
    private String buildConfig(String text) {
        String lower = text.toLowerCase();
        int budget = parseBudget(text);
        boolean gaming = containsAny(text, "游戏", "电竞", "3A", "打游戏", "显卡")
                || containsAny(lower, "game", "gaming");
        boolean office = containsAny(text, "办公", "文档", "家用", "学习", "上网")
                || containsAny(lower, "office", "work", "study");
        boolean creator = containsAny(text, "剪辑", "渲染", "建模", "AI训练", "设计")
                || containsAny(lower, "video edit", "render", "creator");
        boolean withMonitor = containsAny(text, "显示器", "带屏", "带屏幕", "整机含屏", "全套")
                || containsAny(lower, "monitor", "with screen");
        boolean highCpu = creator || containsAny(text, "多开", "虚拟机", "编程", "开发")
                || containsAny(lower, "coding", "virtual", "develop");

        // 预算分配比例
        double cpuShare = gaming ? 0.18 : 0.25;
        double gpuShare = gaming ? 0.30 : (creator ? 0.22 : 0.0);
        double memShare = creator ? 0.12 : 0.08;
        double ssdShare = 0.08;
        double monitorShare = withMonitor ? 0.15 : 0.0;

        StringBuilder sb = new StringBuilder();
        sb.append("预算 ").append(budget).append(" 元").append(gaming ? "，主打游戏" : creator ? "，偏生产力" : "").append("，这样配比较稳：\n");

        pick(sb, "cpu", "CPU", budget, cpuShare, highCpu ? 6 : 4);
        if (gpuShare > 0) {
            pick(sb, "gpu", "显卡", budget, gpuShare, gaming ? 8 : 5);
        }
        pick(sb, "mem_desktop", "内存", budget, memShare, 2);
        pick(sb, "ssd", "固态硬盘", budget, ssdShare, 3);
        if (withMonitor) {
            pick(sb, "monitor", "显示器", budget, monitorShare, 3);
        }
        sb.append(office ? "办公用途集显就够，省下的钱加到内存和固态上更实在。" : "");
        sb.append("避坑提醒：内存买回来先开 XMP，电源别省，主板型号和 CPU 代际要对上。");
        return sb.toString();
    }

    /** 从该硬件类型的低价型号里挑一个预算份额内的，附平台与价格 */
    private void pick(StringBuilder sb, String type, String label, int budget, double share, int limit) {
        List<SearchResultVO.ProductHit> hits = priceService.cheapestByType(type, limit);
        if (hits.isEmpty()) {
            return;
        }
        BigDecimal cap = BigDecimal.valueOf(budget).multiply(BigDecimal.valueOf(share));
        SearchResultVO.ProductHit chosen = null;
        SearchResultVO.ProductHit cheapest = null;
        for (SearchResultVO.ProductHit hit : hits) {
            if (hit.getLatestPrice() == null) {
                continue;
            }
            if (cheapest == null || hit.getLatestPrice().compareTo(cheapest.getLatestPrice()) < 0) {
                cheapest = hit;
            }
            if (hit.getLatestPrice().compareTo(cap) <= 0) {
                chosen = hit;
            }
        }
        if (chosen == null) {
            chosen = cheapest;
        }
        if (chosen == null) {
            return;
        }
        sb.append("- ").append(label).append("：").append(chosen.getBrand()).append(" ").append(chosen.getModel());
        if (chosen.getSpec() != null && !chosen.getSpec().isBlank()) {
            sb.append(" ").append(chosen.getSpec());
        }
        sb.append("（约 ¥").append(price(chosen.getLatestPrice()));
        if (chosen.getPlatform() != null) {
            sb.append("，").append(chosen.getPlatform());
        }
        sb.append("）\n");
    }

    private int parseBudget(String text) {
        // 优先识别 "budget xxx"（英文）或 "预算xxx"（中文）的写法
        Matcher m = Pattern.compile("(?i)budget.{0,8}?(\\d+(?:\\.\\d+)?)\\s*[kK千]?").matcher(text);
        if (m.find()) {
            return toYuan(m.group(1));
        }
        m = Pattern.compile("预算.{0,6}?(\\d+(?:\\.\\d+)?)\\s*[kK千]?").matcher(text);
        if (m.find()) {
            return toYuan(m.group(1));
        }
        // 其次找"数字+万"或"数字k"
        m = Pattern.compile("(\\d+(?:\\.\\d+)?)\\s*万").matcher(text);
        if (m.find()) {
            return (int) (Double.parseDouble(m.group(1)) * 10000);
        }
        m = Pattern.compile("(\\d+(?:\\.\\d+)?)\\s*[kK]").matcher(text);
        if (m.find()) {
            return (int) (Double.parseDouble(m.group(1)) * 1000);
        }
        return 5000; // 默认预算
    }

    private int toYuan(String value) {
        try {
            if (value.endsWith("k") || value.endsWith("K")) {
                return (int) (Double.parseDouble(value.substring(0, value.length() - 1)) * 1000);
            }
            double d = Double.parseDouble(value);
            if (d < 100) {
                return (int) (d * 1000); // "预算5k"已处理；"预算0.5"视为 0.5 万
            }
            return (int) d;
        } catch (NumberFormatException e) {
            return 5000;
        }
    }

    private String price(BigDecimal value) {
        return value.setScale(0, RoundingMode.HALF_UP).toPlainString();
    }

    private boolean containsAny(String text, String... keywords) {
        for (String kw : keywords) {
            if (text.contains(kw)) {
                return true;
            }
        }
        return false;
    }
}
