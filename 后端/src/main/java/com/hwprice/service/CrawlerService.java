package com.hwprice.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hwprice.config.AppProperties;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

/**
 * 爬虫控制服务（管理页"启动爬虫"按钮）：
 * <ul>
 *   <li>start()：以后台子进程执行 app.crawler.command（默认 python run.py once --mode real），
 *       只写真实采集价；同一时刻只允许一轮，重复点击返回"正在运行"；</li>
 *   <li>status()：读取 爬虫/logs/crawl_stats.jsonl 最近一轮统计（成功率/写入数/
 *       沿用上一真实价/暂无数据），并报告子进程是否仍在运行。</li>
 * </ul>
 */
@Slf4j
@Service
public class CrawlerService {

    private final AppProperties properties;
    private final ObjectMapper objectMapper;

    private volatile Process running;

    public CrawlerService(AppProperties properties, ObjectMapper objectMapper) {
        this.properties = properties;
        this.objectMapper = objectMapper;
    }

    /** 解析爬虫工作目录（相对路径按后端进程目录解析，找不到时回退项目标准路径） */
    public Path crawlerDir() {
        String configured = properties.getCrawler().getWorkDir();
        Path p = Path.of(configured);
        if (!p.isAbsolute()) {
            p = Path.of(System.getProperty("user.dir")).resolve(configured);
        }
        if (!Files.isDirectory(p)) {
            Path fallback = Path.of("D:\\AI电脑购买指导项目\\爬虫");
            if (Files.isDirectory(fallback)) {
                return fallback;
            }
        }
        return p;
    }

    public synchronized Map<String, Object> start() {
        boolean alive = running != null && running.isAlive();
        if (alive) {
            return Map.of("started", false, "message", "爬虫已在运行中，请等待本轮完成");
        }
        String command = properties.getCrawler().getCommand();
        List<String> cmd = List.of(command.trim().split("\\s+"));
        Path workDir = crawlerDir();
        Path logFile = workDir.resolve("logs").resolve("admin_crawl.log");
        try {
            Files.createDirectories(logFile.getParent());
            ProcessBuilder pb = new ProcessBuilder(cmd);
            pb.directory(workDir.toFile());
            pb.redirectErrorStream(true);
            pb.redirectOutput(ProcessBuilder.Redirect.appendTo(logFile.toFile()));
            Process process = pb.start();
            running = process;
            log.info("管理页启动爬虫: {}（工作目录 {}，日志 {}）", command, workDir, logFile);
            return Map.of("started", true,
                    "message", "爬虫已启动（" + String.join(" ", cmd) + "），预计 3~5 分钟完成",
                    "logFile", logFile.toString());
        } catch (IOException e) {
            log.error("启动爬虫失败", e);
            return Map.of("started", false, "message", "启动失败：" + e.getMessage());
        }
    }

    /** 最近一轮统计 + 运行状态 */
    public Map<String, Object> status() {
        Map<String, Object> out = new java.util.LinkedHashMap<>();
        boolean alive = running != null && running.isAlive();
        if (!alive) {
            running = null;
        }
        out.put("running", alive);
        out.put("lastRound", lastRound());
        out.put("workDir", crawlerDir().toString());
        return out;
    }

    private Map<String, Object> lastRound() {
        Path stats = crawlerDir().resolve("logs").resolve("crawl_stats.jsonl");
        if (!Files.isRegularFile(stats)) {
            return Map.of("time", "暂无抓取统计");
        }
        try {
            List<String> lines = Files.readAllLines(stats, StandardCharsets.UTF_8);
            if (lines.isEmpty()) {
                return Map.of("time", "暂无抓取统计");
            }
            String last = lines.get(lines.size() - 1);
            @SuppressWarnings("unchecked")
            Map<String, Object> rec = objectMapper.readValue(last, Map.class);
            // 统计文件里没有的补充字段容错
            rec.putIfAbsent("carry_over", 0);
            rec.putIfAbsent("no_data", 0);
            return rec;
        } catch (Exception e) {
            log.warn("读取爬虫统计失败: {}", e.getMessage());
            return Map.of("time", "统计读取失败：" + e.getMessage());
        }
    }
}
