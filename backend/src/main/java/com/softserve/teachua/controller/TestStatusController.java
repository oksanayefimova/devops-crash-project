package com.softserve.teachua.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * Temporary controller for load-testing the monitoring stack.
 * Returns controlled HTTP status codes and optional delays.
 */
@RestController
public class TestStatusController {

    private static final int MAX_SLEEP_SECONDS = 10;

    @GetMapping("/200")
    public ResponseEntity<Map<String, Integer>> ok(
            @RequestParam(value = "seconds_sleep", defaultValue = "0") int secondsSleep)
            throws InterruptedException {
        sleep(Math.max(0, Math.min(secondsSleep, MAX_SLEEP_SECONDS)));
        return status(HttpStatus.OK);
    }

    @GetMapping("/400")
    public ResponseEntity<Map<String, Integer>> badRequest() {
        return status(HttpStatus.BAD_REQUEST);
    }

    @GetMapping("/409")
    public ResponseEntity<Map<String, Integer>> conflict() {
        return status(HttpStatus.CONFLICT);
    }

    @GetMapping("/500")
    public ResponseEntity<Map<String, Integer>> internalServerError() {
        return status(HttpStatus.INTERNAL_SERVER_ERROR);
    }

    private void sleep(int seconds) throws InterruptedException {
        if (seconds > 0) {
            TimeUnit.SECONDS.sleep(seconds);
        }
    }

    private ResponseEntity<Map<String, Integer>> status(HttpStatus status) {
        return ResponseEntity.status(status).body(Map.of("status", status.value()));
    }
}
