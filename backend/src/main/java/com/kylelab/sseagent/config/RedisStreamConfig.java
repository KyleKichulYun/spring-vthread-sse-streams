package com.kylelab.sseagent.config;

import com.kylelab.sseagent.messaging.RedisStreamListener;
import com.kylelab.sseagent.service.RedisPublisherService;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.connection.stream.ReadOffset;
import org.springframework.data.redis.connection.stream.StreamOffset;
import org.springframework.data.redis.stream.StreamMessageListenerContainer;

import java.time.Duration;

@Configuration
public class RedisStreamConfig {

    private final RedisStreamListener streamListener;

    public RedisStreamConfig(RedisStreamListener streamListener) {
        this.streamListener = streamListener;
    }

    @Bean
    public StreamMessageListenerContainer<String, MapRecord<String, String, String>> streamMessageListenerContainer(
            RedisConnectionFactory connectionFactory) {

        // 리스너 컨테이너 옵션 설정 (0.1초마다 폴링)
        StreamMessageListenerContainer.StreamMessageListenerContainerOptions<String, MapRecord<String, String, String>> options =
                StreamMessageListenerContainer.StreamMessageListenerContainerOptions.builder()
                        .pollTimeout(Duration.ofMillis(100))
                        .build();

        StreamMessageListenerContainer<String, MapRecord<String, String, String>> container =
                StreamMessageListenerContainer.create(connectionFactory, options);

        // 🚀 'ai:chat:broadcast' 스트림의 가장 최신 메시지(LATEST)부터 듣기 시작합니다.
        container.receive(
                StreamOffset.create(RedisPublisherService.STREAM_KEY, ReadOffset.latest()),
                streamListener
        );

        // 컨테이너 시작!
        container.start();
        return container;
    }
}