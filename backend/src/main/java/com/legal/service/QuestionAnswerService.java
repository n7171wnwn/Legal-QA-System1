package com.legal.service;

import com.alibaba.fastjson2.JSON;
import com.legal.entity.KnowledgeBase;
import com.legal.entity.LegalArticle;
import com.legal.entity.LegalCase;
import com.legal.entity.LegalConcept;
import com.legal.entity.QuestionAnswer;
import com.legal.repository.KnowledgeBaseRepository;
import com.legal.repository.LegalArticleRepository;
import com.legal.repository.LegalCaseRepository;
import com.legal.repository.LegalConceptRepository;
import com.legal.repository.QuestionAnswerRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.PrintWriter;
import java.util.*;
import java.util.function.Consumer;
import java.util.stream.Collectors;

@Slf4j
@Service
public class QuestionAnswerService {
    
    @Autowired
    private QuestionAnswerRepository questionAnswerRepository;
    
    @Autowired
    private DeepSeekService deepSeekService;
    
    @Autowired
    private KnowledgeBaseRepository knowledgeBaseRepository;
    
    @Autowired
    private LegalArticleRepository legalArticleRepository;
    
    @Autowired
    private LegalCaseRepository legalCaseRepository;
    
    @Autowired
    private LegalConceptRepository legalConceptRepository;
    
    /**
     * 处理用户问题并生成答案
     */
    @Transactional
    public Map<String, Object> processQuestion(String question, Long userId, String sessionId) {
        Map<String, Object> result = new HashMap<>();
        
        // 1. 问题分类
        String questionType = deepSeekService.classifyQuestion(question);
        
        // 2. 实体识别
        Map<String, List<String>> entities = deepSeekService.extractEntities(question);
        
        // 3. 知识检索
        String context = retrieveKnowledge(question, questionType, entities);
        
        // 4. 生成答案
        String answer = deepSeekService.generateAnswer(question, context);
        
        // 5. 检索相关法条和案例（在可信度评估之前，以便用于评估）
        List<LegalArticle> relatedLaws = findRelatedLaws(question, entities);
        List<LegalCase> relatedCases = findRelatedCases(question, questionType);
        
        // 6. 可信度评估（使用增强版本，传入更多上下文信息）
        Double confidenceScore = deepSeekService.evaluateConfidence(question, answer, context, relatedLaws, relatedCases, entities);
        
        // 7. 保存问答记录
        QuestionAnswer qa = new QuestionAnswer();
        qa.setUserId(userId);
        qa.setQuestion(question);
        qa.setAnswer(answer);
        qa.setQuestionType(questionType);
        qa.setConfidenceScore(confidenceScore);
        qa.setEntities(JSON.toJSONString(entities));
        qa.setRelatedLaws(JSON.toJSONString(relatedLaws.stream()
                .map(la -> formatArticleName(la.getTitle(), la.getArticleNumber()))
                .collect(Collectors.toList())));
        qa.setRelatedCases(JSON.toJSONString(relatedCases.stream()
                .map(lc -> lc.getTitle())
                .collect(Collectors.toList())));
        qa.setSessionId(sessionId);
        qa.setIsFeedback(false);
        qa.setIsFavorite(false);
        qa = questionAnswerRepository.save(qa);
        
        // 8. 构建返回结果
        result.put("id", qa.getId());
        result.put("question", question);
        result.put("answer", answer);
        result.put("questionType", questionType);
        result.put("confidenceScore", confidenceScore);
        result.put("entities", entities);
        result.put("relatedLaws", relatedLaws);
        result.put("relatedCases", relatedCases);
        result.put("sessionId", sessionId);
        
        return result;
    }
    
    private void sendRelatedEvent(List<Map<String, Object>> relatedLaws,
                                  List<Map<String, Object>> relatedCases,
                                  Map<String, List<String>> entities,
                                  PrintWriter writer) {
        Map<String, Object> relatedPayload = new HashMap<>();
        relatedPayload.put("relatedLaws", relatedLaws);
        relatedPayload.put("relatedCases", relatedCases);
        relatedPayload.put("entities", entities);
        writer.write("event: related\n");
        writer.write("data: " + JSON.toJSONString(relatedPayload) + "\n\n");
        writer.flush();
    }
    
