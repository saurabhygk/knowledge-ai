package com.knowledgeai.api.storage;

import java.io.InputStream;

public interface StorageService {
    String upload(String key, InputStream data, long size, String contentType);
    InputStream download(String key);
    void delete(String key);
}
