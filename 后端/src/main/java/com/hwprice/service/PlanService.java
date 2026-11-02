package com.hwprice.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.hwprice.common.BizException;
import com.hwprice.common.ErrorCode;
import com.hwprice.entity.SubscriptionPlan;
import com.hwprice.mapper.SubscriptionPlanMapper;
import com.hwprice.vo.PlanVO;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 订阅套餐服务：套餐数据存于 t_subscription_plan，
 * 名称/定价/额度/多模态开关均可后台调整、即时生效，无需发版。
 */
@Service
@RequiredArgsConstructor
public class PlanService {

    private final SubscriptionPlanMapper planMapper;

    /** 上架中的全部套餐（按排序展示） */
    public List<PlanVO> listActive() {
        QueryWrapper<SubscriptionPlan> wrapper = new QueryWrapper<SubscriptionPlan>()
                .eq("status", 1)
                .orderByAsc("sort_order", "id");
        return planMapper.selectList(wrapper).stream().map(this::toVO).toList();
    }

    /** 免费套餐（注册默认等级） */
    public SubscriptionPlan freePlan() {
        SubscriptionPlan plan = planMapper.selectFreePlan();
        if (plan == null) {
            throw new BizException(ErrorCode.SYSTEM_ERROR, "套餐数据缺失：请先执行 sql/subscription_schema.sql 初始化免费套餐");
        }
        return plan;
    }

    /** 按 id 取上架套餐 */
    public SubscriptionPlan getActive(Long planId) {
        SubscriptionPlan plan = planMapper.selectActiveById(planId);
        if (plan == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "套餐不存在或已下架");
        }
        return plan;
    }

    /** 可升级套餐：比当前套餐等级更高的上架套餐（429 弹窗数据源） */
    public List<PlanVO> upgradable(SubscriptionPlan currentPlan) {
        QueryWrapper<SubscriptionPlan> wrapper = new QueryWrapper<SubscriptionPlan>()
                .eq("status", 1)
                .gt("sort_order", currentPlan.getSortOrder() == null ? 0 : currentPlan.getSortOrder())
                .orderByAsc("sort_order", "id");
        return planMapper.selectList(wrapper).stream().map(this::toVO).toList();
    }

    private PlanVO toVO(SubscriptionPlan plan) {
        PlanVO vo = new PlanVO();
        vo.setId(plan.getId());
        vo.setPlanName(plan.getPlanName());
        vo.setPriceMonth(plan.getPriceMonth());
        vo.setQuotaDay(plan.getQuotaDay());
        vo.setQuotaMonth(plan.getQuotaMonth());
        vo.setMultimodal(plan.getMultimodal() != null && plan.getMultimodal() == 1);
        vo.setDescription(plan.getDescription());
        return vo;
    }
}