    private List<Map<String, Object>> convertArticlesForStream(List<LegalArticle> articles) {
        return articles.stream().map(article -> {
            Map<String, Object> map = new HashMap<>();
            map.put("id", article.getId());
            map.put("title", article.getTitle());
            // 使用清理后的条号，避免重复“第”“条”
            map.put("articleNumber", cleanArticleNumber(article.getArticleNumber()));
            map.put("content", article.getContent());
            return map;
        }).collect(Collectors.toList());
    }
    
    private List<Map<String, Object>> convertCasesForStream(List<LegalCase> cases) {
        return cases.stream().map(caseItem -> {
            Map<String, Object> map = new HashMap<>();
            map.put("id", caseItem.getId());
            map.put("title", caseItem.getTitle());
            map.put("courtName", caseItem.getCourtName());
            map.put("judgeDate", caseItem.getJudgeDate() != null ? caseItem.getJudgeDate().toString() : null);
            map.put("caseType", caseItem.getCaseType());
            map.put("disputePoint", caseItem.getDisputePoint());
            map.put("judgmentResult", caseItem.getJudgmentResult());
            return map;
        }).collect(Collectors.toList());
    }
    
    /**
     * 流式处理用户问题
     */
    @Transactional
    public void processQuestionStream(String question,
                                      Long userId,
                                      String sessionId,
                                      Consumer<String> onChunk,
                                      PrintWriter writer) {
        long startTime = System.currentTimeMillis();
        log.info("开始流式处理问题: {}", question);
        
        // 1. 问题分类
        long step1Start = System.currentTimeMillis();
        String questionType = deepSeekService.classifyQuestion(question);
        log.info("问题分类完成，耗时: {}ms, 类型: {}", System.currentTimeMillis() - step1Start, questionType);
        
        // 2. 实体识别
        long step2Start = System.currentTimeMillis();
        Map<String, List<String>> entities = deepSeekService.extractEntities(question);
        log.info("实体识别完成，耗时: {}ms", System.currentTimeMillis() - step2Start);
        
        // 3. 知识检索
        long step3Start = System.currentTimeMillis();
        String context = retrieveKnowledge(question, questionType, entities);
        log.info("知识检索完成，耗时: {}ms", System.currentTimeMillis() - step3Start);
        
        // 4. 预先检索关联内容并推送到前端
        List<LegalArticle> relatedLaws = findRelatedLaws(question, entities);
        List<LegalCase> relatedCases = findRelatedCases(question, questionType);
        log.info("检索到相关法条: {} 条, 相关案例: {} 条", relatedLaws.size(), relatedCases.size());
        List<Map<String, Object>> relatedLawsPayload = convertArticlesForStream(relatedLaws);
        List<Map<String, Object>> relatedCasesPayload = convertCasesForStream(relatedCases);
        log.info("准备发送相关数据，法条payload: {} 条, 案例payload: {} 条", relatedLawsPayload.size(), relatedCasesPayload.size());
        sendRelatedEvent(relatedLawsPayload, relatedCasesPayload, entities, writer);
        log.info("已发送related事件");
        
        // 5. 流式生成答案
        long step5Start = System.currentTimeMillis();
        StringBuilder fullAnswer = new StringBuilder();
        Consumer<String> streamingConsumer = chunk -> {
            if (chunk != null) {
                fullAnswer.append(chunk);
                if (onChunk != null) {
                    onChunk.accept(chunk);
                }
            }
        };
        String resultAnswer = deepSeekService.generateAnswerStream(question, context, streamingConsumer);
        log.info("流式生成答案完成，耗时: {}ms, 答案长度: {}", System.currentTimeMillis() - step5Start, fullAnswer.length());
        if (resultAnswer != null && resultAnswer.length() > fullAnswer.length()) {
            // generateAnswerStream 返回的完整答案可能包含回调未覆盖的内容
            fullAnswer.setLength(0);
            fullAnswer.append(resultAnswer);
        }
        
        if (fullAnswer.length() == 0) {
            fullAnswer.append("抱歉，暂时无法生成答案，请稍后再试。");
        }
        
        // 6. 可信度评估（使用增强版本，传入更多上下文信息）
        Double confidenceScore = deepSeekService.evaluateConfidence(question, fullAnswer.toString(), context, relatedLaws, relatedCases, entities);
        
        // 7. 保存问答记录
        QuestionAnswer qa = new QuestionAnswer();
        qa.setUserId(userId);
        qa.setQuestion(question);
        qa.setAnswer(fullAnswer.toString());
        qa.setQuestionType(questionType);
        qa.setConfidenceScore(confidenceScore);
        qa.setEntities(JSON.toJSONString(entities));
        qa.setRelatedLaws(JSON.toJSONString(relatedLaws.stream()
                .map(la -> formatArticleName(la.getTitle(), la.getArticleNumber()))
                .collect(Collectors.toList())));
        qa.setRelatedCases(JSON.toJSONString(relatedCases.stream()
                .map(LegalCase::getTitle)
                .collect(Collectors.toList())));
        qa.setSessionId(sessionId);
        qa.setIsFeedback(false);
        qa.setIsFavorite(false);
        qa = questionAnswerRepository.save(qa);
        
        // 8. 从AI答案中提取法条引用，优先显示这些法条
        List<LegalArticle> answerMentionedLaws = extractArticlesFromAnswer(fullAnswer.toString());
        List<Map<String, Object>> finalRelatedLawsPayload;
        if (!answerMentionedLaws.isEmpty()) {
            log.info("从AI答案中提取到 {} 条法条引用", answerMentionedLaws.size());
            // 优先使用答案中提到的法条
            finalRelatedLawsPayload = convertArticlesForStream(answerMentionedLaws);
            // 如果答案中提到的法条不足5条，补充之前匹配到的法条
            if (finalRelatedLawsPayload.size() < 5 && !relatedLaws.isEmpty()) {
                // 获取答案中已包含的法条ID，避免重复
                java.util.Set<Long> mentionedIds = answerMentionedLaws.stream()
                        .map(LegalArticle::getId)
                        .collect(Collectors.toSet());
                // 添加之前匹配到的法条（排除已包含的）
                List<LegalArticle> additionalLaws = relatedLaws.stream()
                        .filter(la -> !mentionedIds.contains(la.getId()))
                        .limit(5 - finalRelatedLawsPayload.size())
                        .collect(Collectors.toList());
                List<Map<String, Object>> additionalPayload = convertArticlesForStream(additionalLaws);
                finalRelatedLawsPayload.addAll(additionalPayload);
            }
        } else {
            // 如果答案中没有提到法条，使用之前匹配到的
            finalRelatedLawsPayload = relatedLawsPayload;
        }
        
        // 9. 推送元数据（使用最终的法条列表）
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("id", qa.getId());
        metadata.put("questionType", questionType);
        metadata.put("confidenceScore", confidenceScore);
        metadata.put("sessionId", sessionId);
        metadata.put("relatedLaws", finalRelatedLawsPayload);
        metadata.put("relatedCases", relatedCasesPayload);
        metadata.put("entities", entities);
        writer.write("event: metadata\n");
        writer.write("data: " + JSON.toJSONString(metadata) + "\n\n");
        writer.flush();
        
        long totalTime = System.currentTimeMillis() - startTime;
        log.info("流式处理问题完成，总耗时: {}ms", totalTime);
    }
    
