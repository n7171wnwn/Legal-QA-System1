package com.legal.controller;

import com.legal.dto.ApiResponse;
import com.legal.service.QuestionAnswerService;
import com.legal.util.JwtUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.Map;
import org.springframework.http.MediaType;

@Slf4j
@RestController
@RequestMapping("/qa")
@CrossOrigin
public class QuestionAnswerController {
    
    @Autowired
    private QuestionAnswerService questionAnswerService;
    
    @Autowired
    private JwtUtil jwtUtil;
    
    /**
     * 提问（普通模式）
     */
    @PostMapping("/ask")
    public ApiResponse<Map<String, Object>> askQuestion(
            @RequestBody Map<String, String> request,
            HttpServletRequest httpRequest) {
        long startTime = System.currentTimeMillis();
        try {
            log.info("收到提问请求，question: {}", request.get("question"));
            
            String question = request.get("question");
            if (question == null || question.trim().isEmpty()) {
                log.warn("问题为空");
                return ApiResponse.error("问题不能为空");
            }
            
            String sessionId = request.getOrDefault("sessionId", generateSessionId());
            log.info("Session ID: {}", sessionId);
            
            String token = httpRequest.getHeader("Authorization");
            Long userId = null;
            if (token != null && token.startsWith("Bearer ")) {
                token = token.substring(7);
                if (jwtUtil.validateToken(token)) {
                    userId = jwtUtil.getUserIdFromToken(token);
                    log.info("用户ID: {}", userId);
                }
            }
            
            log.info("开始处理问题...");
            Map<String, Object> result = questionAnswerService.processQuestion(question, userId, sessionId);
            long duration = System.currentTimeMillis() - startTime;
            log.info("问题处理完成，耗时: {}ms", duration);
            return ApiResponse.success(result);
        } catch (Exception e) {
            long duration = System.currentTimeMillis() - startTime;
            log.error("处理问题失败，耗时: {}ms", duration, e);
            return ApiResponse.error("处理问题失败：" + e.getMessage());
        }
    }
    
    /**
     * 流式提问（SSE模式）
     */
    @PostMapping(value = "/ask/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public void askQuestionStream(
            @RequestBody Map<String, String> request,
            HttpServletRequest httpRequest,
            javax.servlet.http.HttpServletResponse response) {
        try {
            String question = request.get("question");
            String sessionId = request.getOrDefault("sessionId", generateSessionId());
            
            String token = httpRequest.getHeader("Authorization");
            Long userId = null;
            if (token != null && token.startsWith("Bearer ")) {
                token = token.substring(7);
                if (jwtUtil.validateToken(token)) {
                    userId = jwtUtil.getUserIdFromToken(token);
                }
            }
            
            // 设置SSE响应头
            response.setContentType(MediaType.TEXT_EVENT_STREAM_VALUE);
            response.setCharacterEncoding("UTF-8");
            response.setHeader("Cache-Control", "no-cache");
            response.setHeader("Connection", "keep-alive");
            response.setHeader("X-Accel-Buffering", "no"); // 禁用nginx缓冲
            
            final PrintWriter writer = response.getWriter();
            
            // 先发送初始信息
            writer.write("event: start\n");
            writer.write("data: " + sessionId + "\n\n");
            writer.flush();
            
            // 流式处理问题
            java.util.function.Consumer<String> onChunk = (chunk) -> {
                if (chunk == null || chunk.isEmpty()) {
                    return;
                }
                String sanitized = chunk.replace("\r", "");
                String[] lines = sanitized.split("\n");
                for (String line : lines) {
                    writer.write("data: " + line + "\n");
                }
                writer.write("\n");
                writer.flush();
            };
            questionAnswerService.processQuestionStream(question, userId, sessionId, onChunk, writer);
            
            // 发送结束标记
            writer.write("event: end\n");
            writer.write("data: done\n\n");
            writer.flush();
            
        } catch (Exception e) {
            log.error("流式处理问题失败", e);
            try {
                PrintWriter errorWriter = response.getWriter();
                errorWriter.write("event: error\n");
                errorWriter.write("data: " + e.getMessage() + "\n\n");
                errorWriter.flush();
            } catch (IOException ex) {
                log.error("写入错误信息失败", ex);
            }
        }
    }
    
