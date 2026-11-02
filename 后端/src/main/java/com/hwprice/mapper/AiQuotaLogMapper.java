package com.hwprice.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hwprice.entity.AiQuotaLog;
import com.hwprice.vo.QuotaLogVO;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

public interface AiQuotaLogMapper extends BaseMapper<AiQuotaLog> {

    /** 额度消耗明细（关联会话，展示提问预览），按时间倒序分页 */
    @Select("SELECT l.id, l.session_id AS sessionId, l.cost, l.quota_type AS quotaType, " +
            "l.create_time AS createTime, s.input AS sessionInput " +
            "FROM t_ai_quota_log l " +
            "LEFT JOIN t_ai_session s ON s.id = l.session_id " +
            "WHERE l.user_id = #{userId} " +
            "ORDER BY l.id DESC")
    IPage<QuotaLogVO> selectLogPage(Page<QuotaLogVO> page, @Param("userId") Long userId);
}
