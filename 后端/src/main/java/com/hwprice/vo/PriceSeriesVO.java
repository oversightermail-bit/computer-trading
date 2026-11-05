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
        /** 参考价（最新真实采集日各来源最低价；无真实价时为 null，前端显示"暂无数据"） */
        private BigDecimal price;
        /** 参考价对应的真实采集日期（沿用上一真实价时即上一采集日） */
        private java.time.LocalDate priceDate;
        /** 性能分 1-100（基准自动映射，PassMark/3DMark/官方规格） */
        private Integer perf;
        /** 性能分依据（基准数值与公式），悬浮提示用 */
        private String perfBasis;
        /**
         * 性价比指数 = 性能分 ÷ ln(参考价) × 100（对数归一化，抑制"越便宜分越高"偏差）。
         * 无真实价或性能分未维护时为 null，前端不参与排序。
         */
        private BigDecimal valueIndex;
    }
}
