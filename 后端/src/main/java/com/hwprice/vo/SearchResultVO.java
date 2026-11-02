package com.hwprice.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.List;

/**
 * 搜索响应
 */
@Data
public class SearchResultVO {

    private String keyword;

    /** 匹配的商品/型号 */
    private List<ProductHit> products;

    /** 匹配的硬件类目页 */
    private List<HardwareHit> hardware;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ProductHit {
        private Long id;
        /** 品牌 */
        private String brand;
        /** 型号 */
        private String model;
        /** 规格 */
        private String spec;
        /** 所属硬件类型 */
        private String hardwareType;
        /** 硬件类型名称 */
        private String typeName;
        /** 最新采集价格 */
        private BigDecimal latestPrice;
        /** 最新价格平台 */
        private String platform;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class HardwareHit {
        private String type;
        private String name;
    }
}