    /**
     * 知识检索
     */
    private String retrieveKnowledge(String question, String questionType, Map<String, List<String>> entities) {
        StringBuilder context = new StringBuilder();
        
        // 1. 从知识库检索相似问题
        List<KnowledgeBase> similarQAs = knowledgeBaseRepository
                .searchByKeywordOrderByScore(question, org.springframework.data.domain.PageRequest.of(0, 3));
        if (!similarQAs.isEmpty()) {
            context.append("相关问答：\n");
            for (KnowledgeBase kb : similarQAs) {
                context.append("Q: ").append(kb.getQuestion()).append("\n");
                context.append("A: ").append(kb.getAnswer()).append("\n\n");
            }
        }
        
        // 2. 检索相关法条
        List<String> laws = entities.getOrDefault("laws", new ArrayList<>());
        for (String law : laws) {
            List<LegalArticle> articles = legalArticleRepository.searchByKeyword(law);
            if (!articles.isEmpty()) {
                context.append("相关法条：\n");
                for (LegalArticle article : articles.subList(0, Math.min(3, articles.size()))) {
                    context.append(article.getTitle())
                            .append("第").append(article.getArticleNumber())
                            .append("条：").append(article.getContent()).append("\n\n");
                }
            }
        }
        
        // 3. 检索法律概念
        List<String> concepts = entities.getOrDefault("concepts", new ArrayList<>());
        for (String concept : concepts) {
            Optional<LegalConcept> legalConcept = legalConceptRepository.findByName(concept);
            if (legalConcept.isPresent()) {
                context.append("概念定义：").append(legalConcept.get().getName())
                        .append(" - ").append(legalConcept.get().getDefinition()).append("\n\n");
            }
        }
        
        return context.toString();
    }
    
