package com.legal.service;

import com.legal.dto.LawSummary;
import com.legal.entity.LegalArticle;
import com.legal.repository.LegalArticleRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
public class LegalArticleService {

    @Autowired
    private LegalArticleRepository legalArticleRepository;

    public Page<LegalArticle> searchArticles(String keyword, Pageable pageable) {
        return legalArticleRepository.findByTitleContainingOrContentContaining(keyword, keyword, pageable);
    }

    public List<LegalArticle> getArticlesByLawType(String lawType) {
        return legalArticleRepository.findByLawType(lawType);
    }

    public List<LegalArticle> getAllValidArticles() {
        return legalArticleRepository.findByIsValidTrue();
    }

    public Optional<LegalArticle> getArticleById(Long id) {
        return legalArticleRepository.findById(id);
    }

    @Transactional
    public LegalArticle saveArticle(LegalArticle article) {
        return legalArticleRepository.save(article);
    }

    @Transactional
    public void deleteArticle(Long id) {
        legalArticleRepository.deleteById(id);
    }

    public List<String> getAllDistinctTitles() {
        return legalArticleRepository.findAllDistinctTitles(true);
    }

    public Long getTotalArticleCount() {
        return legalArticleRepository.countAllValidArticles(true);
    }

    public Long getTotalLawCount() {
        return legalArticleRepository.countDistinctTitles(true);
    }

    public List<LegalArticle> getMinorProtectionLaws() {
        return legalArticleRepository.findByTitleContainingAndIsValidTrue("未成年");
    }

    /**
     * 获取所有法律列表及其统计信息
     */
    public List<LawSummary> getAllLawSummaries() {
        List<Object[]> results = legalArticleRepository.findAllLawSummaries(true);
        return convertToLawSummaries(results);
    }

    /**
     * 根据关键词搜索法律列表（名称匹配）
     */
    public List<LawSummary> getLawSummariesByNameMatch(String keyword) {
        if (keyword == null || keyword.trim().isEmpty()) {
            return getAllLawSummaries();
        }
        List<Object[]> results = legalArticleRepository.findLawSummariesByNameMatch(true, keyword.trim());
        return convertToLawSummaries(results);
    }

    /**
     * 根据关键词搜索法律列表（内容匹配）
     */
    public List<LawSummary> getLawSummariesByContentMatch(String keyword) {
        if (keyword == null || keyword.trim().isEmpty()) {
            return getAllLawSummaries();
        }
        List<Object[]> results = legalArticleRepository.findLawSummariesByContentMatch(true, keyword.trim());
        return convertToLawSummaries(results);
    }

    /**
     * 将查询结果 Object[] 转换为 LawSummary
     * Object[] 格式: [title, lawType, publishOrg, count]
     */
    private List<LawSummary> convertToLawSummaries(List<Object[]> results) {
        return results.stream()
                .map(row -> {
                    String title = (String) row[0];
                    String lawType = (String) row[1];
                    String publishOrg = (String) row[2];
                    Long count = ((Number) row[3]).longValue();
                    return new LawSummary(title, lawType, publishOrg, count);
                })
                .collect(Collectors.toList());
    }
}