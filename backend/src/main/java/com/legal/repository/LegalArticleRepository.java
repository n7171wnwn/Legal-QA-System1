package com.legal.repository;

import com.legal.entity.LegalArticle;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface LegalArticleRepository extends JpaRepository<LegalArticle, Long> {
    Page<LegalArticle> findByTitleContainingOrContentContaining(String title, String content, Pageable pageable);

    List<LegalArticle> findByLawType(String lawType);

    List<LegalArticle> findByIsValidTrue();

    @Query("SELECT la FROM LegalArticle la WHERE (la.title LIKE CONCAT('%', ?1, '%') OR la.articleNumber LIKE CONCAT('%', ?1, '%') OR la.content LIKE CONCAT('%', ?1, '%')) AND la.isValid = true")
    List<LegalArticle> searchByKeyword(String keyword);

    @Query("SELECT DISTINCT la.title FROM LegalArticle la WHERE la.isValid = :isValid ORDER BY la.title")
    List<String> findAllDistinctTitles(@Param("isValid") Boolean isValid);

    @Query("SELECT COUNT(la) FROM LegalArticle la WHERE la.isValid = :isValid")
    Long countAllValidArticles(@Param("isValid") Boolean isValid);

    @Query("SELECT COUNT(DISTINCT la.title) FROM LegalArticle la WHERE la.isValid = :isValid")
    Long countDistinctTitles(@Param("isValid") Boolean isValid);

    List<LegalArticle> findByTitleContainingAndIsValidTrue(String title);

    /**
     * 获取所有法律列表及其统计信息（按法律名称分组）
     * 返回：title, lawType, publishOrg, count
     * 司法解释类型：统计所有记录
     * 其他类型：只统计"条"的记录，不包含"章"、"节"
     */
    @Query("SELECT la.title, MAX(la.lawType), MAX(la.publishOrg), " +
           "SUM(CASE WHEN la.lawType = '司法解释' THEN 1 " +
           "         WHEN la.articleNumber LIKE '%条%' AND la.articleNumber NOT LIKE '%章%' AND la.articleNumber NOT LIKE '%节%' THEN 1 " +
           "         ELSE 0 END) " +
           "FROM LegalArticle la " +
           "WHERE la.isValid = :isValid " +
           "GROUP BY la.title " +
           "ORDER BY la.title")
    List<Object[]> findAllLawSummaries(@Param("isValid") Boolean isValid);

    /**
     * 根据关键词搜索法律列表（名称匹配）
     * 返回：title, lawType, publishOrg, count
     * 司法解释类型：统计所有记录
     * 其他类型：只统计"条"的记录，不包含"章"、"节"
     */
    @Query("SELECT la.title, MAX(la.lawType), MAX(la.publishOrg), " +
           "SUM(CASE WHEN la.lawType = '司法解释' THEN 1 " +
           "         WHEN la.articleNumber LIKE '%条%' AND la.articleNumber NOT LIKE '%章%' AND la.articleNumber NOT LIKE '%节%' THEN 1 " +
           "         ELSE 0 END) " +
           "FROM LegalArticle la " +
           "WHERE la.isValid = :isValid AND LOWER(la.title) LIKE LOWER(CONCAT('%', :keyword, '%')) " +
           "GROUP BY la.title " +
           "ORDER BY la.title")
    List<Object[]> findLawSummariesByNameMatch(@Param("isValid") Boolean isValid, @Param("keyword") String keyword);

    /**
     * 根据关键词搜索法律列表（内容匹配）
     * 返回：title, lawType, publishOrg, count
     * 司法解释类型：统计所有记录
     * 其他类型：只统计"条"的记录，不包含"章"、"节"
     */
    @Query("SELECT la.title, MAX(la.lawType), MAX(la.publishOrg), " +
           "SUM(CASE WHEN la.lawType = '司法解释' THEN 1 " +
           "         WHEN la.articleNumber LIKE '%条%' AND la.articleNumber NOT LIKE '%章%' AND la.articleNumber NOT LIKE '%节%' THEN 1 " +
           "         ELSE 0 END) " +
           "FROM LegalArticle la " +
           "WHERE la.isValid = :isValid AND LOWER(la.content) LIKE LOWER(CONCAT('%', :keyword, '%')) " +
           "GROUP BY la.title " +
           "ORDER BY la.title")
    List<Object[]> findLawSummariesByContentMatch(@Param("isValid") Boolean isValid, @Param("keyword") String keyword);
}