    /**
     * 查找相关法条
     */
    private List<LegalArticle> findRelatedLaws(String question, Map<String, List<String>> entities) {
        List<LegalArticle> laws = new ArrayList<>();
        
        // 1. 根据实体中的法律名称查找
        List<String> lawNames = entities.getOrDefault("laws", new ArrayList<>());
        log.debug("实体中的法律名称: {}", lawNames);
        for (String lawName : lawNames) {
            List<LegalArticle> found = legalArticleRepository.searchByKeyword(lawName);
            log.debug("根据法律名称 '{}' 找到 {} 条法条", lawName, found.size());
            laws.addAll(found);
        }
        
        // 2. 如果实体中没有法律名称，尝试从问题中提取法律相关关键词
        if (laws.isEmpty()) {
            // 提取可能的法律关键词（包含"法"、"条例"等的词）
            java.util.regex.Pattern lawKeywordPattern = java.util.regex.Pattern.compile("([^，。！？、\\s]{2,15}(?:法|条例|规定|办法))");
            java.util.regex.Matcher matcher = lawKeywordPattern.matcher(question);
            java.util.Set<String> keywords = new java.util.HashSet<>();
            while (matcher.find()) {
                String keyword = matcher.group(1);
                if (keyword.length() >= 2 && keyword.length() <= 15) {
                    keywords.add(keyword);
                }
            }
            
            // 如果没有匹配到，使用常见法律关键词列表（按长度从长到短排序，优先匹配更长的）
            if (keywords.isEmpty()) {
                String[] commonKeywords = {
                    // 劳动相关（按长度排序）
                    "劳动合同法", "劳动合同", "劳动法", "劳动", "工资", "加班", "社保", "解除", "违约", "赔偿", "补偿",
                    // 婚姻家庭相关（按长度排序）
                    "婚姻法", "婚姻", "离婚", "结婚", "抚养", "赡养", "继承", "遗嘱", "财产分割",
                    // 合同相关
                    "合同法", "合同", "协议", "违约", "解除",
                    // 程序相关
                    "仲裁", "诉讼", "起诉", "上诉", "申诉",
                    // 其他
                    "侵权", "责任", "权利", "义务", "公司", "企业", "员工", "用人单位"
                };
                // 按长度从长到短排序，优先匹配更长的关键词
                java.util.Arrays.sort(commonKeywords, (a, b) -> Integer.compare(b.length(), a.length()));
                for (String kw : commonKeywords) {
                    if (question.contains(kw)) {
                        keywords.add(kw);
                        // 不停止，继续匹配，因为可能一个问题包含多个关键词
                    }
                }
            }
            
            log.debug("提取到的关键词: {}", keywords);
            for (String keyword : keywords) {
                List<LegalArticle> found = legalArticleRepository.searchByKeyword(keyword);
                laws.addAll(found);
                if (laws.size() >= 10) break; // 找到足够的结果就停止
            }
            log.debug("根据问题关键词找到 {} 条法条", laws.size());
        }
        
        // 3. 去重并限制数量
        List<LegalArticle> result = laws.stream()
                .filter(article -> article.getIsValid() != null && article.getIsValid()) // 只返回有效的法条
                .distinct()
                .limit(5)
                .collect(Collectors.toList());
        log.debug("最终返回 {} 条相关法条", result.size());
        return result;
    }
    
