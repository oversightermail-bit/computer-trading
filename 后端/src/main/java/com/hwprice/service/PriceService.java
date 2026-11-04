package com.hwprice.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hwprice.common.BizException;
import com.hwprice.common.ErrorCode;
import com.hwprice.config.AppProperties;
import com.hwprice.entity.Hardware;
import com.hwprice.mapper.HardwareMapper;
import com.hwprice.mapper.PriceHistoryMapper;
import com.hwprice.mapper.ProductMapper;
import com.hwprice.vo.HardwareVO;
import com.hwprice.vo.PriceContentVO;
import com.hwprice.vo.PriceRow;
import com.hwprice.vo.PriceSeriesVO;
import com.hwprice.vo.SearchResultVO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

/**
 * 价格服务：价格时序聚合（ECharts 折线数据源）、高性价比推荐、搜索、硬件文案。
 * 热点价格走 Redis 缓存（Redis 不可用时自动直查数据库）。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PriceService {

    /** 折线图时间窗口（天） */
    private static final int SERIES_DAYS = 30;

    private final PriceHistoryMapper priceHistoryMapper;
    private final ProductMapper productMapper;
    private final HardwareMapper hardwareMapper;
    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;
    private final AppProperties properties;

    /** AI 实时价格注入的内存缓存（10 秒，避免每次问答都打库） */
    private final Map<String, OverviewCacheEntry> overviewCache = new ConcurrentHashMap<>();

    /** 首页硬件分类列表（含型号数与近期最低价） */
    public List<HardwareVO> hardwareList() {
        List<Hardware> hardware = hardwareMapper.selectList(null);
        LocalDate since = LocalDate.now().minusDays(3);
        List<PriceRow> rows = priceHistoryMapper.selectRecentRows(since);
        Map<String, List<PriceRow>> byType = rows.stream().collect(Collectors.groupingBy(PriceRow::getHardwareType));

        List<HardwareVO> result = new ArrayList<>();
        for (Hardware h : hardware) {
            HardwareVO vo = new HardwareVO();
            vo.setType(h.getType());
            vo.setName(h.getName());
            vo.setProductCount(productMapper.countByType(h.getType()));
            List<PriceRow> typeRows = byType.getOrDefault(h.getType(), List.of());
            if (!typeRows.isEmpty()) {
                vo.setMinPrice(typeRows.stream().map(PriceRow::getPrice).min(Comparator.naturalOrder()).orElse(null));
            }
            result.add(vo);
        }
        return result;
    }

    /** 关键词搜索：商品/型号 + 硬件类目 */
    public SearchResultVO search(String keyword) {
        SearchResultVO vo = new SearchResultVO();
        vo.setKeyword(keyword);
        vo.setProducts(productMapper.search(keyword));
        vo.setHardware(hardwareMapper.search(keyword).stream()
                .map(h -> new SearchResultVO.HardwareHit(h.getType(), h.getName()))
                .toList());
        return vo;
    }

    /** 硬件文案：功能作用 / 适用场景 / 易踩坑点（价格波动页面 F3） */
    public PriceContentVO content(String type) {
        Hardware h = hardware(type);
        PriceContentVO vo = new PriceContentVO();
        vo.setType(h.getType());
        vo.setName(h.getName());
        vo.setFunc(h.getFuncDesc());
        vo.setScene(h.getScene());
        vo.setPitfall(h.getPitfall());
        return vo;
    }

    /**
     * 价格时序（F3 折线图数据源）：
     * 每个型号一条折线（当日参考价），并给出每型号的性能分与性价比指数。
     */
    public PriceSeriesVO series(String type) {
        Hardware h = hardware(type);
        // 命中 Redis 缓存直接返回
        PriceSeriesVO cached = readCache(type);
        if (cached != null) {
            return cached;
        }
        LocalDate start = LocalDate.now().minusDays(SERIES_DAYS - 1L);
        List<PriceRow> rows = priceHistoryMapper.selectRowsByType(type, start);

        PriceSeriesVO vo = new PriceSeriesVO();
        vo.setType(type);
        vo.setName(h.getName());

        // 按商品分组，保持 id 顺序
        Map<Long, List<PriceRow>> byProduct = rows.stream()
                .collect(Collectors.groupingBy(PriceRow::getProductId, LinkedHashMap::new, Collectors.toList()));
        if (byProduct.isEmpty()) {
            vo.setDates(List.of());
            vo.setSeries(List.of());
            vo.setRecommend(List.of());
            return vo;
        }

        // 横轴：数据中出现的日期
        List<String> dates = rows.stream().map(r -> r.getDate().toString()).distinct().sorted().toList();

        // 型号重名时补规格区分
        Map<String, Long> modelCount = new LinkedHashMap<>();
        for (List<PriceRow> group : byProduct.values()) {
            PriceRow first = group.get(0);
            modelCount.merge(first.getModel(), 1L, Long::sum);
        }

        List<PriceSeriesVO.Series> seriesList = new ArrayList<>();
        List<PriceSeriesVO.Recommend> recommendList = new ArrayList<>();
        for (Map.Entry<Long, List<PriceRow>> entry : byProduct.entrySet()) {
            List<PriceRow> group = entry.getValue();
            PriceRow first = group.get(0);
            String seriesName = modelCount.get(first.getModel()) > 1
                    ? first.getBrand() + " " + first.getModel() + " " + first.getSpec()
                    : first.getBrand() + " " + first.getModel();

            // 日期 -> 当日价格列表
            Map<String, List<BigDecimal>> byDate = new TreeMap<>();
            for (PriceRow row : group) {
                byDate.computeIfAbsent(row.getDate().toString(), k -> new ArrayList<>()).add(row.getPrice());
            }
            List<BigDecimal> data = new ArrayList<>();
            for (String date : dates) {
                List<BigDecimal> dayPrices = byDate.get(date);
                if (dayPrices == null || dayPrices.isEmpty()) {
                    data.add(null); // 缺口用 null，ECharts 折线断开
                } else {
                    data.add(median(dayPrices));
                }
            }
            seriesList.add(new PriceSeriesVO.Series(seriesName, data));
            recommendList.add(buildRecommend(first, group));
        }
        vo.setDates(dates);
        vo.setSeries(seriesList);
        vo.setRecommend(recommendList);

        writeCache(type, vo);
        return vo;
    }

    /** 每型号当日参考价 + 性能分 → 高性价比指数（前端按指数降序展示推荐） */
    private PriceSeriesVO.Recommend buildRecommend(PriceRow first, List<PriceRow> group) {
        // 该型号最新采集日期
        LocalDate latest = group.stream().map(PriceRow::getDate).max(Comparator.naturalOrder()).orElse(null);
        // 最新日期上各来源最低价（数据源为单平台时即该平台参考价）
        Map<String, BigDecimal> platformMin = new LinkedHashMap<>();
        for (PriceRow row : group) {
            if (row.getDate().equals(latest)) {
                platformMin.merge(row.getPlatform(), row.getPrice(), BigDecimal::min);
            }
        }
        List<Map.Entry<String, BigDecimal>> sorted = platformMin.entrySet().stream()
                .sorted(Map.Entry.comparingByValue())
                .toList();
        PriceSeriesVO.Recommend r = new PriceSeriesVO.Recommend();
        r.setBrand(first.getBrand());
        r.setModel(first.getModel());
        r.setSpec(first.getSpec());
        r.setPerf(first.getPerfScore());
        if (!sorted.isEmpty()) {
            Map.Entry<String, BigDecimal> best = sorted.get(0);
            r.setPrice(best.getValue());
        }
        // 性价比指数 = 性能分 ÷ 参考价 × 1000（perf 未维护时为 null，前端不参与排序）
        if (first.getPerfScore() != null && first.getPerfScore() > 0 && r.getPrice() != null
                && r.getPrice().compareTo(BigDecimal.ZERO) > 0) {
            r.setValueIndex(BigDecimal.valueOf(first.getPerfScore())
                    .multiply(BigDecimal.valueOf(1000))
                    .divide(r.getPrice(), 2, RoundingMode.HALF_UP));
        }
        return r;
    }

    /**
     * AI 实时价格注入：近 3 日各硬件类型最低价 TOP3，拼接成提示词上下文。
     * 例：CPU: i5-13490F(中关村在线 ¥1299) | R5 5600(中关村在线 ¥729)；GPU: RTX 4060(中关村在线 ¥2399) ...
     */
    public String recommendOverview() {
        OverviewCacheEntry entry = overviewCache.get("all");
        if (entry != null && System.currentTimeMillis() - entry.timestamp < 10_000) {
            return entry.text;
        }
        LocalDate since = LocalDate.now().minusDays(3);
        List<PriceRow> rows = priceHistoryMapper.selectRecentRows(since);
        Map<String, List<PriceRow>> byType = rows.stream().collect(Collectors.groupingBy(PriceRow::getHardwareType));
        Map<String, String> typeName = hardwareMapper.selectList(null).stream()
                .collect(Collectors.toMap(Hardware::getType, Hardware::getName, (a, b) -> a));

        StringBuilder sb = new StringBuilder();
        for (Map.Entry<String, List<PriceRow>> e : byType.entrySet()) {
            List<PriceRow> top = bestPerProduct(e.getValue()).values().stream()
                    .sorted(Comparator.comparing(PriceRow::getPrice))
                    .limit(3)
                    .toList();
            if (top.isEmpty()) {
                continue;
            }
            String name = typeName.getOrDefault(e.getKey(), e.getKey());
            sb.append(name).append(": ");
            sb.append(top.stream()
                    .map(r -> r.getModel() + "(" + r.getPlatform() + " ¥" + r.getPrice().setScale(0, RoundingMode.HALF_UP) + ")")
                    .collect(Collectors.joining(" | ")));
            sb.append("；");
        }
        String text = sb.toString();
        overviewCache.put("all", new OverviewCacheEntry(text, System.currentTimeMillis()));
        return text;
    }

    /** 供本地演示模型做"硬件对比"：按关键词找型号 */
    public List<SearchResultVO.ProductHit> searchModels(String keyword) {
        return productMapper.search(keyword);
    }

    /** 某硬件类型下近 3 日最低价 TOP-N 型号（装机推荐选品用） */
    public List<SearchResultVO.ProductHit> cheapestByType(String type, int limit) {
        LocalDate since = LocalDate.now().minusDays(3);
        List<PriceRow> rows = priceHistoryMapper.selectRecentRows(since).stream()
                .filter(r -> type.equals(r.getHardwareType()))
                .toList();
        return bestPerProduct(rows).values().stream()
                .sorted(Comparator.comparing(PriceRow::getPrice))
                .limit(limit)
                .map(r -> {
                    SearchResultVO.ProductHit hit = new SearchResultVO.ProductHit();
                    hit.setId(r.getProductId());
                    hit.setBrand(r.getBrand());
                    hit.setModel(r.getModel());
                    hit.setSpec(r.getSpec());
                    hit.setHardwareType(r.getHardwareType());
                    hit.setPlatform(r.getPlatform());
                    hit.setLatestPrice(r.getPrice());
                    return hit;
                })
                .toList();
    }

    /** 每个商品取窗口内最优价格行 */
    private Map<Long, PriceRow> bestPerProduct(List<PriceRow> rows) {
        Map<Long, PriceRow> best = new LinkedHashMap<>();
        for (PriceRow row : rows) {
            PriceRow prev = best.get(row.getProductId());
            if (prev == null || row.getPrice().compareTo(prev.getPrice()) < 0) {
                best.put(row.getProductId(), row);
            }
        }
        return best;
    }

    private Hardware hardware(String type) {
        Hardware h = hardwareMapper.selectOne(new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<Hardware>()
                .eq("type", type).last("LIMIT 1"));
        if (h == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "硬件类型不存在: " + type);
        }
        return h;
    }

    /** 中位价（多平台同日取中位数，消除极端促销价抖动） */
    private BigDecimal median(List<BigDecimal> values) {
        List<BigDecimal> sorted = values.stream().sorted().toList();
        int n = sorted.size();
        if (n % 2 == 1) {
            return sorted.get(n / 2);
        }
        return sorted.get(n / 2 - 1).add(sorted.get(n / 2)).divide(BigDecimal.valueOf(2), 2, RoundingMode.HALF_UP);
    }

    // ---------------- Redis 缓存（失败静默降级直查 DB） ----------------

    private String cacheKey(String type) {
        return "price:series:" + type;
    }

    private PriceSeriesVO readCache(String type) {
        try {
            String json = redisTemplate.opsForValue().get(cacheKey(type));
            if (json != null) {
                return objectMapper.readValue(json, new TypeReference<>() {
                });
            }
        } catch (Exception e) {
            log.debug("读取价格缓存失败，直查数据库: {}", e.getMessage());
        }
        return null;
    }

    private void writeCache(String type, PriceSeriesVO vo) {
        try {
            redisTemplate.opsForValue().set(cacheKey(type),
                    objectMapper.writeValueAsString(vo),
                    properties.getCache().getPriceTtlMinutes(), TimeUnit.MINUTES);
        } catch (Exception e) {
            log.debug("写入价格缓存失败（可忽略）: {}", e.getMessage());
        }
    }

    private record OverviewCacheEntry(String text, long timestamp) {
    }
}
