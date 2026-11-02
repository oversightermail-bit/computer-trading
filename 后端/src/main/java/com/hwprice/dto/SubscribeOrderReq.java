package com.hwprice.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

/**
 * 订阅下单请求
 */
@Data
public class SubscribeOrderReq {

    @NotNull(message = "请选择要订阅的套餐")
    private Long planId;
}
