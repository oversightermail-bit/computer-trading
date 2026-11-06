package com.hwprice.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hwprice.common.BizException;
import com.hwprice.common.ErrorCode;
import com.hwprice.config.AppProperties;
import com.hwprice.entity.PayOrder;
import com.hwprice.entity.SubscriptionPlan;
import com.hwprice.entity.User;
import com.hwprice.mapper.PayOrderMapper;
import com.hwprice.mapper.UserMapper;
import com.hwprice.pay.PaymentChannel;
import com.hwprice.vo.PayOrderVO;
import com.hwprice.vo.SubscriptionVO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.ThreadLocalRandom;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * 订阅支付模块（模拟支付 + 可切换真实接口）：
 * <ul>
 *   <li>下单 createOrder：创建 t_pay_order 待支付单，按 app.subscribe.payment.channel
 *       选择通道生成支付参数（mock 返回模拟收款码；alipay/wechat 未接入时返回"功能开发中"）；</li>
 *   <li>模拟支付确认 confirmMockPay：比赛演示用（demo 演示账号 / 根管理员），
 *       标记已支付并激活套餐；</li>
 *   <li>支付回调 handleNotify：支付网关异步通知入口（游客通道），真实接口接入后
 *       在此验签 + 标记已支付 + 激活套餐，流程与 mock 保持一致。</li>
 * </ul>
 * 切换真实支付：application-subscription.yml 中 payment.channel 改为 alipay/wechat，
 * 填写对应参数并实现通道类中的 TODO 即可，前端与其余流程无需改动。
 */
@Slf4j
@Service
public class PaymentService {

    private final PayOrderMapper payOrderMapper;
    private final PlanService planService;
    private final SubscriptionService subscriptionService;
    private final AppProperties properties;
    private final ObjectMapper objectMapper;
    private final UserMapper userMapper;
    private final Map<String, PaymentChannel> channels;

    public PaymentService(PayOrderMapper payOrderMapper,
                          PlanService planService,
                          SubscriptionService subscriptionService,
                          AppProperties properties,
                          ObjectMapper objectMapper,
                          UserMapper userMapper,
                          List<PaymentChannel> channelList) {
        this.payOrderMapper = payOrderMapper;
        this.planService = planService;
        this.subscriptionService = subscriptionService;
        this.properties = properties;
        this.objectMapper = objectMapper;
        this.userMapper = userMapper;
        this.channels = channelList.stream()
                .collect(Collectors.toMap(PaymentChannel::name, Function.identity()));
    }

    /** 模拟支付仅演示账号 demo 与根管理员 Controler 可用（真实账户走线上支付，未接入前"功能开发中"） */
    private boolean mockPayAllowed(Long userId) {
        if (userId == null) {
            return false;
        }
        User user = userMapper.selectById(userId);
        return user != null && ("demo".equals(user.getUsername()) || UserService.ROOT_ADMIN.equals(user.getUsername()));
    }

    /** 下单：创建支付单并生成支付参数（未支付时对同一套餐幂等复用） */
    public PayOrderVO createOrder(Long userId, Long planId) {
        SubscriptionPlan plan = planService.getActive(planId);

        PayOrder existing = payOrderMapper.selectOne(new QueryWrapper<PayOrder>()
                .eq("user_id", userId)
                .eq("plan_id", planId)
                .eq("status", 0)
                .orderByDesc("id")
                .last("LIMIT 1"));
        if (existing != null) {
            return toVO(existing);
        }

        String channelName = properties.getSubscribe().getPayment().getChannel();
        PaymentChannel channel = channels.get(channelName);
        if (channel == null) {
            throw new BizException(ErrorCode.SYSTEM_ERROR, "支付通道配置错误：" + channelName);
        }

        PayOrder order = new PayOrder();
        order.setOrderNo("P" + DateTimeFormatter.ofPattern("yyyyMMddHHmmss").format(LocalDateTime.now())
                + String.format("%06d", ThreadLocalRandom.current().nextInt(1_000_000)));
        order.setUserId(userId);
        order.setPlanId(plan.getId());
        order.setPlanName(plan.getPlanName());
        order.setAmount(plan.getPriceMonth());
        order.setChannel(channelName);
        order.setStatus(0);
        order.setCreateTime(LocalDateTime.now());
        order.setPayParams(channel.createPay(order));
        payOrderMapper.insert(order);
        log.info("创建订阅支付单 {}：用户 {} 套餐 [{}] 金额 {} 渠道 {}",
                order.getOrderNo(), userId, plan.getPlanName(), plan.getPriceMonth(), channelName);
        return toVO(order);
    }

