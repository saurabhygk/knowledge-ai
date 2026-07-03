package com.knowledgeai.api.domain.chunk;

import com.knowledgeai.api.domain.document.Document;
import com.knowledgeai.api.domain.tenant.Tenant;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

@Entity
@Table(name = "chunks", indexes = {
    @Index(name = "idx_chunks_document", columnList = "document_id"),
    @Index(name = "idx_chunks_tenant",   columnList = "tenant_id")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Chunk {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "document_id", nullable = false)
    private Document document;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "tenant_id", nullable = false)
    private Tenant tenant;

    @Column(nullable = false)
    private Integer chunkIndex;

    @Column(columnDefinition = "text", nullable = false)
    private String text;

    private Integer charStart;
    private Integer charEnd;

    // Embedding is managed by Spring AI VectorStore in the vector_store table — not mapped here.

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    @Builder.Default
    private Map<String, Object> metadata = Map.of();

    @CreationTimestamp
    @Column(updatable = false)
    private OffsetDateTime createdAt;
}
