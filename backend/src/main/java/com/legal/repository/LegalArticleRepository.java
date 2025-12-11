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
}
