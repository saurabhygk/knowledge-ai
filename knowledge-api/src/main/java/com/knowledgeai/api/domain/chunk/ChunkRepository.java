package com.knowledgeai.api.domain.chunk;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.UUID;

public interface ChunkRepository extends JpaRepository<Chunk, UUID> {

    List<Chunk> findByDocumentIdOrderByChunkIndex(UUID documentId);

    @Modifying
    @Query("DELETE FROM Chunk c WHERE c.document.id = :documentId")
    void deleteByDocumentId(UUID documentId);
}
