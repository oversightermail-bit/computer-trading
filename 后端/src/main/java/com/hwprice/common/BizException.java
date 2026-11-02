package com.hwprice.common;

import lombok.Getter;

/**
 * 业务异常：携带业务错误码，由 {@link GlobalExceptionHandler} 统一收敛为 {@link Result}。
 */
@Getter
public class BizException extends RuntimeException {

    private final int code;

    public BizException(ErrorCode errorCode) {
        super(errorCode.getDefaultMessage());
        this.code = errorCode.getCode();
    }

    public BizException(ErrorCode errorCode, String message) {
        super(message);
        this.code = errorCode.getCode();
    }

    public BizException(int code, String message) {
        super(message);
        this.code = code;
    }
}
