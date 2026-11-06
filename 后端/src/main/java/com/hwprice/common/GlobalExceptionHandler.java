package com.hwprice.common;

import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.validation.BindException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.resource.NoResourceFoundException;

/**
 * 全局异常处理器：把异常统一收敛为 {@code {code, message, data}} 响应体。
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /** 业务异常 */
    @ExceptionHandler(BizException.class)
    public Result<Void> handleBiz(BizException e, HttpServletResponse response) {
        response.setStatus(httpStatusOf(e.getCode()));
        return Result.fail(e.getCode(), e.getMessage());
    }

    /** @Valid 参数校验异常（JSON body） */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Result<Void> handleValid(MethodArgumentNotValidException e) {
        FieldError fe = e.getBindingResult().getFieldError();
        String msg = fe == null ? ErrorCode.PARAM_ERROR.getDefaultMessage() : fe.getDefaultMessage();
        return Result.fail(ErrorCode.PARAM_ERROR, msg);
    }

    /** 表单绑定参数校验异常 */
    @ExceptionHandler(BindException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Result<Void> handleBind(BindException e) {
        FieldError fe = e.getBindingResult().getFieldError();
        String msg = fe == null ? ErrorCode.PARAM_ERROR.getDefaultMessage() : fe.getDefaultMessage();
        return Result.fail(ErrorCode.PARAM_ERROR, msg);
    }

    /** 认证异常（理论上被 Security EntryPoint 拦截，此处兜底） */
    @ExceptionHandler(AuthenticationException.class)
    @ResponseStatus(HttpStatus.UNAUTHORIZED)
    public Result<Void> handleAuth(AuthenticationException e) {
        return Result.fail(ErrorCode.UNAUTHORIZED);
    }

    /** 越权异常 */
    @ExceptionHandler(AccessDeniedException.class)
    @ResponseStatus(HttpStatus.FORBIDDEN)
    public Result<Void> handleDenied(AccessDeniedException e) {
        return Result.fail(ErrorCode.FORBIDDEN);
    }

    /** 接口不存在 */
    @ExceptionHandler(NoResourceFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public Result<Void> handleNotFound(NoResourceFoundException e) {
        return Result.fail(ErrorCode.NOT_FOUND, "接口不存在");
    }

    /** 兜底异常 */
    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public Result<Void> handleOther(Exception e) {
        log.error("系统异常", e);
        return Result.fail(ErrorCode.SYSTEM_ERROR);
    }

    /** 业务错误码 -> HTTP 状态码 */
    private int httpStatusOf(int code) {
        return switch (code) {
            case 40001 -> HttpStatus.BAD_REQUEST.value();
            case 40101 -> HttpStatus.UNAUTHORIZED.value();
            case 40301 -> HttpStatus.FORBIDDEN.value();
            case 40401 -> HttpStatus.NOT_FOUND.value();
            case 42901, 42902 -> HttpStatus.TOO_MANY_REQUESTS.value();
            default -> code >= 50000 ? HttpStatus.INTERNAL_SERVER_ERROR.value()
                    : HttpStatus.OK.value();
        };
    }
}
