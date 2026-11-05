package com.hwprice.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.hwprice.entity.PriceHistory;
import com.hwprice.vo.PriceRow;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDate;
import java.util.List;

public interface PriceHistoryMapper extends BaseMapper<PriceHistory> {

    /** 某硬件类型在时间窗口内的全部真实采集价格行（联商品表，只读 source='real'） */
    @Select("SELECT p.id AS productId, p.hardware_type AS hardwareType, p.brand, p.model, p.spec, " +
            "p.perf_score AS perfScore, p.perf_basis AS perfBasis, p.perf_updated AS perfUpdated, " +
            "ph.platform, ph.price, ph.date " +
            "FROM t_price_history ph " +
            "JOIN t_product p ON p.id = ph.product_id " +
            "WHERE p.hardware_type = #{type} AND ph.date >= #{start} AND ph.source = 'real' " +
            "ORDER BY ph.date, p.id, ph.platform")
    List<PriceRow> selectRowsByType(@Param("type") String type, @Param("start") LocalDate start);

    /** 各硬件类型近几日真实采集价格行（首页参考价 / AI 实时价格注入，只读 source='real'） */
    @Select("SELECT p.id AS productId, p.hardware_type AS hardwareType, p.brand, p.model, p.spec, " +
            "p.perf_score AS perfScore, p.perf_basis AS perfBasis, p.perf_updated AS perfUpdated, " +
            "ph.platform, ph.price, ph.date " +
            "FROM t_price_history ph " +
            "JOIN t_product p ON p.id = ph.product_id " +
            "WHERE ph.date >= #{since} AND ph.source = 'real' " +
            "ORDER BY p.hardware_type, p.id, ph.date")
    List<PriceRow> selectRecentRows(@Param("since") LocalDate since);
}
