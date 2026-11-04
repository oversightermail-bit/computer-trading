package com.hwprice.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.List;

/**
 * 价格时序视图（ECharts 折线图数据源）：
 * dates 为横轴日期，series 为多条折线（图例可显隐），recommend 为各型号高性价比推荐
 * （参考价 + 性能分 + 性价比指数）。
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

    /** 高性价比推荐：每型号参考价 + 性能分 + 性价比指数（前端按指数降序展示） */
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
        /** 今日参考价（数据源：中关村在线参考报价） */
        private BigDecimal price;
        /** 性能分 1-100（人工维护，用于高性价比推荐） */
        private Integer perf;
        /** 性价比指数 = 性能分 ÷ 参考价 × 1000，越大越划算（perf=0 时为 null） */
        private BigDecimal valueIndex;
    }
}
