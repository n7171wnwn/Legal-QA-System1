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
                .map(la -> la.getTitle() + "第" + la.getArticleNumber() + "条")
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
            map.put("articleNumber", article.getArticleNumber());
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
        // 1. 问题分类
        String questionType = deepSeekService.classifyQuestion(question);
        
        // 2. 实体识别
        Map<String, List<String>> entities = deepSeekService.extractEntities(question);
        
        // 3. 知识检索
        String context = retrieveKnowledge(question, questionType, entities);
        
        // 4. 预先检索关联内容并推送到前端
        List<LegalArticle> relatedLaws = findRelatedLaws(question, entities);
        List<LegalCase> relatedCases = findRelatedCases(question, questionType);
        List<Map<String, Object>> relatedLawsPayload = convertArticlesForStream(relatedLaws);
        List<Map<String, Object>> relatedCasesPayload = convertCasesForStream(relatedCases);
        sendRelatedEvent(relatedLawsPayload, relatedCasesPayload, entities, writer);
        
        // 5. 流式生成答案
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
                .map(la -> la.getTitle() + "第" + la.getArticleNumber() + "条")
                .collect(Collectors.toList())));
        qa.setRelatedCases(JSON.toJSONString(relatedCases.stream()
                .map(LegalCase::getTitle)
                .collect(Collectors.toList())));
        qa.setSessionId(sessionId);
        qa.setIsFeedback(false);
        qa.setIsFavorite(false);
        qa = questionAnswerRepository.save(qa);
        
        // 8. 推送元数据
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("id", qa.getId());
        metadata.put("questionType", questionType);
        metadata.put("confidenceScore", confidenceScore);
        metadata.put("sessionId", sessionId);
        metadata.put("relatedLaws", relatedLawsPayload);
        metadata.put("relatedCases", relatedCasesPayload);
        metadata.put("entities", entities);
        writer.write("event: metadata\n");
        writer.write("data: " + JSON.toJSONString(metadata) + "\n\n");
        writer.flush();
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
        
        // 根据实体查找
        List<String> lawNames = entities.getOrDefault("laws", new ArrayList<>());
        for (String lawName : lawNames) {
            laws.addAll(legalArticleRepository.searchByKeyword(lawName));
        }
        
        // 根据问题关键词查找
        if (laws.isEmpty()) {
            laws.addAll(legalArticleRepository.searchByKeyword(question));
        }
        
        return laws.stream().distinct().limit(5).collect(Collectors.toList());
    }
    
    /**
     * 查找相关案例
     */
    private List<LegalCase> findRelatedCases(String question, String questionType) {
        List<LegalCase> cases = legalCaseRepository.searchByKeyword(question);
        if (cases.isEmpty() && questionType != null) {
            cases = legalCaseRepository.findByCaseType(questionType);
        }
        return cases.stream().distinct().limit(3).collect(Collectors.toList());
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

