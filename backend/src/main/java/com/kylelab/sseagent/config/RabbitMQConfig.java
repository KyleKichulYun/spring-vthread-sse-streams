package com.kylelab.sseagent.config;

import org.springframework.amqp.core.Queue;
import org.springframework.amqp.support.converter.JacksonJsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {
    public static final String QUESTION_QUEUE = "question.queue";
    public static final String ANSWER_QUEUE = "answer.queue";

    // 1. Spring Boot가 뜰 때 큐가 없으면 자동으로 생성해 줍니다.
    @Bean
    public Queue questionQueue() {
        return new Queue(QUESTION_QUEUE, true); // true: 서버가 재시작되어도 큐 유지(Durable)
    }

    @Bean
    public Queue answerQueue() {
        return new Queue(ANSWER_QUEUE, true);
    }

    // 2. 객체를 JSON 현태로 큐에 넣고 빼기 위한 컨버터
    @Bean
    public MessageConverter messageConverter() {
        return new JacksonJsonMessageConverter();
    }
}
