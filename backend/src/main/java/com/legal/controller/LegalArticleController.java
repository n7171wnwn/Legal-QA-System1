package com.legal.controller;

import com.legal.dto.ApiResponse;
import com.legal.entity.LegalArticle;
import com.legal.service.LegalArticleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/legal/article")
@CrossOrigin
public class LegalArticleController {

    @Autowired
    private LegalArticleService legalArticleService;

    @GetMapping("/search")
    public ApiResponse<Page<LegalArticle>> searchArticles(
            @RequestParam String keyword,
            @RequestParam(defaultValue = "0") Integer page,
            @RequestParam(defaultValue = "10") Integer size) {
        Pageable pageable = PageRequest.of(page, size);
        return ApiResponse.success(legalArticleService.searchArticles(keyword, pageable));
    }

    @GetMapping("/type/{lawType}")
    public ApiResponse<List<LegalArticle>> getArticlesByType(@PathVariable String lawType) {
        return ApiResponse.success(legalArticleService.getArticlesByLawType(lawType));
    }

    @GetMapping("/{id}")
    public ApiResponse<LegalArticle> getArticle(@PathVariable Long id) {
        return legalArticleService.getArticleById(id)
                .map(ApiResponse::success)
                .orElse(ApiResponse.error("法条不存在"));
    }

    @GetMapping("/all")
    public ApiResponse<List<LegalArticle>> getAllArticles() {
        return ApiResponse.success(legalArticleService.getAllValidArticles());
    }

    @GetMapping("/titles")
    public ApiResponse<List<String>> getAllTitles() {
        return ApiResponse.success(legalArticleService.getAllDistinctTitles());
    }

    @GetMapping("/stats")
    public ApiResponse<Object> getStatistics() {
        try {
            Long totalLaws = legalArticleService.getTotalLawCount();
            Long totalArticles = legalArticleService.getTotalArticleCount();
            List<LegalArticle> minorLaws = legalArticleService.getMinorProtectionLaws();

            java.util.Map<String, Object> stats = new java.util.HashMap<>();
            // 处理可能为null的情况
            stats.put("totalLaws", totalLaws != null ? totalLaws : 0L);
            stats.put("totalArticles", totalArticles != null ? totalArticles : 0L);

            // 提取并去重未成年人相关法律名称
            java.util.Set<String> uniqueTitles = new java.util.HashSet<>();
            java.util.List<java.util.Map<String, Object>> minorProtectionLawsList = new java.util.ArrayList<>();
            if (minorLaws != null) {
                for (LegalArticle article : minorLaws) {
                    String title = article.getTitle();
                    if (title != null && !uniqueTitles.contains(title)) {
                        uniqueTitles.add(title);
                        java.util.Map<String, Object> lawInfo = new java.util.HashMap<>();
                        lawInfo.put("title", title);
                        minorProtectionLawsList.add(lawInfo);
                    }
                }
            }
            stats.put("minorProtectionLaws", minorProtectionLawsList);

            return ApiResponse.success(stats);
        } catch (Exception e) {
            e.printStackTrace();
            return ApiResponse.error("获取统计信息失败: " + e.getMessage());
        }
    }
}
