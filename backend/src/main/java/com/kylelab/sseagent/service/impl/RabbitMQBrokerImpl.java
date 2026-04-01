package com.kylelab.sseagent.service.impl;

import com.kylelab.sseagent.config.RabbitMQConfig;
import com.kylelab.sseagent.dto.request.ChatMessageRequest;
import com.kylelab.sseagent.service.MessageBrokerService;
import com.kylelab.sseagent.service.SseSessionManager;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;

import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
@ConditionalOnProperty(name = "app.broker.type", havingValue = "rabbitmq", matchIfMissing = true)
public class RabbitMQBrokerImpl implements MessageBrokerService {

    private final RabbitTemplate rabbitTemplate;
    private final SseSessionManager sseSessionManager;

    @Override
    public void sendQuestion(ChatMessageRequest request) {
        rabbitTemplate.convertAndSend(RabbitMQConfig.QUESTION_QUEUE, request);
        log.info("🐰 [RabbitMQ 발송] question.queue -> {}", request.question());
    }

    @RabbitListener(queues = RabbitMQConfig.ANSWER_QUEUE)
    public void receiveAnswer(Map<String, Object> responseData) {
        log.info("🐰 [RabbitMQ 수신] answer.queue <- {}", responseData);

        String threadId = (String) responseData.get("threadId");
        Boolean isDone = (Boolean) responseData.getOrDefault("isDone", false);

        sseSessionManager.sendToClient(threadId, responseData, isDone);
    }
}