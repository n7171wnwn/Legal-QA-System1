package com.legal.controller;

import com.legal.dto.ApiResponse;
import com.legal.entity.*;
import com.legal.repository.QuestionAnswerRepository;
import com.legal.service.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/admin")
@CrossOrigin
public class AdminController {
    
    @Autowired
    private KnowledgeBaseService knowledgeBaseService;
    
    @Autowired
    private LegalArticleService legalArticleService;
    
    @Autowired
    private LegalCaseService legalCaseService;
    
    @Autowired
    private LegalConceptService legalConceptService;
    
    @Autowired
    private QuestionAnswerRepository questionAnswerRepository;
    
    @Autowired
    private com.legal.repository.UserRepository userRepository;
    
    // 知识库管理
    @GetMapping("/knowledge")
    public ApiResponse<Page<KnowledgeBase>> getKnowledge(
            @RequestParam(required = false) String keyword,
            @RequestParam(defaultValue = "0") Integer page,
            @RequestParam(defaultValue = "10") Integer size) {
        Pageable pageable = PageRequest.of(page, size);
        if (keyword != null && !keyword.isEmpty()) {
            return ApiResponse.success(knowledgeBaseService.searchKnowledge(keyword, pageable));
        }
        return ApiResponse.success(knowledgeBaseService.searchKnowledge("", pageable));
    }
    
    @PostMapping("/knowledge")
    public ApiResponse<KnowledgeBase> createKnowledge(@RequestBody KnowledgeBase knowledge) {
        return ApiResponse.success(knowledgeBaseService.saveKnowledge(knowledge));
    }
    
    @PutMapping("/knowledge/{id}")
    public ApiResponse<KnowledgeBase> updateKnowledge(@PathVariable Long id, @RequestBody KnowledgeBase knowledge) {
        knowledge.setId(id);
        return ApiResponse.success(knowledgeBaseService.saveKnowledge(knowledge));
    }
    
    @DeleteMapping("/knowledge/{id}")
    public ApiResponse<?> deleteKnowledge(@PathVariable Long id) {
        knowledgeBaseService.deleteKnowledge(id);
        return ApiResponse.success("删除成功");
    }
    
    // 法条管理
    @PostMapping("/article")
    public ApiResponse<LegalArticle> createArticle(@RequestBody LegalArticle article) {
        return ApiResponse.success(legalArticleService.saveArticle(article));
    }
    
    @PutMapping("/article/{id}")
    public ApiResponse<LegalArticle> updateArticle(@PathVariable Long id, @RequestBody LegalArticle article) {
        article.setId(id);
        return ApiResponse.success(legalArticleService.saveArticle(article));
    }
    
    @DeleteMapping("/article/{id}")
    public ApiResponse<?> deleteArticle(@PathVariable Long id) {
        legalArticleService.deleteArticle(id);
        return ApiResponse.success("删除成功");
    }
    
    // 案例管理
    @PostMapping("/case")
    public ApiResponse<LegalCase> createCase(@RequestBody LegalCase legalCase) {
        return ApiResponse.success(legalCaseService.saveCase(legalCase));
    }
    
    @PutMapping("/case/{id}")
    public ApiResponse<LegalCase> updateCase(@PathVariable Long id, @RequestBody LegalCase legalCase) {
        legalCase.setId(id);
        return ApiResponse.success(legalCaseService.saveCase(legalCase));
    }
    
    @DeleteMapping("/case/{id}")
    public ApiResponse<?> deleteCase(@PathVariable Long id) {
        legalCaseService.deleteCase(id);
        return ApiResponse.success("删除成功");
    }
    
    // 概念管理
    @PostMapping("/concept")
    public ApiResponse<LegalConcept> createConcept(@RequestBody LegalConcept concept) {
        return ApiResponse.success(legalConceptService.saveConcept(concept));
    }
    
    @PutMapping("/concept/{id}")
    public ApiResponse<LegalConcept> updateConcept(@PathVariable Long id, @RequestBody LegalConcept concept) {
        concept.setId(id);
        return ApiResponse.success(legalConceptService.saveConcept(concept));
    }
    
