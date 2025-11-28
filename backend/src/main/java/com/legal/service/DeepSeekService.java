package com.legal.service;

import com.alibaba.fastjson2.JSON;
import com.alibaba.fastjson2.JSONArray;
import com.alibaba.fastjson2.JSONObject;
import com.legal.config.DeepSeekConfig;
import com.legal.entity.LegalArticle;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;

@Slf4j
@Service
public class DeepSeekService {
    
    @Autowired
    private DeepSeekConfig deepSeekConfig;
    
    private OkHttpClient httpClient;
    
    private OkHttpClient getHttpClient() {
        if (httpClient == null) {
            synchronized (this) {
                if (httpClient == null) {
                    // 使用配置中的 timeout，如果没有配置则使用默认值
                    int timeout = deepSeekConfig.getTimeout() != null ? deepSeekConfig.getTimeout() : 120000; // 默认120秒
                    int timeoutSeconds = timeout / 1000;
                    
                    // 配置连接池以提升性能
                    ConnectionPool connectionPool = new ConnectionPool(10, 5, TimeUnit.MINUTES);
                    
                    this.httpClient = new OkHttpClient.Builder()
                            .connectTimeout(30, TimeUnit.SECONDS)
                            .readTimeout(timeoutSeconds, TimeUnit.SECONDS)
                            .writeTimeout(30, TimeUnit.SECONDS)
                            .connectionPool(connectionPool)
                            .retryOnConnectionFailure(true) // 自动重试连接失败
                            .build();
                    
                    log.info("DeepSeek HTTP客户端初始化完成，超时时间: {}秒", timeoutSeconds);
                }
            }
        }
        return httpClient;
    }
    
    /**
     * 调用DeepSeek API生成答案（带重试机制）
     */
    public String generateAnswer(String question, String context) {
        return generateAnswerWithRetry(question, context, 3); // 最多重试3次
    }
    
    /**
     * 流式调用DeepSeek API生成答案
     * @param question 用户问题
     * @param context 上下文
     * @param onChunk 接收到数据块时的回调函数
     * @return 完整的答案
     */
    public String generateAnswerStream(String question, String context, Consumer<String> onChunk) {
        return generateAnswerStreamWithRetry(question, context, onChunk, 3);
    }
    
