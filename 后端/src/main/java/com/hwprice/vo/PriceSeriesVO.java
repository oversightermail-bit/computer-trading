package com.hwprice.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.List;

/**
 * 价格时序视图（ECharts 折线图数据源）：
 * dates 为横轴日期，series 为多条折线（图例可显隐），recommend 为各型号推荐购买平台。
 */
@Data
public class PriceSeriesVO {

    /** 硬件类型编码 */
    private String type;

    /** 硬件名称 */
    private String name;

    /** 横轴日期 yyyy-MM-dd */
    private List<String> dates;

    /** 折线序列：每个型号一条（多平台取当日中位价） */
    private List<Series> series;

    /** 推荐购买平台：每型号取当日最低价平台 */
    private List<Recommend> recommend;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Series {
        /** 图例名：品牌 + 型号（+规格） */
        private String name;
        private List<BigDecimal> data;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Recommend {
        /** 品牌 */
        private String brand;
        /** 型号 */
        private String model;
        /** 规格 */
        private String spec;
        /** 推荐平台（当日最低价） */
        private String platform;
        /** 推荐平台价格 */
        private BigDecimal price;
        /** 次低价平台 */
        private String secondPlatform;
        /** 次低价 */
        private BigDecimal secondPrice;
        /** 与次低价差额 */
        private BigDecimal diff;
    }
}
