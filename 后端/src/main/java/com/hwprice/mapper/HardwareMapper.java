package com.hwprice.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.hwprice.entity.Hardware;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

public interface HardwareMapper extends BaseMapper<Hardware> {

    /** 按名称/类型/文案关键词搜索硬件类目 */
    @Select("SELECT * FROM t_hardware " +
            "WHERE name LIKE CONCAT('%', #{keyword}, '%') " +
            "   OR type LIKE CONCAT('%', #{keyword}, '%') " +
            "   OR func_desc LIKE CONCAT('%', #{keyword}, '%') " +
            "ORDER BY sort_order, id " +
            "LIMIT 10")
    List<Hardware> search(@Param("keyword") String keyword);
}
