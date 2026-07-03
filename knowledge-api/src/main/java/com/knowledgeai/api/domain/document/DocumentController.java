package com.knowledgeai.api.domain.document;

import com.knowledgeai.api.domain.document.dto.DocumentResponse;
import com.knowledgeai.api.domain.document.dto.DocumentUploadResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/tenants/{tenantSlug}/documents")
@RequiredArgsConstructor
public class DocumentController {

    private final DocumentService documentService;

    @PostMapping(consumes = "multipart/form-data")
    public ResponseEntity<DocumentUploadResponse> upload(
            @PathVariable String tenantSlug,
            @RequestPart("file") MultipartFile file) {
        return ResponseEntity.accepted().body(documentService.upload(tenantSlug, file));
    }

    @GetMapping
    public Page<DocumentResponse> list(
            @PathVariable String tenantSlug,
            Pageable pageable) {
        return documentService.list(tenantSlug, pageable);
    }

    @GetMapping("/{documentId}")
    public DocumentResponse get(
            @PathVariable String tenantSlug,
            @PathVariable UUID documentId) {
        return documentService.get(tenantSlug, documentId);
    }
}
