package com.hwprice;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

/**
 * 硬件价格比价与智能推荐网站 - 后端服务入口
 *
 * <p>技术栈：Spring Boot 3 + Spring Security(JWT) + MyBatis-Plus(MySQL) + Redis</p>
 * <p>启动后访问 Swagger UI：http://localhost:8080/swagger-ui/index.html</p>
 */
@SpringBootApplication
@MapperScan("com.hwprice.mapper")
@ConfigurationPropertiesScan("com.hwprice.config")
public class HwPriceApplication {

    public static void main(String[] args) {
        SpringApplication.run(HwPriceApplication.class, args);
    }
}
