package com.knowledgeai.api.domain.document;

import com.knowledgeai.api.domain.document.dto.DocumentResponse;
import com.knowledgeai.api.domain.document.dto.DocumentUploadResponse;
import com.knowledgeai.api.domain.tenant.Tenant;
import com.knowledgeai.api.domain.tenant.TenantRepository;
import com.knowledgeai.api.processing.DocumentProcessingProducer;
import com.knowledgeai.api.processing.ProcessingEvent;
import com.knowledgeai.api.storage.StorageService;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class DocumentService {

    private final DocumentRepository documentRepository;
    private final TenantRepository tenantRepository;
    private final StorageService storageService;
    private final DocumentProcessingProducer processingProducer;
    private final DocumentMapper documentMapper;

    @Transactional
    public DocumentUploadResponse upload(String tenantSlug, MultipartFile file) {
        Tenant tenant = tenantRepository.findBySlug(tenantSlug)
                .orElseThrow(() -> new EntityNotFoundException("Tenant not found: " + tenantSlug));

        String storageKey = "%s/%s/%s".formatted(tenant.getId(), UUID.randomUUID(), file.getOriginalFilename());

        try {
            storageService.upload(storageKey, file.getInputStream(),
                    file.getSize(), file.getContentType());
        } catch (Exception e) {
            throw new RuntimeException("File upload failed", e);
        }

        Document doc = Document.builder()
                .tenant(tenant)
                .filename(file.getOriginalFilename())
                .contentType(file.getContentType())
                .storageKey(storageKey)
                .status(DocumentStatus.UPLOADED)
                .build();

        doc = documentRepository.save(doc);

        processingProducer.publish(new ProcessingEvent(
                doc.getId(), tenant.getId(), storageKey, file.getContentType()));

        log.info("Document uploaded id={} tenant={}", doc.getId(), tenantSlug);
        return new DocumentUploadResponse(doc.getId(), doc.getStatus().name(),
                "Document uploaded and queued for processing");
    }

    public Page<DocumentResponse> list(String tenantSlug, Pageable pageable) {
        Tenant tenant = tenantRepository.findBySlug(tenantSlug)
                .orElseThrow(() -> new EntityNotFoundException("Tenant not found: " + tenantSlug));
        return documentRepository.findByTenantId(tenant.getId(), pageable)
                .map(documentMapper::toResponse);
    }

    public DocumentResponse get(String tenantSlug, UUID documentId) {
        Tenant tenant = tenantRepository.findBySlug(tenantSlug)
                .orElseThrow(() -> new EntityNotFoundException("Tenant not found: " + tenantSlug));
        Document doc = documentRepository.findByIdAndTenantId(documentId, tenant.getId())
                .orElseThrow(() -> new EntityNotFoundException("Document not found: " + documentId));
        return documentMapper.toResponse(doc);
    }
}
