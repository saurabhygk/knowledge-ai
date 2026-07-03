package com.knowledgeai.api;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@ConfigurationPropertiesScan
@EnableAsync
public class KnowledgeApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(KnowledgeApiApplication.class, args);
    }
}
