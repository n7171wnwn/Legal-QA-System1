package com.legal.repository;

import com.legal.entity.QuestionAnswer;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface QuestionAnswerRepository extends JpaRepository<QuestionAnswer, Long> {
    Page<QuestionAnswer> findByUserId(Long userId, Pageable pageable);
    List<QuestionAnswer> findBySessionId(String sessionId, Sort sort);
    Page<QuestionAnswer> findByQuestionContaining(String keyword, Pageable pageable);
    Page<QuestionAnswer> findByUserIdAndIsFavorite(Long userId, Boolean isFavorite, Pageable pageable);
    
    @Query("SELECT COUNT(q) FROM QuestionAnswer q WHERE DATE(q.createTime) = CURRENT_DATE")
    Long countTodayQuestions();
    
    @Query("SELECT q.questionType, COUNT(q) FROM QuestionAnswer q GROUP BY q.questionType")
    List<Object[]> countByQuestionType();
    
    @Query("SELECT COUNT(q) FROM QuestionAnswer q")
    Long countAllQuestions();
    
    @Query(value = "SELECT question, COUNT(*) as cnt FROM question_answers GROUP BY question ORDER BY cnt DESC LIMIT 10", nativeQuery = true)
    List<Object[]> findHotQuestions();
    
    @Query("SELECT COUNT(q) FROM QuestionAnswer q WHERE q.isFeedback = true AND q.feedbackType = 'positive'")
    Long countPositiveFeedback();
    
    @Query("SELECT COUNT(q) FROM QuestionAnswer q WHERE q.isFeedback = true")
    Long countTotalFeedback();
}