    /**
     * 带重试机制的流式API调用
     */
    private String generateAnswerStreamWithRetry(String question, String context, Consumer<String> onChunk, int maxRetries) {
        int retryCount = 0;
        Exception lastException = null;
        
        while (retryCount < maxRetries) {
            try {
                JSONObject requestBody = new JSONObject();
                requestBody.put("model", deepSeekConfig.getModel());
                
                JSONArray messages = new JSONArray();
                
                // 系统提示词
                JSONObject systemMessage = new JSONObject();
                systemMessage.put("role", "system");
                systemMessage.put("content", buildSystemPrompt(context));
                messages.add(systemMessage);
                
                // 用户问题
                JSONObject userMessage = new JSONObject();
                userMessage.put("role", "user");
                userMessage.put("content", question);
                messages.add(userMessage);
                
                requestBody.put("messages", messages);
                requestBody.put("temperature", 0.7);
                requestBody.put("max_tokens", 2000);
                requestBody.put("stream", true); // 启用流式输出
                
                Request request = new Request.Builder()
                        .url(deepSeekConfig.getUrl())
                        .addHeader("Content-Type", "application/json")
                        .addHeader("Authorization", "Bearer " + deepSeekConfig.getApiKey())
                        .post(RequestBody.create(requestBody.toJSONString(), MediaType.parse("application/json")))
                        .build();
                
                log.debug("调用DeepSeek流式API (尝试 {}/{})", retryCount + 1, maxRetries);
                
                StringBuilder fullAnswer = new StringBuilder();
                
                try (Response response = getHttpClient().newCall(request).execute()) {
                    if (!response.isSuccessful()) {
                        String errorBody = response.body() != null ? response.body().string() : "";
                        log.warn("DeepSeek流式API调用失败: {} - {}", response.code(), errorBody);
                        
                        if (response.code() >= 500 && retryCount < maxRetries - 1) {
                            retryCount++;
                            Thread.sleep(1000 * retryCount);
                            continue;
                        }
                        
                        return "抱歉，服务暂时不可用，请稍后再试。";
                    }
                    
                    // 读取流式响应
                    try (BufferedReader reader = new BufferedReader(
                            new InputStreamReader(response.body().byteStream(), "UTF-8"))) {
                        String line;
                        while ((line = reader.readLine()) != null) {
                            if (line.trim().isEmpty()) {
                                continue;
                            }
                            
                            // SSE格式：data: {...}
                            if (line.startsWith("data: ")) {
                                String data = line.substring(6);
                                
                                // 流结束标记
                                if ("[DONE]".equals(data.trim())) {
                                    break;
                                }
                                
                                try {
                                    JSONObject jsonResponse = JSON.parseObject(data);
                                    
                                    // 检查错误
                                    if (jsonResponse.containsKey("error")) {
                                        JSONObject error = jsonResponse.getJSONObject("error");
                                        String errorMessage = error.getString("message");
                                        log.error("DeepSeek流式API返回错误: {}", errorMessage);
                                        return "抱歉，生成答案时出现错误：" + errorMessage;
                                    }
                                    
                                    JSONArray choices = jsonResponse.getJSONArray("choices");
                                    if (choices != null && choices.size() > 0) {
                                        JSONObject choice = choices.getJSONObject(0);
                                        JSONObject delta = choice.getJSONObject("delta");
                                        
                                        if (delta != null && delta.containsKey("content")) {
                                            String content = delta.getString("content");
                                            if (content != null && !content.isEmpty()) {
                                                fullAnswer.append(content);
                                                // 调用回调函数，实时推送数据
                                                onChunk.accept(content);
                                            }
                                        }
                                        
                                        // 检查是否完成
                                        String finishReason = choice.getString("finish_reason");
                                        if (finishReason != null && !finishReason.isEmpty()) {
                                            break;
                                        }
                                    }
                                } catch (Exception e) {
                                    log.warn("解析流式数据失败: {}", e.getMessage());
                                    // 继续处理下一行
                                }
                            }
                        }
                    }
                    
                    log.debug("DeepSeek流式API调用成功，答案长度: {}", fullAnswer.length());
                    return fullAnswer.toString();
                }
            } catch (IOException e) {
                lastException = e;
                log.warn("调用DeepSeek流式API异常 (尝试 {}/{}): {}", retryCount + 1, maxRetries, e.getMessage());
                
                if (retryCount < maxRetries - 1) {
                    retryCount++;
                    try {
                        Thread.sleep(1000 * retryCount);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        break;
                    }
                } else {
                    log.error("调用DeepSeek流式API失败，已重试{}次", maxRetries, e);
                }
            } catch (Exception e) {
                lastException = e;
                log.error("调用DeepSeek流式API时发生未知异常", e);
                break;
            }
        }
        
        String errorMsg = "抱歉，生成答案时出现错误，请稍后再试。";
        if (lastException != null) {
            if (lastException.getMessage() != null && lastException.getMessage().contains("timeout")) {
                errorMsg = "抱歉，请求超时，请稍后再试。";
            } else if (lastException.getMessage() != null && lastException.getMessage().contains("connection")) {
                errorMsg = "抱歉，网络连接失败，请检查网络后重试。";
            }
        }
        return errorMsg;
    }
    
