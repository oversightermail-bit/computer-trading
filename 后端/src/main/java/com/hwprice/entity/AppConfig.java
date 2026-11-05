package com.hwprice.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 应用配置表 t_app_config（管理员维护：AI API 密钥等）
 */
@Data
@TableName("t_app_config")
public class AppConfig {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 配置键，如 ai.apiKey / ai.baseUrl / ai.model */
    private String cfgKey;

    /** 配置值 */
    private String cfgValue;

    private LocalDateTime updateTime;
}
