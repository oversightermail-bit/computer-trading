package com.hwprice.service;

import com.hwprice.ai.LlmClient;
import com.hwprice.common.BizException;
import com.hwprice.common.ErrorCode;
import com.hwprice.config.AppProperties;
import com.hwprice.dto.AiChatReq;
import com.hwprice.entity.AiSession;
import com.hwprice.mapper.AiSessionMapper;
import com.hwprice.quota.QuotaContext;
import com.hwprice.vo.AiChatVO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

/**
 * AI 问答服务（F4）：
 * <ul>
 *   <li>系统提示词强制"简单、浓缩的大白话"作答，并注入网站实时价格数据；</li>
 *   <li>调用前额度已由 QuotaInterceptor 扣减；调用失败/超时返还额度（先扣减、后调用、失败返还）；</li>
 *   <li>回答经压缩模板处理，杜绝长篇大论。</li>
 * </ul>
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AiService {

    /** 系统提示词模板：简短大白话 + 实时价格 */
    private static final String SYSTEM_PROMPT_TEMPLATE =
            "你是装机顾问。用简短的大白话回答，禁止长篇大论，多用短句和列表，每次不超过 300 字。" +
            "结合以下网站实时价格数据给出推荐（价格已含平台信息，优先推荐最低价平台）：\n%s";

    private final LlmClient llmClient;
    private final PriceService priceService;
    private final QuotaService quotaService;
    private final SubscriptionService subscriptionService;
    private final AiSessionMapper aiSessionMapper;
    private final AppProperties properties;

    /**
     * AI 问答主流程。cost 由 QuotaInterceptor 预先扣减并传入。
     *
     * @param userId 当前登录用户
     * @param req    提问内容（文本 / 图片）
     * @param cost   本次成本（1 或 2）
     */
    public AiChatVO chat(Long userId, AiChatReq req, int cost) {
        QuotaContext ctx = subscriptionService.current(userId);
        Long sessionId = null;
        try {
            String priceContext = priceService.recommendOverview();
            if (priceContext.isBlank()) {
                priceContext = "（价格数据暂未采集，请先运行爬虫子系统）";
            }
            String systemPrompt = String.format(SYSTEM_PROMPT_TEMPLATE, priceContext);
            String rawAnswer = llmClient.chat(systemPrompt, req.getContent(), blankToNull(req.getImageUrl()));
            String answer = compress(rawAnswer);

            // 会话落库
            AiSession session = new AiSession();
            session.setUserId(userId);
            session.setInput(req.getContent());
            session.setImageUrl(blankToNull(req.getImageUrl()));
            session.setAnswer(answer);
            session.setCost(cost);
            session.setCreateTime(LocalDateTime.now());
            aiSessionMapper.insert(session);
            sessionId = session.getId();

            // 消耗流水异步落库
            quotaService.recordCharge(userId, sessionId, cost);

            long[] used = quotaService.used(ctx);
            AiChatVO vo = new AiChatVO();
            vo.setAnswer(answer);
            vo.setCost(cost);
            vo.setSessionId(sessionId);
            vo.setDayRemain(Math.max(ctx.getQuotaDay() - used[0], 0));
            vo.setMonthRemain(Math.max(ctx.getQuotaMonth() - used[1], 0));
            return vo;
        } catch (BizException e) {
            // 业务异常（如额度不足）不返还，直接上抛
            throw e;
        } catch (Exception e) {
            // 大模型超时/失败：返还已扣额度，返回友好提示
            log.error("AI 调用失败，返还额度 userId={}, cost={}", userId, cost, e);
            quotaService.refund(ctx, cost);
            if (sessionId != null) {
                quotaService.recordRefund(userId, sessionId, cost);
            }
            throw new BizException(ErrorCode.AI_UPSTREAM_FAIL);
        }
    }

    /** 压缩 + 大白话化：折叠空白、按句子边界截断到配置的最大字符数 */
    String compress(String text) {
        if (text == null) {
            return "";
        }
        String cleaned = text.replaceAll("\\s+", " ").trim();
        int max = properties.getAi().getCompressMaxChars();
        if (cleaned.length() <= max) {
            return cleaned;
        }
        String cut = cleaned.substring(0, max);
        // 尽量切在句末
        int lastSentenceEnd = Math.max(
                Math.max(cut.lastIndexOf('。'), cut.lastIndexOf('！')),
                Math.max(cut.lastIndexOf('？'), cut.lastIndexOf('\n')));
        if (lastSentenceEnd > max / 2) {
            cut = cut.substring(0, lastSentenceEnd + 1);
        }
        return cut + "……";
    }

    private String blankToNull(String value) {
        return value == null || value.isBlank() ? null : value;
    }
}
