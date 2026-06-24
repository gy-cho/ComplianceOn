package com.kbds.compliance.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration // 2. 스프링이 이 설정을 읽도록 어노테이션 필수!
public class WebConfig implements WebMvcConfigurer {

    // @Value("${cors.allowed-origins}")
    // private List<String> allowedOrigins;

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // [개발환경] C:\Users\KBDS\Documents\images
        // [운영환경] file:/home/kbds/Documents/images/  (운영 반영 시 이 값으로 교체 필요)
        registry.addResourceHandler("/images/**")
                // .addResourceLocations("file:///C:/Users/KBDS/Documents/images/");
                .addResourceLocations("file:/home/kbds/Documents/images/");
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")
            .allowedOrigins("*")   // ← 여기
            // .allowedOrigins(allowedOrigins.toArray(new String[0]))
            .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
            .allowedHeaders("*");
    }
}