    @DeleteMapping("/concept/{id}")
    public ApiResponse<?> deleteConcept(@PathVariable Long id) {
        legalConceptService.deleteConcept(id);
        return ApiResponse.success("删除成功");
    }
    
    // 统计数据
    @GetMapping("/stats")
    public ApiResponse<Map<String, Object>> getStats() {
        Map<String, Object> stats = new HashMap<>();
        
        // 今日问答数
        Long todayQuestions = questionAnswerRepository.countTodayQuestions();
        stats.put("todayQuestions", todayQuestions != null ? todayQuestions : 0L);
        
        // 总问答数
        Long totalQuestions = questionAnswerRepository.countAllQuestions();
        stats.put("totalQuestions", totalQuestions != null ? totalQuestions : 0L);
        
        // 用户数
        long userCount = userRepository.count();
        stats.put("userCount", userCount);
        
        // 满意度计算
        Long positiveFeedback = questionAnswerRepository.countPositiveFeedback();
        Long totalFeedback = questionAnswerRepository.countTotalFeedback();
        double satisfaction = 0.0;
        if (totalFeedback != null && totalFeedback > 0 && positiveFeedback != null) {
            satisfaction = (positiveFeedback.doubleValue() / totalFeedback.doubleValue()) * 100;
        }
        stats.put("satisfaction", Math.round(satisfaction * 10.0) / 10.0); // 保留一位小数
        
        // 问题分类统计
        List<Object[]> questionTypes = questionAnswerRepository.countByQuestionType();
        List<Map<String, Object>> typeStats = new java.util.ArrayList<>();
        for (Object[] row : questionTypes) {
            Map<String, Object> typeStat = new HashMap<>();
            typeStat.put("type", row[0] != null ? row[0].toString() : "其他");
            typeStat.put("count", row[1]);
            typeStats.add(typeStat);
        }
        stats.put("questionTypes", typeStats);
        
        // 热门问题TOP10
        List<Object[]> hotQuestions = questionAnswerRepository.findHotQuestions();
        List<Map<String, Object>> hotQuestionsList = new java.util.ArrayList<>();
        int limit = Math.min(10, hotQuestions.size());
        for (int i = 0; i < limit; i++) {
            Object[] row = hotQuestions.get(i);
            Map<String, Object> hotQuestion = new HashMap<>();
            String question = row[0] != null ? row[0].toString() : "";
            // 截断过长的问题
            if (question.length() > 100) {
                question = question.substring(0, 100) + "...";
            }
            hotQuestion.put("question", question);
            hotQuestion.put("count", row[1]);
            hotQuestionsList.add(hotQuestion);
        }
        stats.put("hotQuestions", hotQuestionsList);
        
        return ApiResponse.success(stats);
    }
    
    // 问答记录管理
    @GetMapping("/qa")
    public ApiResponse<Page<QuestionAnswer>> getQARecords(
            @RequestParam(required = false) String keyword,
            @RequestParam(defaultValue = "0") Integer page,
            @RequestParam(defaultValue = "10") Integer size) {
        // 按创建时间倒序排列（由近到远）
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createTime"));
        if (keyword != null && !keyword.isEmpty()) {
            return ApiResponse.success(questionAnswerRepository.findByQuestionContaining(keyword, pageable));
        }
        return ApiResponse.success(questionAnswerRepository.findAll(pageable));
    }
    
    @GetMapping("/qa/{id}")
    public ApiResponse<QuestionAnswer> getQARecord(@PathVariable Long id) {
        return ApiResponse.success(questionAnswerRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("问答记录不存在")));
    }
    
    @DeleteMapping("/qa/{id}")
    public ApiResponse<?> deleteQARecord(@PathVariable Long id) {
        if (!questionAnswerRepository.existsById(id)) {
            return ApiResponse.error("问答记录不存在");
        }
        questionAnswerRepository.deleteById(id);
        return ApiResponse.success("删除成功");
    }
    
    @DeleteMapping("/qa/batch")
    public ApiResponse<?> batchDeleteQARecords(@RequestBody List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return ApiResponse.error("请选择要删除的记录");
        }
        questionAnswerRepository.deleteAllById(ids);
        return ApiResponse.success("批量删除成功");
    }
}

