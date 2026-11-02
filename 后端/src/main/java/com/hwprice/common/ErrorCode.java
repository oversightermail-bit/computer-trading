package com.hwprice.common;

import lombok.Getter;

/**
 * 业务错误码。HTTP 状态码由 {@link GlobalExceptionHandler} 按错误码映射。
 */
@Getter
public enum ErrorCode {

    /** 参数校验失败 -> HTTP 400 */
    PARAM_ERROR(40001, "参数不正确"),

    /** 未登录 / token 无效或过期 -> HTTP 401 */
    UNAUTHORIZED(40101, "未登录或登录已过期"),

    /** 越权 / 套餐能力不足 -> HTTP 403 */
    FORBIDDEN(40301, "没有权限执行该操作"),

    /** 资源不存在 -> HTTP 404 */
    NOT_FOUND(40401, "资源不存在"),

    /** AI 额度用尽 -> HTTP 429（前端据此弹出订阅升级弹窗） */
    QUOTA_EXCEEDED(42901, "AI额度已用完，升级订阅可解锁更多次数"),

    /** AI 上游调用失败（额度已返还） -> HTTP 502 */
    AI_UPSTREAM_FAIL(50201, "AI 服务暂时不可用，本次额度已返还，请稍后再试"),

    /** 系统内部错误 -> HTTP 500 */
    SYSTEM_ERROR(50000, "系统繁忙，请稍后再试");

    private final int code;
    private final String defaultMessage;

    ErrorCode(int code, String defaultMessage) {
        this.code = code;
        this.defaultMessage = defaultMessage;
    }
}