    /**
     * 带重试机制的API调用
     */
    private String generateAnswerWithRetry(String question, String context, int maxRetries) {
        int retryCount = 0;
        Exception lastException = null;
        
        while (retryCount < maxRetries) {
            try {
                JSONObject requestBody = new JSONObject();
                requestBody.put("model", deepSeekConfig.getModel());
                
                JSONArray messages = new JSONArray();
                
                // 系统提示词
                JSONObject systemMessage = new JSONObject();
                systemMessage.put("role", "system");
                systemMessage.put("content", buildSystemPrompt(context));
                messages.add(systemMessage);
                
                // 用户问题
                JSONObject userMessage = new JSONObject();
                userMessage.put("role", "user");
                userMessage.put("content", question);
                messages.add(userMessage);
                
                requestBody.put("messages", messages);
                requestBody.put("temperature", 0.7);
                requestBody.put("max_tokens", 2000);
                
                Request request = new Request.Builder()
                        .url(deepSeekConfig.getUrl())
                        .addHeader("Content-Type", "application/json")
                        .addHeader("Authorization", "Bearer " + deepSeekConfig.getApiKey())
                        .post(RequestBody.create(requestBody.toJSONString(), MediaType.parse("application/json")))
                        .build();
                
                log.debug("调用DeepSeek API (尝试 {}/{})", retryCount + 1, maxRetries);
                
                try (Response response = getHttpClient().newCall(request).execute()) {
                    if (!response.isSuccessful()) {
                        String errorBody = response.body() != null ? response.body().string() : "";
                        log.warn("DeepSeek API调用失败: {} - {}", response.code(), errorBody);
                        
                        // 如果是服务器错误（5xx），可以重试
                        if (response.code() >= 500 && retryCount < maxRetries - 1) {
                            retryCount++;
                            Thread.sleep(1000 * retryCount); // 递增延迟
                            continue;
                        }
                        
                        return "抱歉，服务暂时不可用，请稍后再试。";
                    }
                    
                    String responseBody = response.body().string();
                    JSONObject jsonResponse = JSON.parseObject(responseBody);
                    
                    // 检查是否有错误
                    if (jsonResponse.containsKey("error")) {
                        JSONObject error = jsonResponse.getJSONObject("error");
                        String errorMessage = error.getString("message");
                        log.error("DeepSeek API返回错误: {}", errorMessage);
                        
                        // 如果是速率限制错误，可以重试
                        if (errorMessage != null && errorMessage.contains("rate limit") && retryCount < maxRetries - 1) {
                            retryCount++;
                            Thread.sleep(2000 * retryCount); // 速率限制时延迟更久
                            continue;
                        }
                        
                        return "抱歉，生成答案时出现错误：" + errorMessage;
                    }
                    
                    JSONArray choices = jsonResponse.getJSONArray("choices");
                    
                    if (choices != null && choices.size() > 0) {
                        JSONObject choice = choices.getJSONObject(0);
                        JSONObject message = choice.getJSONObject("message");
                        String content = message.getString("content");
                        log.debug("DeepSeek API调用成功，答案长度: {}", content != null ? content.length() : 0);
                        return content;
                    } else {
                        log.warn("DeepSeek API返回的choices为空");
                        return "抱歉，未能生成有效答案，请稍后再试。";
                    }
                }
            } catch (IOException e) {
                lastException = e;
                log.warn("调用DeepSeek API异常 (尝试 {}/{}): {}", retryCount + 1, maxRetries, e.getMessage());
                
                if (retryCount < maxRetries - 1) {
                    retryCount++;
                    try {
                        Thread.sleep(1000 * retryCount); // 递增延迟：1秒、2秒、3秒
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        break;
                    }
                } else {
                    log.error("调用DeepSeek API失败，已重试{}次", maxRetries, e);
                }
            } catch (Exception e) {
                lastException = e;
                log.error("调用DeepSeek API时发生未知异常", e);
                break; // 非IO异常不重试
            }
        }
        
        // 所有重试都失败
        String errorMsg = "抱歉，生成答案时出现错误，请稍后再试。";
        if (lastException != null) {
            if (lastException.getMessage() != null && lastException.getMessage().contains("timeout")) {
                errorMsg = "抱歉，请求超时，请稍后再试。";
            } else if (lastException.getMessage() != null && lastException.getMessage().contains("connection")) {
                errorMsg = "抱歉，网络连接失败，请检查网络后重试。";
            }
        }
        return errorMsg;
    }
    
