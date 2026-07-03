package com.knowledgeai.api.domain.document.dto;

import com.knowledgeai.api.domain.document.DocumentStatus;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

public record DocumentResponse(
        UUID id,
        UUID tenantId,
        String filename,
        String contentType,
        DocumentStatus status,
        Map<String, Object> metadata,
        String errorMessage,
        OffsetDateTime createdAt,
        OffsetDateTime indexedAt
) {}
