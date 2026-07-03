package com.knowledgeai.api.processing;

import java.util.UUID;

public record ProcessingEvent(
        UUID documentId,
        UUID tenantId,
        String storageKey,
        String contentType
) {}