    /**
     * 获取问答历史
     */
    @GetMapping("/history")
    public ApiResponse<Page<?>> getHistory(
            @RequestParam(defaultValue = "0") Integer page,
            @RequestParam(defaultValue = "10") Integer size,
            HttpServletRequest request) {
        try {
            String token = request.getHeader("Authorization");
            if (token == null || !token.startsWith("Bearer ")) {
                return ApiResponse.error(401, "未登录");
            }
            
            token = token.substring(7);
            if (!jwtUtil.validateToken(token)) {
                return ApiResponse.error(401, "Token无效");
            }
            
            Long userId = jwtUtil.getUserIdFromToken(token);
            Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createTime"));
            Page<?> history = questionAnswerService.getQuestionHistory(userId, pageable);
            return ApiResponse.success(history);
        } catch (Exception e) {
            log.error("获取历史失败", e);
            return ApiResponse.error("获取历史失败：" + e.getMessage());
        }
    }
    
    /**
     * 获取会话历史
     */
    @GetMapping("/conversation/{sessionId}")
    public ApiResponse<?> getConversation(@PathVariable String sessionId) {
        try {
            return ApiResponse.success(questionAnswerService.getConversationHistory(sessionId));
        } catch (Exception e) {
            log.error("获取会话历史失败", e);
            return ApiResponse.error("获取会话历史失败：" + e.getMessage());
        }
    }
    
    /**
     * 提交反馈
     */
    @PostMapping("/feedback")
    public ApiResponse<?> submitFeedback(@RequestBody Map<String, Object> request) {
        try {
            Long qaId = Long.valueOf(request.get("qaId").toString());
            String feedbackType = request.get("feedbackType").toString();
            questionAnswerService.submitFeedback(qaId, feedbackType);
            return ApiResponse.success("反馈提交成功");
        } catch (Exception e) {
            log.error("提交反馈失败", e);
            return ApiResponse.error("提交反馈失败：" + e.getMessage());
        }
    }
    
    /**
     * 收藏/取消收藏问答
     */
    @PostMapping("/favorite")
    public ApiResponse<?> toggleFavorite(@RequestBody Map<String, Object> request, HttpServletRequest httpRequest) {
        try {
            String token = httpRequest.getHeader("Authorization");
            if (token == null || !token.startsWith("Bearer ")) {
                return ApiResponse.error(401, "未登录");
            }
            
            token = token.substring(7);
            if (!jwtUtil.validateToken(token)) {
                return ApiResponse.error(401, "Token无效");
            }
            
            Long qaId = Long.valueOf(request.get("qaId").toString());
            Boolean isFavorite = questionAnswerService.toggleFavorite(qaId);
            return ApiResponse.success(isFavorite ? "收藏成功" : "取消收藏成功");
        } catch (Exception e) {
            log.error("收藏操作失败", e);
            return ApiResponse.error("收藏操作失败：" + e.getMessage());
        }
    }
    
    /**
     * 获取收藏列表
     */
    @GetMapping("/favorites")
    public ApiResponse<Page<?>> getFavorites(
            @RequestParam(defaultValue = "0") Integer page,
            @RequestParam(defaultValue = "10") Integer size,
            HttpServletRequest request) {
        try {
            String token = request.getHeader("Authorization");
            if (token == null || !token.startsWith("Bearer ")) {
                return ApiResponse.error(401, "未登录");
            }
            
            token = token.substring(7);
            if (!jwtUtil.validateToken(token)) {
                return ApiResponse.error(401, "Token无效");
            }
            
            Long userId = jwtUtil.getUserIdFromToken(token);
            Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createTime"));
            Page<?> favorites = questionAnswerService.getFavorites(userId, pageable);
            return ApiResponse.success(favorites);
        } catch (Exception e) {
            log.error("获取收藏列表失败", e);
            return ApiResponse.error("获取收藏列表失败：" + e.getMessage());
        }
    }
    
    private String generateSessionId() {
        return "session_" + System.currentTimeMillis() + "_" + (int)(Math.random() * 1000);
    }
}