    /**
     * 从AI答案中提取法条引用
     * 支持格式：
     * - 《民法典》第五百七十七条
     * - 民法典第五百七十七条
     * - 《民法典》第577条
     * - 民法典第577条
     */
    private List<LegalArticle> extractArticlesFromAnswer(String answer) {
        List<LegalArticle> articles = new ArrayList<>();
        if (answer == null || answer.isEmpty()) {
            return articles;
        }
        
        // 匹配模式1: 《法律名称》第XXX条 或 《法律名称》第五百XX条
        java.util.regex.Pattern pattern1 = java.util.regex.Pattern.compile("《([^》]+)》[第]?([一二三四五六七八九十百千万\\d]+)条");
        java.util.regex.Matcher matcher1 = pattern1.matcher(answer);
        while (matcher1.find()) {
            String lawTitle = matcher1.group(1);
            String articleNumber = matcher1.group(2);
            // 查找匹配的法条
            List<LegalArticle> found = legalArticleRepository.findByTitleContainingAndIsValidTrue(lawTitle);
            for (LegalArticle article : found) {
                // 检查条号是否匹配（支持中文数字和阿拉伯数字）
                if (isArticleNumberMatch(article.getArticleNumber(), articleNumber)) {
                    if (!articles.contains(article)) {
                        articles.add(article);
                    }
                }
            }
        }
        
        // 匹配模式2: 法律名称第XXX条 或 法律名称第五百XX条（无《》）
        java.util.regex.Pattern pattern2 = java.util.regex.Pattern.compile("([^，。！？、\\s]{2,20}(?:法|条例|规定|办法))[第]?([一二三四五六七八九十百千万\\d]+)条");
        java.util.regex.Matcher matcher2 = pattern2.matcher(answer);
        while (matcher2.find()) {
            String lawTitle = matcher2.group(1);
            String articleNumber = matcher2.group(2);
            // 查找匹配的法条
            List<LegalArticle> found = legalArticleRepository.findByTitleContainingAndIsValidTrue(lawTitle);
            for (LegalArticle article : found) {
                if (isArticleNumberMatch(article.getArticleNumber(), articleNumber)) {
                    if (!articles.contains(article)) {
                        articles.add(article);
                    }
                }
            }
        }
        
        log.debug("从答案中提取到 {} 条法条引用", articles.size());
        return articles.stream().limit(10).collect(Collectors.toList()); // 最多返回10条
    }
    
    /**
     * 去除条号中的冗余字符
     */
    private String cleanArticleNumber(String articleNumber) {
        if (articleNumber == null) {
            return "";
        }
        return articleNumber.replaceAll("[第条\\s]", "").trim();
    }

    /**
     * 格式化法条名称
     * 处理 articleNumber 可能已包含"第"和"条"的情况
     */
    private String formatArticleName(String title, String articleNumber) {
        if (title == null) {
            title = "";
        }
        String cleanNumber = cleanArticleNumber(articleNumber);
        if (cleanNumber.isEmpty()) {
            return title;
        }
        
        // 统一格式：标题 + 第 + 条号 + 条
        return title + "第" + cleanNumber + "条";
    }
    
    /**
     * 检查条号是否匹配（支持中文数字和阿拉伯数字的转换）
     */
    private boolean isArticleNumberMatch(String dbArticleNumber, String answerArticleNumber) {
        if (dbArticleNumber == null || answerArticleNumber == null) {
            return false;
        }
        
        // 去除空格和"第"、"条"等字符
        String dbNum = dbArticleNumber.replaceAll("[第条\\s]", "");
        String ansNum = answerArticleNumber.replaceAll("[第条\\s]", "");
        
        // 直接匹配
        if (dbNum.equals(ansNum)) {
            return true;
        }
        
        // 如果都是阿拉伯数字，直接比较
        if (dbNum.matches("\\d+") && ansNum.matches("\\d+")) {
            return dbNum.equals(ansNum);
        }
        
        // 尝试模糊匹配（包含关系）
        if (dbNum.contains(ansNum) || ansNum.contains(dbNum)) {
            return true;
        }
        
        return false;
    }
    
