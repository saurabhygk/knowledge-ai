package com.knowledgeai.api.domain.document;

import com.knowledgeai.api.domain.document.dto.DocumentResponse;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface DocumentMapper {

    @Mapping(source = "tenant.id", target = "tenantId")
    DocumentResponse toResponse(Document document);
}
