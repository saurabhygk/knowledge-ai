package com.knowledgeai.api.processing;

import com.knowledgeai.api.config.RedisStreamConfig;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.connection.stream.ObjectRecord;
import org.springframework.data.redis.connection.stream.StreamRecords;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class DocumentProcessingProducer {

    private final RedisTemplate<String, Object> redisTemplate;

    public void publish(ProcessingEvent event) {
        ObjectRecord<String, ProcessingEvent> record = StreamRecords
                .newRecord()
                .ofObject(event)
                .withStreamKey(RedisStreamConfig.PROCESSING_STREAM);

        redisTemplate.opsForStream().add(record);
        log.info("Published processing event for document={}", event.documentId());
    }
}
