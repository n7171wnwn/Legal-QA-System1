package com.legal.controller;

import com.legal.dto.ApiResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.servlet.http.HttpServletRequest;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/file")
@CrossOrigin
public class FileController {

    @Value("${file.upload.path:./uploads/}")
    private String uploadPath;

    /**
     * 上传文件（合同、证据图片等）
     */
    @PostMapping("/upload")
    public ApiResponse<Map<String, Object>> uploadFile(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "type", required = false, defaultValue = "document") String type,
            HttpServletRequest request) {
        try {
            // 验证文件
            if (file.isEmpty()) {
                return ApiResponse.error("文件不能为空");
            }

            String originalFilename = file.getOriginalFilename();
            if (originalFilename == null || originalFilename.isEmpty()) {
                return ApiResponse.error("文件名不能为空");
            }

            // 获取文件扩展名
            String extension = "";
            int lastDotIndex = originalFilename.lastIndexOf(".");
            if (lastDotIndex > 0) {
                extension = originalFilename.substring(lastDotIndex);
            }

            // 验证文件类型
            String allowedExtensions = "";
            if ("image".equals(type)) {
                // 图片类型：jpg, jpeg, png, gif, bmp, webp
                allowedExtensions = "\\.(jpg|jpeg|png|gif|bmp|webp)$";
                if (!extension.matches(allowedExtensions)) {
                    return ApiResponse.error("图片格式不支持，仅支持：jpg, jpeg, png, gif, bmp, webp");
                }
            } else if ("document".equals(type)) {
                // 文档类型：pdf, doc, docx, txt
                allowedExtensions = "\\.(pdf|doc|docx|txt)$";
                if (!extension.matches(allowedExtensions)) {
                    return ApiResponse.error("文档格式不支持，仅支持：pdf, doc, docx, txt");
                }
            } else {
                // 通用类型：支持图片和文档
                allowedExtensions = "\\.(jpg|jpeg|png|gif|bmp|webp|pdf|doc|docx|txt)$";
                if (!extension.matches(allowedExtensions)) {
                    return ApiResponse.error("文件格式不支持，仅支持：图片（jpg, jpeg, png, gif, bmp, webp）和文档（pdf, doc, docx, txt）");
                }
            }

            // 验证文件大小（10MB）
            long maxSize = 10 * 1024 * 1024; // 10MB
            if (file.getSize() > maxSize) {
                return ApiResponse.error("文件大小不能超过10MB");
            }

            // 创建上传目录
            File uploadDir = new File(uploadPath);
            if (!uploadDir.exists()) {
                uploadDir.mkdirs();
            }

            // 生成唯一文件名
            String filename = UUID.randomUUID().toString() + extension;
            Path filePath = Paths.get(uploadPath + filename);

            // 保存文件
            Files.write(filePath, file.getBytes());

            // 返回文件信息
            Map<String, Object> result = new HashMap<>();
            result.put("filename", filename);
            result.put("originalFilename", originalFilename);
            result.put("url", "/uploads/" + filename);
            result.put("size", file.getSize());
            result.put("type", type);
            result.put("extension", extension.substring(1)); // 去掉点号

            log.info("文件上传成功: {} -> {}", originalFilename, filename);

            return ApiResponse.success("文件上传成功", result);
        } catch (IOException e) {
            log.error("文件上传失败", e);
            return ApiResponse.error("文件上传失败：" + e.getMessage());
        } catch (Exception e) {
            log.error("文件上传失败", e);
            return ApiResponse.error("文件上传失败：" + e.getMessage());
        }
    }
}
