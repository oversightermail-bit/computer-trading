package com.hwprice.controller;

import com.hwprice.common.Result;
import com.hwprice.service.PriceService;
import com.hwprice.vo.HardwareVO;
import com.hwprice.vo.PriceContentVO;
import com.hwprice.vo.PriceSeriesVO;
import com.hwprice.vo.SearchResultVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 价格浏览接口（游客开放）：首页硬件列表、搜索、价格时序、硬件文案（F2 / F3）
 */
@Tag(name = "价格浏览", description = "游客可访问的硬件与价格接口")
@RestController
@RequestMapping("/api/public")
@RequiredArgsConstructor
public class PriceController {

    private final PriceService priceService;

    @Operation(summary = "首页硬件分类列表")
    @GetMapping("/hardware")
    public Result<List<HardwareVO>> hardware() {
        return Result.ok(priceService.hardwareList());
    }

    @Operation(summary = "关键词搜索", description = "按品牌/型号/规格/硬件类目搜索")
    @GetMapping("/search")
    public Result<SearchResultVO> search(@RequestParam("keyword") String keyword) {
        return Result.ok(priceService.search(keyword));
    }

    @Operation(summary = "价格时序（折线图数据源）", description = "type 如 cpu/gpu/keyboard；返回多型号多平台中位价时序与推荐购买平台")
    @GetMapping("/price/series")
    public Result<PriceSeriesVO> series(@RequestParam("type") String type) {
        return Result.ok(priceService.series(type));
    }

    @Operation(summary = "硬件文案", description = "价格波动页面的功能作用/适用场景/易踩坑点")
    @GetMapping("/price/content")
    public Result<PriceContentVO> content(@RequestParam("type") String type) {
        return Result.ok(priceService.content(type));
    }
}
