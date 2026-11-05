package com.hwprice.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.hwprice.entity.Product;
import com.hwprice.vo.SearchResultVO;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

public interface ProductMapper extends BaseMapper<Product> {

    /** 按关键词搜索商品/型号（含最新真实采集价与平台，只读 source='real'） */
    @Select("SELECT p.id, p.brand, p.model, p.spec, p.hardware_type AS hardwareType, h.name AS typeName, " +
            "(SELECT ph.price FROM t_price_history ph WHERE ph.product_id = p.id AND ph.source = 'real' " +
            "  ORDER BY ph.date DESC, ph.price ASC LIMIT 1) AS latestPrice, " +
            "(SELECT ph.platform FROM t_price_history ph WHERE ph.product_id = p.id AND ph.source = 'real' " +
            "  ORDER BY ph.date DESC, ph.price ASC LIMIT 1) AS platform " +
            "FROM t_product p " +
            "LEFT JOIN t_hardware h ON h.type = p.hardware_type " +
            "WHERE p.brand LIKE CONCAT('%', #{keyword}, '%') " +
            "   OR p.model LIKE CONCAT('%', #{keyword}, '%') " +
            "   OR p.spec LIKE CONCAT('%', #{keyword}, '%') " +
            "ORDER BY p.id " +
            "LIMIT 20")
    List<SearchResultVO.ProductHit> search(@Param("keyword") String keyword);

    /** 某类型下的商品数量 */
    @Select("SELECT COUNT(*) FROM t_product WHERE hardware_type = #{type}")
    long countByType(@Param("type") String type);
}
