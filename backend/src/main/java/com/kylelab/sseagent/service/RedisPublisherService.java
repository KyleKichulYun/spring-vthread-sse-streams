package com.kylelab.sseagent.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.kylelab.sseagent.dto.response.AiAgentResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.connection.stream.StreamRecords;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.Collections;

@Service
public class RedisPublisherService {

    private static final Logger log = LoggerFactory.getLogger(RedisPublisherService.class);

    // Redis Streams에서 사용할 채널(키) 이름입니다.
    // 나중에 Listener가 이 채널을 구독(Subscribe)하게 됩니다.
    public static final String STREAM_KEY = "ai:chat:broadcast";

    private final RedisTemplate<String, String> redisTemplate;
    private final ObjectMapper objectMapper; // 객체를 JSON 문자열로 바꿔주는 마법사

    public RedisPublisherService(RedisTemplate<String, String> redisTemplate, ObjectMapper objectMapper) {
        this.redisTemplate = redisTemplate;
        this.objectMapper = objectMapper;
    }

    /**
     * AI의 답변을 Redis Streams 채널에 발행(Publish)합니다.
     */
    public void publishAiResponse(AiAgentResponse response) {
        try {
            // 1. DTO 객체를 안전한 JSON 문자열로 변환
            String jsonMessage = objectMapper.writeValueAsString(response);

            // 2. Redis Stream에 넣을 레코드(메시지) 생성 (Key-Value 형태)
            MapRecord<String, String, String> record = StreamRecords.newRecord()
                    .in(STREAM_KEY)
                    .ofStrings(Collections.singletonMap("payload", jsonMessage));

            // 3. Streams 채널에 쏘아 올리기!
            redisTemplate.opsForStream().add(record);
            log.info("📢 [Redis Publish] AI 응답을 스트림에 발행했습니다! 데이터: {}", jsonMessage);

        } catch (JsonProcessingException e) {
            log.error("❌ JSON 직렬화 실패: {}", e.getMessage());
            throw new RuntimeException("AI 응답을 JSON으로 변환할 수 없습니다.", e);
        }
    }
}