package com.kylelab.sseagent.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
public class RestClientConfig {

    // application.yml에 등록했던 주소를 가져옵니다.
    @Value("${ai.agent.url:http://localhost:8000/api/chat}")
    private String aiAgentUrl;

    @Bean
    public RestClient aiAgentRestClient() {
        return RestClient.builder()
                .baseUrl(aiAgentUrl)
                .defaultHeader("Content-Type", "application/json")
                .build();
    }
}