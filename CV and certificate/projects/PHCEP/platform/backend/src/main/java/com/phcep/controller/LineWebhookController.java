package com.phcep.controller;

import com.linecorp.bot.model.event.MessageEvent;
import com.linecorp.bot.model.event.message.TextMessageContent;
import com.linecorp.bot.spring.boot.annotation.EventMapping;
import com.linecorp.bot.spring.boot.annotation.LineMessageHandler;
import com.phcep.service.QueryService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * LINE Messaging API webhook endpoint and integration controller.
 *
 * The webhook receives events from LINE platform.
 * When a text message is received it is treated as a medical query
 * submitted by the LINE user (mapped to pseudonymous token via LINE user ID).
 */
@RestController
@RequestMapping("/api/line")
@RequiredArgsConstructor
public class LineWebhookController {

    private final QueryService queryService;

    /**
     * LINE Bot webhook — receives message events.
     * LINE SDK validates the X-Line-Signature header automatically.
     */
    @PostMapping("/webhook")
    public ResponseEntity<String> webhook(@RequestBody String body,
                                           @RequestHeader("X-Line-Signature") String signature) {
        // Signature verification and event dispatch is handled by LINE SDK
        return ResponseEntity.ok("OK");
    }

    /**
     * Handle incoming text messages from LINE users.
     * Annotated method invoked by LINE SDK when a text message event arrives.
     */
    @EventMapping
    public void handleTextMessage(MessageEvent<TextMessageContent> event) {
        String lineUserId = event.getSource().getUserId();
        String messageText = event.getMessage().getText();
        // Map LINE user ID to pseudonymous token and submit as query
        queryService.submitQueryFromLine(lineUserId, messageText);
    }
}