    /** 模拟支付确认（比赛演示；demo 演示账号 / 根管理员走此流程） */
    @Transactional(rollbackFor = Exception.class)
    public SubscriptionVO confirmMockPay(Long userId, String orderNo) {
        PayOrder order = findByOrderNo(orderNo);
        if (order == null || !Objects.equals(order.getUserId(), userId)) {
            throw new BizException(ErrorCode.NOT_FOUND, "支付单不存在");
        }
        if (!"mock".equals(order.getChannel())) {
            throw new BizException(ErrorCode.PARAM_ERROR, "该订单使用真实支付渠道，不能走模拟支付确认");
        }
        if (!mockPayAllowed(userId)) {
            throw new BizException(ErrorCode.FORBIDDEN,
                    "真实账户请使用线上支付：支付功能开发中，目前暂不支持");
        }
        if (order.getStatus() != null && order.getStatus() == 1) {
            return subscriptionService.me(userId); // 幂等：已支付直接返回当前订阅
        }
        order.setStatus(1);
        order.setPayTime(LocalDateTime.now());
        payOrderMapper.updateById(order);
        log.info("模拟支付成功 {}：用户 {} 套餐 [{}]", orderNo, userId, order.getPlanName());
        return subscriptionService.subscribe(userId, order.getPlanId());
    }

    /**
     * 支付异步通知（游客通道，支付网关无 JWT）：
     * mock 渠道兼容 JSON 通知（orderNo）；真实渠道接入后在此解析网关参数并验签。
     *
     * @return 网关要求的应答文本（"success"）
     */
    @Transactional(rollbackFor = Exception.class)
    public String handleNotify(String rawBody) {
        if (rawBody == null || rawBody.isBlank()) {
            throw new BizException(ErrorCode.PARAM_ERROR, "支付回调参数为空");
        }
        PayOrder order;
        try {
            JsonNode node = objectMapper.readTree(rawBody);
            order = findByOrderNo(node.path("orderNo").asText(""));
        } catch (Exception e) {
            throw new BizException(ErrorCode.PARAM_ERROR, "支付回调格式错误");
        }
        if (order == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "支付单不存在");
        }
        if (order.getStatus() != null && order.getStatus() == 1) {
            return "success"; // 幂等应答
        }
        if ("mock".equals(order.getChannel())) {
            // 模拟渠道：仅演示账号/根管理员可支付；标记支付成功并激活
            if (!mockPayAllowed(order.getUserId())) {
                throw new BizException(ErrorCode.FORBIDDEN,
                        "真实账户请使用线上支付：支付功能开发中，目前暂不支持");
            }
            order.setStatus(1);
            order.setPayTime(LocalDateTime.now());
            payOrderMapper.updateById(order);
            subscriptionService.subscribe(order.getUserId(), order.getPlanId());
            log.info("支付回调（mock）激活订阅 {}：用户 {} 套餐 [{}]", order.getOrderNo(), order.getUserId(), order.getPlanName());
            return "success";
        }
        // TODO 真实渠道：解析网关参数 → PaymentChannel.verifyNotify 验签 → 通过后执行与上面一致的激活流程
        throw new BizException(ErrorCode.SYSTEM_ERROR,
                "真实支付渠道未接入：营业执照办理后启用验签与回调激活流程");
    }

    private PayOrder findByOrderNo(String orderNo) {
        if (orderNo == null || orderNo.isBlank()) {
            return null;
        }
        return payOrderMapper.selectOne(new QueryWrapper<PayOrder>().eq("order_no", orderNo));
    }

    private PayOrderVO toVO(PayOrder o) {
        PayOrderVO vo = new PayOrderVO();
        vo.setOrderNo(o.getOrderNo());
        vo.setChannel(o.getChannel());
        vo.setMock("mock".equals(o.getChannel()));
        vo.setQrContent(o.getPayParams());
        vo.setPayUrl(null);
        vo.setAmount(o.getAmount());
        vo.setPlanName(o.getPlanName());
        vo.setStatus(o.getStatus());
        vo.setMessage("mock".equals(o.getChannel())
                ? "模拟支付：请确认支付后完成开通" : "等待支付");
        return vo;
    }
}