    /**
     * 查找相关案例
     */
    private List<LegalCase> findRelatedCases(String question, String questionType) {
        List<LegalCase> cases = new ArrayList<>();
        
        // 1. 提取问题中的关键词进行查询
        // 提取可能的关键词（去除停用词）
        String[] stopWords = {"讲讲", "说说", "介绍", "讲解", "说明", "怎么", "如何", "什么", "的", "了", "吗", "呢"};
        String cleanedQuestion = question;
        for (String stopWord : stopWords) {
            cleanedQuestion = cleanedQuestion.replace(stopWord, " ");
        }
        
        // 提取关键词（长度大于1的词）
        String[] keywords = cleanedQuestion.replaceAll("[，。！？、]", " ").split("\\s+");
        java.util.Set<String> searchKeywords = new java.util.HashSet<>();
        for (String keyword : keywords) {
            if (keyword.length() > 1 && keyword.length() <= 10) {
                searchKeywords.add(keyword);
            }
        }
        
        log.debug("提取到的案例搜索关键词: {}", searchKeywords);
        
        // 2. 使用关键词查询案例
        for (String keyword : searchKeywords) {
            List<LegalCase> found = legalCaseRepository.searchByKeyword(keyword);
            cases.addAll(found);
            if (cases.size() >= 5) break; // 找到足够的结果就停止
        }
        log.debug("根据问题关键词找到 {} 个案例", cases.size());
        
        // 3. 如果关键词查找失败，根据问题类型查找
        if (cases.isEmpty() && questionType != null && !questionType.equals("其他")) {
            List<LegalCase> typeCases = legalCaseRepository.findByCaseType(questionType);
            log.debug("根据问题类型 '{}' 找到 {} 个案例", questionType, typeCases.size());
            cases.addAll(typeCases);
        }
        
        // 4. 去重并限制数量
        List<LegalCase> result = cases.stream()
                .distinct()
                .limit(3)
                .collect(Collectors.toList());
        log.debug("最终返回 {} 个相关案例", result.size());
        return result;
    }
    
    /**
     * 获取问答历史
     */
    public Page<QuestionAnswer> getQuestionHistory(Long userId, Pageable pageable) {
        return questionAnswerRepository.findByUserId(userId, pageable);
    }
    
    /**
     * 根据会话ID获取对话历史
     */
    public List<QuestionAnswer> getConversationHistory(String sessionId) {
        return questionAnswerRepository.findBySessionId(sessionId, Sort.by(Sort.Direction.ASC, "createTime"));
    }
    
    /**
     * 提交反馈
     */
    @Transactional
    public void submitFeedback(Long qaId, String feedbackType) {
        QuestionAnswer qa = questionAnswerRepository.findById(qaId)
                .orElseThrow(() -> new RuntimeException("问答记录不存在"));
        qa.setIsFeedback(true);
        qa.setFeedbackType(feedbackType);
        questionAnswerRepository.save(qa);
    }
    
    /**
     * 收藏/取消收藏问答
     */
    @Transactional
    public Boolean toggleFavorite(Long qaId) {
        QuestionAnswer qa = questionAnswerRepository.findById(qaId)
                .orElseThrow(() -> new RuntimeException("问答记录不存在"));
        Boolean newFavoriteStatus = qa.getIsFavorite() == null || !qa.getIsFavorite();
        qa.setIsFavorite(newFavoriteStatus);
        questionAnswerRepository.save(qa);
        return newFavoriteStatus;
    }
    
    /**
     * 获取收藏列表
     */
    public Page<QuestionAnswer> getFavorites(Long userId, Pageable pageable) {
        return questionAnswerRepository.findByUserIdAndIsFavorite(userId, true, pageable);
    }
    
    /**
     * 搜索问答记录
     */
    public Page<QuestionAnswer> searchQuestions(String keyword, Pageable pageable) {
        return questionAnswerRepository.findByQuestionContaining(keyword, pageable);
    }
}

