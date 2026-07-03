package com.knowledgeai.api.domain.document.dto;

import java.util.UUID;

public record DocumentUploadResponse(UUID documentId, String status, String message) {}
