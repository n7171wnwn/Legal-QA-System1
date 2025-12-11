package com.legal.service;

import com.legal.entity.LegalCase;
import com.legal.repository.LegalCaseRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Slf4j
@Service
public class LegalCaseService {
    
    @Autowired
    private LegalCaseRepository legalCaseRepository;
    
    public Page<LegalCase> searchCases(String keyword, Pageable pageable) {
        // 确保只返回 legal_cases 表中的数据（不包含法规）
        Page<LegalCase> result = legalCaseRepository.findByTitleContainingOrContentContaining(keyword, keyword, pageable);
        
        // 记录查询结果，便于调试
        if (result != null && result.getContent() != null) {
            log.debug("案例查询结果: 关键词={}, 总数={}, 当前页数据={}", 
                     keyword, result.getTotalElements(), result.getContent().size());
        }
        
        return result;
    }
    
    public List<LegalCase> getCasesByLawType(String lawType) {
        return legalCaseRepository.findByLawType(lawType);
    }
    
    public List<LegalCase> getCasesByCaseType(String caseType) {
        return legalCaseRepository.findByCaseType(caseType);
    }
    
    public Optional<LegalCase> getCaseById(Long id) {
        return legalCaseRepository.findById(id);
    }
    
    @Transactional
    public LegalCase saveCase(LegalCase legalCase) {
        return legalCaseRepository.save(legalCase);
    }
    
    @Transactional
    public void deleteCase(Long id) {
        legalCaseRepository.deleteById(id);
    }
}

