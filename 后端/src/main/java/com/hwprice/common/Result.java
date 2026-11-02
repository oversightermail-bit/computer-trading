package com.hwprice.common;

import lombok.Data;

/**
 * 统一响应体。
 *
 * <p>契约与前端 Mock 层保持一致：{@code {code, message, data}}，
 * 前端仅依赖 {@code code === 42901}（额度用尽弹升级窗）与 HTTP 401（跳登录页）。</p>
 */
@Data
public class Result<T> {

    /** 0 = 成功；非 0 = 业务错误码（见 {@link ErrorCode}） */
    private int code;

    /** 提示信息（中文，可直接展示） */
    private String message;

    /** 业务数据 */
    private T data;

    public Result() {
    }

    public Result(int code, String message, T data) {
        this.code = code;
        this.message = message;
        this.data = data;
    }

    public static <T> Result<T> ok(T data) {
        return new Result<>(0, "ok", data);
    }

    public static <T> Result<T> ok() {
        return new Result<>(0, "ok", null);
    }

    public static <T> Result<T> fail(int code, String message) {
        return new Result<>(code, message, null);
    }

    public static <T> Result<T> fail(ErrorCode errorCode) {
        return new Result<>(errorCode.getCode(), errorCode.getDefaultMessage(), null);
    }

    public static <T> Result<T> fail(ErrorCode errorCode, String message) {
        return new Result<>(errorCode.getCode(), message, null);
    }

    public static <T> Result<T> fail(ErrorCode errorCode, String message, T data) {
        return new Result<>(errorCode.getCode(), message, data);
    }
}
