package com.knowledgeai.api.domain.document;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface DocumentRepository extends JpaRepository<Document, UUID> {

    Page<Document> findByTenantIdAndStatus(UUID tenantId, DocumentStatus status, Pageable pageable);

    Page<Document> findByTenantId(UUID tenantId, Pageable pageable);

    Optional<Document> findByIdAndTenantId(UUID id, UUID tenantId);
}
