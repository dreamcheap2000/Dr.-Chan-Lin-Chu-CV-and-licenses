package com.phcep;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * PHCEP — Personal Health Care Evidence-Based Medicine Platform
 * Spring Boot application entry point.
 */
@SpringBootApplication
@EnableAsync
@EnableScheduling
public class PhcepApplication {

    public static void main(String[] args) {
        SpringApplication.run(PhcepApplication.class, args);
    }
}
