package com.kylelab.sseagent.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class JacksonConfig {

    @Bean
    public ObjectMapper objectMapper() {
        ObjectMapper objectMapper = new ObjectMapper();

        // 날짜/시간(LocalDateTime 등)을 직렬화/역직렬화하기 위한 모듈 등록 (필수)
        objectMapper.registerModule(new JavaTimeModule());

        return objectMapper;
    }
}