    /**
     * 构建系统提示词
     */
    private String buildSystemPrompt(String context) {
        StringBuilder prompt = new StringBuilder();
        prompt.append("你是一位专业的法律咨询AI助手，具有丰富的法律知识和司法实践经验。");
        prompt.append("你的任务是回答用户的法律问题，提供准确、专业、易懂的法律建议。");
        prompt.append("\n\n");
        prompt.append("回答要求：");
        prompt.append("1. 回答要准确、专业，基于中国法律法规");
        prompt.append("2. 语言要通俗易懂，避免过于专业的术语");
        prompt.append("3. 如果涉及具体法条，要明确指出法条名称和条号");
        prompt.append("4. 如果是案例分析，要提供相关案例参考");
        prompt.append("5. 如果问题不够明确，要主动询问以获取更多信息");
        prompt.append("\n\n");
        
        if (context != null && !context.isEmpty()) {
            prompt.append("相关知识上下文：\n");
            prompt.append(context);
            prompt.append("\n\n");
        }
        
        prompt.append("请根据以上要求回答用户的问题。");
        
        return prompt.toString();
    }
    
    /**
     * 问题分类（简化版，减少API调用）
     */
    public String classifyQuestion(String question) {
        // 使用简单的关键词匹配，减少API调用
        String lowerQuestion = question.toLowerCase();
        if (lowerQuestion.contains("第") && (lowerQuestion.contains("条") || lowerQuestion.contains("款"))) {
            return "法条查询";
        }
        if (lowerQuestion.contains("是什么") || lowerQuestion.contains("定义") || lowerQuestion.contains("概念")) {
            return "概念定义";
        }
        if (lowerQuestion.contains("怎么") || lowerQuestion.contains("如何") || lowerQuestion.contains("流程") || lowerQuestion.contains("程序")) {
            return "程序咨询";
        }
        if (lowerQuestion.contains("案例") || lowerQuestion.contains("判例") || lowerQuestion.contains("判决")) {
            return "案例分析";
        }
        
        // 如果关键词匹配失败，再调用API（但使用更短的提示词）
        try {
            String prompt = "分类：" + question.substring(0, Math.min(100, question.length()));
            String result = generateAnswerWithRetry(prompt, "只返回：法条查询、概念定义、程序咨询、案例分析、其他", 2);
            return extractCategory(result);
        } catch (Exception e) {
            log.warn("问题分类失败，使用默认分类", e);
            return "其他";
        }
    }
    
    /**
     * 实体识别（简化版，减少API调用）
     */
    public Map<String, List<String>> extractEntities(String question) {
        Map<String, List<String>> entities = new HashMap<>();
        entities.put("laws", new ArrayList<>());
        entities.put("crimes", new ArrayList<>());
        entities.put("organizations", new ArrayList<>());
        entities.put("concepts", new ArrayList<>());
        
        // 简单的实体提取（基于关键词）
        // 提取法条名称（包含《》的内容）
        java.util.regex.Pattern lawPattern = java.util.regex.Pattern.compile("《([^》]+)》");
        java.util.regex.Matcher lawMatcher = lawPattern.matcher(question);
        while (lawMatcher.find()) {
            entities.get("laws").add(lawMatcher.group(1));
        }
        
        // 如果简单提取失败，再调用API（但使用更短的提示词）
        if (entities.get("laws").isEmpty()) {
            try {
                String prompt = "提取实体：" + question.substring(0, Math.min(100, question.length()));
                String result = generateAnswerWithRetry(prompt, "返回JSON：{\"laws\":[],\"crimes\":[],\"organizations\":[],\"concepts\":[]}", 2);
                Map<String, List<String>> apiEntities = parseEntities(result);
                // 合并结果
                entities.get("laws").addAll(apiEntities.getOrDefault("laws", new ArrayList<>()));
                entities.get("crimes").addAll(apiEntities.getOrDefault("crimes", new ArrayList<>()));
                entities.get("organizations").addAll(apiEntities.getOrDefault("organizations", new ArrayList<>()));
                entities.get("concepts").addAll(apiEntities.getOrDefault("concepts", new ArrayList<>()));
            } catch (Exception e) {
                log.warn("实体识别失败", e);
            }
        }
        
        return entities;
    }
    
    /**
     * 评估答案可信度（简化版本，保持向后兼容）
     */
    public Double evaluateConfidence(String question, String answer) {
        return evaluateConfidence(question, answer, null, null, null, null);
    }
    
