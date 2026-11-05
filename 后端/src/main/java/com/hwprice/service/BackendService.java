package com.hwprice.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 后端服务自身管理（仅根管理员 Controler，见 AdminController.requireRootAdmin）：
 * <ul>
 *   <li>status()：进程 PID / 启动时间 / 运行时长 / Java 版本 / jar 路径；</li>
 *   <li>restart()：以分离子进程执行项目根目录的重启脚本
 *       （Windows：restart-backend.bat；Linux 服务器：restart-backend.sh），
 *       脚本先等待 3 秒（让管理接口把响应发完）再结束旧进程并启动新实例，
 *       因此服务器（Windows / Linux）上同样可用。</li>
 * </ul>
 */
@Slf4j
@Service
public class BackendService {

    /** 进程状态（管理中心"后端服务"卡片） */
    public Map<String, Object> status() {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("pid", ProcessHandle.current().pid());
        out.put("startedAt", ManagementFactory.getRuntimeMXBean().getStartTime());
        out.put("uptimeSeconds", ManagementFactory.getRuntimeMXBean().getUptime() / 1000);
        out.put("javaVersion", System.getProperty("java.version"));
        out.put("os", System.getProperty("os.name"));
        out.put("jarPath", jarPath());
        out.put("projectRoot", projectRoot().toString());
        return out;
    }

    /** 下发重启指令：分离执行重启脚本，脚本会先杀旧进程再拉起新实例 */
    public Map<String, Object> restart() {
        boolean windows = System.getProperty("os.name").toLowerCase().contains("win");
        Path script = projectRoot().resolve(windows ? "restart-backend.bat" : "restart-backend.sh");
        if (!Files.isRegularFile(script)) {
            return Map.of("ok", false, "message", "重启脚本不存在：" + script);
        }
        String pid = String.valueOf(ProcessHandle.current().pid());
        try {
            Path logFile = projectRoot().resolve("后端").resolve("target")
                    .resolve("backend_restart.log");
            Files.createDirectories(logFile.getParent());
            ProcessBuilder pb = windows
                    ? new ProcessBuilder("cmd", "/c", script.toString(), pid)
                    : new ProcessBuilder("/bin/sh", script.toString(), pid);
            pb.directory(projectRoot().toFile());
            pb.redirectErrorStream(true);
            pb.redirectOutput(ProcessBuilder.Redirect.appendTo(logFile.toFile()));
            pb.start();
            log.info("已下发后端重启指令（当前 PID {}，脚本 {}）", pid, script);
            return Map.of("ok", true, "message", "重启指令已下发，约 5~8 秒后服务恢复，页面将自动刷新");
        } catch (IOException e) {
            log.error("下发重启指令失败", e);
            return Map.of("ok", false, "message", "重启失败：" + e.getMessage());
        }
    }

    /** 项目根目录：jar 位于 &lt;root&gt;/后端/target/xxx.jar */
    public Path projectRoot() {
        try {
            String cp = System.getProperty("java.class.path");
            if (cp != null && cp.endsWith(".jar")) {
                Path jar = Path.of(cp).toAbsolutePath();
                Path root = jar.getParent().getParent().getParent(); // target -> 后端 -> root
                if (Files.isDirectory(root.resolve("后端"))) {
                    return root;
                }
            }
        } catch (Exception ignore) {
            // 继续走兜底
        }
        Path fallback = Path.of("D:\\AI电脑购买指导项目");
        return Files.isDirectory(fallback) ? fallback : Path.of(System.getProperty("user.dir"));
    }

    private String jarPath() {
        String cp = System.getProperty("java.class.path");
        if (cp == null) {
            return "";
        }
        return cp.endsWith(".jar") ? cp : "（开发模式，非 jar 启动）";
    }
}
