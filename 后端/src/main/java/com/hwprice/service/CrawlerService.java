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
 * 爬虫控制服务（管理页"启动爬虫" / "开启定时抓取"按钮）：
 * <ul>
 *   <li>start()：以后台子进程执行 app.crawler.command（默认 python run.py once --mode real），
 *       只写真实采集价；同一时刻只允许一轮，重复点击返回"正在运行"；</li>
 *   <li>startSchedule()：执行 app.crawler.schedule-command（默认 python run.py schedule --mode real），
 *       常驻调度进程，每日 08/12/18/22 点各抓一轮（服务器长期运行用），
 *       stopSchedule() 可停止该进程；</li>
 *   <li>status()：读取 爬虫/logs/crawl_stats.jsonl 最近一轮统计（成功率/写入数/
 *       沿用上一真实价/暂无数据），并报告单轮子进程与调度进程是否仍在运行。</li>
 * </ul>
 */
@Slf4j
@Service
public class CrawlerService {

    private final AppProperties properties;
    private final ObjectMapper objectMapper;

    private volatile Process running;
    private volatile Process scheduled;

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

    /** 最近一轮统计 + 运行状态（单轮爬虫 + 定时调度进程） */
    public Map<String, Object> status() {
        Map<String, Object> out = new java.util.LinkedHashMap<>();
        boolean alive = running != null && running.isAlive();
        if (!alive) {
            running = null;
        }
        boolean scheduleAlive = scheduled != null && scheduled.isAlive();
        if (!scheduleAlive) {
            scheduled = null;
        }
        out.put("running", alive);
        out.put("scheduleRunning", scheduleAlive);
        out.put("lastRound", lastRound());
        out.put("workDir", crawlerDir().toString());
        return out;
    }

    /**
     * 开启定时抓取：常驻调度进程，每日 08/12/18/22 点各抓一轮（服务器长期运行用）。
     * 与单轮爬虫互不阻塞；后端重启后调度进程随之退出，需在管理页重新开启。
     */
    public synchronized Map<String, Object> startSchedule() {
        if (scheduled != null && scheduled.isAlive()) {
            return Map.of("started", false, "message", "定时抓取已在运行中（每日 08/12/18/22 点）");
        }
        String command = properties.getCrawler().getScheduleCommand();
        List<String> cmd = List.of(command.trim().split("\\s+"));
        Path workDir = crawlerDir();
        Path logFile = workDir.resolve("logs").resolve("admin_schedule.log");
        try {
            Files.createDirectories(logFile.getParent());
            ProcessBuilder pb = new ProcessBuilder(cmd);
            pb.directory(workDir.toFile());
            pb.redirectErrorStream(true);
            pb.redirectOutput(ProcessBuilder.Redirect.appendTo(logFile.toFile()));
            Process process = pb.start();
            scheduled = process;
            log.info("管理页开启定时抓取: {}（工作目录 {}，日志 {}）", command, workDir, logFile);
            return Map.of("started", true,
                    "message", "定时抓取已开启：每日 08:00 / 12:00 / 18:00 / 22:00 自动抓取（服务器常驻，重启后端后需重新开启）",
                    "logFile", logFile.toString());
        } catch (IOException e) {
            log.error("开启定时抓取失败", e);
            return Map.of("started", false, "message", "开启失败：" + e.getMessage());
        }
    }

    /** 停止定时抓取调度进程 */
    public synchronized Map<String, Object> stopSchedule() {
        Process p = scheduled;
        if (p == null || !p.isAlive()) {
            scheduled = null;
            return Map.of("stopped", false, "message", "定时抓取未在运行");
        }
        p.destroy();
        try {
            if (!p.waitFor(3, java.util.concurrent.TimeUnit.SECONDS)) {
                p.destroyForcibly();
                p.waitFor(3, java.util.concurrent.TimeUnit.SECONDS);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            p.destroyForcibly();
        }
        scheduled = null;
        log.info("管理页停止定时抓取");
        return Map.of("stopped", true, "message", "定时抓取已停止");
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