    /**
     * 评估答案可信度（增强版本）
     * 基于多维度因素进行综合评估，提高可信度计算的精确度
     * 
     * @param question 用户问题
     * @param answer 生成的答案
     * @param context 知识库检索的上下文（可为null）
     * @param relatedLaws 相关法条列表（可为null）
     * @param relatedCases 相关案例列表（可为null）
     * @param entities 识别的实体（可为null）
     * @return 可信度评分 0.0-1.0
     */
    public Double evaluateConfidence(String question, String answer, 
                                     String context, 
                                     List<?> relatedLaws, 
                                     List<?> relatedCases, 
                                     Map<String, List<String>> entities) {
        double score = 0.0;
        
        // 1. 答案质量评估 (30%)
        score += evaluateAnswerQuality(question, answer);
        
        // 2. 法条引用评估 (25%)
        score += evaluateLegalCitation(answer, relatedLaws);
        
        // 3. 知识库匹配度评估 (20%)
        score += evaluateKnowledgeMatch(context);
        
        // 4. 相关资源评估 (15%)
        score += evaluateRelatedResources(relatedLaws, relatedCases);
        
        // 5. 实体识别评估 (10%)
        score += evaluateEntityRecognition(entities);
        
        return Math.min(Math.max(score, 0.0), 1.0);
    }
    
    /**
     * 评估答案质量 (最高0.3分)
     */
    private double evaluateAnswerQuality(String question, String answer) {
        double score = 0.0;
        
        // 答案长度评估
        int answerLength = answer.length();
        if (answerLength > 500) {
            score += 0.15; // 详细答案
        } else if (answerLength > 200) {
            score += 0.10; // 中等长度
        } else if (answerLength > 100) {
            score += 0.05; // 基本长度
        } else if (answerLength < 20) {
            score -= 0.05; // 答案过短，扣分
        }
        
        // 答案完整性：检查是否包含问题中的关键词
        if (question != null && answer != null) {
            String[] questionKeywords = question.replaceAll("[，。！？、]", " ").split("\\s+");
            int matchedKeywords = 0;
            for (String keyword : questionKeywords) {
                if (keyword.length() > 1 && answer.contains(keyword)) {
                    matchedKeywords++;
                }
            }
            if (questionKeywords.length > 0) {
                double matchRatio = (double) matchedKeywords / questionKeywords.length;
                score += matchRatio * 0.10; // 关键词匹配度
            }
        }
        
        // 答案结构评估：检查是否有段落分隔或列表
        if (answer.contains("\n") || answer.contains("。") || 
            answer.contains("1.") || answer.contains("一、") || 
            answer.contains("（") || answer.contains("(")) {
            score += 0.05; // 结构化答案
        }
        
        return Math.min(score, 0.3);
    }
    
    /**
     * 评估法条引用 (最高0.25分)
     */
    private double evaluateLegalCitation(String answer, List<?> relatedLaws) {
        double score = 0.0;
        
        // 检查是否包含书名号
        if (answer.contains("《") && answer.contains("》")) {
            score += 0.10;
            
            // 检查书名号数量（多个法条引用更可信）
            long bookCount = answer.chars().filter(ch -> ch == '《').count();
            if (bookCount > 1) {
                score += 0.05;
            }
        }
        
        // 检查是否包含"第X条"格式
        if (answer.contains("第") && answer.contains("条")) {
            score += 0.10;
            
            // 检查是否有具体的条文编号（数字+条）
            if (answer.matches(".*第\\d+条.*")) {
                score += 0.05;
            }
        }
        
        // 如果答案中实际引用了相关法条，额外加分
        if (relatedLaws != null && !relatedLaws.isEmpty() && answer != null) {
            int matchedLaws = 0;
            for (Object lawObj : relatedLaws) {
                if (lawObj != null) {
                    // 如果是 LegalArticle 对象，精确检查
                    if (lawObj instanceof LegalArticle) {
                        LegalArticle law = (LegalArticle) lawObj;
                        String title = law.getTitle();
                        String articleNumber = law.getArticleNumber();
                        
                        // 检查答案中是否包含法条标题
                        if (title != null && answer.contains(title)) {
                            matchedLaws++;
                        }
                        // 检查答案中是否包含法条编号
                        if (articleNumber != null && answer.contains("第" + articleNumber + "条")) {
                            matchedLaws++;
                        }
                    } else {
                        // 如果不是 LegalArticle 对象，使用 toString 方法
                        String lawStr = lawObj.toString();
                        if (answer.contains(lawStr)) {
                            matchedLaws++;
                        }
                    }
                }
            }
            if (matchedLaws > 0) {
                score += Math.min(0.05 * matchedLaws, 0.05); // 最多加0.05分
            }
        }
        
        return Math.min(score, 0.25);
    }
    
    /**
     * 评估知识库匹配度 (最高0.2分)
     */
    private double evaluateKnowledgeMatch(String context) {
        double score = 0.0;
        
        if (context != null && !context.trim().isEmpty()) {
            score += 0.10; // 有知识库检索结果
            
            // 根据上下文长度评估
            int contextLength = context.length();
            if (contextLength > 500) {
                score += 0.10; // 丰富的上下文
            } else if (contextLength > 200) {
                score += 0.05; // 中等上下文
            }
            
            // 检查是否包含相关问答、法条、概念等
            if (context.contains("相关问答") || context.contains("相关法条") || 
                context.contains("概念定义")) {
                score += 0.05;
            }
        }
        
        return Math.min(score, 0.2);
    }
    
    /**
     * 评估相关资源 (最高0.15分)
     */
    private double evaluateRelatedResources(List<?> relatedLaws, List<?> relatedCases) {
        double score = 0.0;
        
        // 相关法条评估
        if (relatedLaws != null && !relatedLaws.isEmpty()) {
            score += 0.08;
            if (relatedLaws.size() > 2) {
                score += 0.02; // 多个法条引用
            }
        }
        
        // 相关案例评估
        if (relatedCases != null && !relatedCases.isEmpty()) {
            score += 0.07;
            if (relatedCases.size() > 1) {
                score += 0.03; // 多个案例引用
            }
        }
        
        return Math.min(score, 0.15);
    }
    
    /**
     * 评估实体识别 (最高0.1分)
     */
    private double evaluateEntityRecognition(Map<String, List<String>> entities) {
        double score = 0.0;
        
        if (entities != null && !entities.isEmpty()) {
            score += 0.05; // 识别到实体
            
            // 统计实体总数
            int totalEntities = entities.values().stream()
                    .mapToInt(List::size)
                    .sum();
            
            if (totalEntities > 2) {
                score += 0.05; // 识别到多个实体
            } else if (totalEntities > 0) {
                score += 0.02; // 识别到少量实体
            }
        }
        
        return Math.min(score, 0.1);
    }
    
    private String extractCategory(String result) {
        if (result.contains("法条查询")) return "法条查询";
        if (result.contains("概念定义")) return "概念定义";
        if (result.contains("程序咨询")) return "程序咨询";
        if (result.contains("案例分析")) return "案例分析";
        return "其他";
    }
    
    private Map<String, List<String>> parseEntities(String result) {
        Map<String, List<String>> entities = new HashMap<>();
        entities.put("laws", new ArrayList<>());
        entities.put("crimes", new ArrayList<>());
        entities.put("organizations", new ArrayList<>());
        entities.put("concepts", new ArrayList<>());
        
        try {
            JSONObject json = JSON.parseObject(result);
            if (json != null) {
                entities.put("laws", json.getJSONArray("laws") != null ? 
                    json.getJSONArray("laws").toJavaList(String.class) : new ArrayList<>());
                entities.put("crimes", json.getJSONArray("crimes") != null ? 
                    json.getJSONArray("crimes").toJavaList(String.class) : new ArrayList<>());
                entities.put("organizations", json.getJSONArray("organizations") != null ? 
                    json.getJSONArray("organizations").toJavaList(String.class) : new ArrayList<>());
                entities.put("concepts", json.getJSONArray("concepts") != null ? 
                    json.getJSONArray("concepts").toJavaList(String.class) : new ArrayList<>());
            }
        } catch (Exception e) {
            log.warn("解析实体失败", e);
        }
        
        return entities;
    }
}

