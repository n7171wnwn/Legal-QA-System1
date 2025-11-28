package com.legal.controller;

import com.legal.dto.ApiResponse;
import com.legal.dto.LoginRequest;
import com.legal.dto.RegisterRequest;
import com.legal.entity.User;
import com.legal.service.UserService;
import com.legal.util.JwtUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
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
@RequestMapping("/auth")
@CrossOrigin
public class AuthController {
    
    @Autowired
    private UserService userService;
    
    @Autowired
    private JwtUtil jwtUtil;
    
    @Autowired
    private BCryptPasswordEncoder passwordEncoder;
    
    @Value("${file.upload.path:./uploads/}")
    private String uploadPath;
    
    @PostMapping("/register")
    public ApiResponse<Map<String, Object>> register(@RequestBody RegisterRequest request) {
        try {
            if (userService.existsByUsername(request.getUsername())) {
                return ApiResponse.error("用户名已存在");
            }
            
            User user = new User();
            user.setUsername(request.getUsername());
            user.setPassword(passwordEncoder.encode(request.getPassword()));
            user.setEmail(request.getEmail());
            user.setPhone(request.getPhone());
            user.setNickname(request.getNickname());
            user.setUserType(0); // 普通用户
            
            user = userService.saveUser(user);
            
            String token = jwtUtil.generateToken(user.getUsername(), user.getId());
            
            Map<String, Object> result = new HashMap<>();
            result.put("token", token);
            result.put("user", user);
            
            return ApiResponse.success("注册成功", result);
        } catch (Exception e) {
            log.error("注册失败", e);
            return ApiResponse.error("注册失败：" + e.getMessage());
        }
    }
    
    @PostMapping("/login")
    public ApiResponse<Map<String, Object>> login(@RequestBody LoginRequest request) {
        try {
            User user = userService.findByUsername(request.getUsername())
                    .orElseThrow(() -> new RuntimeException("用户不存在"));
            
            if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
                return ApiResponse.error("密码错误");
            }
            
            String token = jwtUtil.generateToken(user.getUsername(), user.getId());
            
            Map<String, Object> result = new HashMap<>();
            result.put("token", token);
            result.put("user", user);
            
            return ApiResponse.success("登录成功", result);
        } catch (Exception e) {
            log.error("登录失败", e);
            return ApiResponse.error("登录失败：" + e.getMessage());
        }
    }
    
    /**
     * 上传头像
     */
    @PostMapping("/avatar")
    public ApiResponse<Map<String, String>> uploadAvatar(
            @RequestParam("file") MultipartFile file,
            HttpServletRequest request) {
        try {
            String token = request.getHeader("Authorization");
            if (token == null || !token.startsWith("Bearer ")) {
                return ApiResponse.error(401, "未登录");
            }
            
            token = token.substring(7);
            if (!jwtUtil.validateToken(token)) {
                return ApiResponse.error(401, "Token无效");
            }
            
            Long userId = jwtUtil.getUserIdFromToken(token);
            User user = userService.findById(userId)
                    .orElseThrow(() -> new RuntimeException("用户不存在"));
            
            // 验证文件类型
            String originalFilename = file.getOriginalFilename();
            if (originalFilename == null || originalFilename.isEmpty()) {
                return ApiResponse.error("文件名不能为空");
            }
            
            String extension = originalFilename.substring(originalFilename.lastIndexOf("."));
            if (!extension.matches("\\.(jpg|jpeg|png|gif|bmp)$")) {
                return ApiResponse.error("只支持图片格式：jpg, jpeg, png, gif, bmp");
            }
            
            // 验证文件大小（5MB）
            if (file.getSize() > 5 * 1024 * 1024) {
                return ApiResponse.error("文件大小不能超过5MB");
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
            
            // 删除旧头像（如果存在）
            if (user.getAvatar() != null && !user.getAvatar().isEmpty()) {
                // 从路径中提取文件名（如果存储的是完整路径）
                String oldAvatar = user.getAvatar();
                if (oldAvatar.contains("/")) {
                    oldAvatar = oldAvatar.substring(oldAvatar.lastIndexOf("/") + 1);
                }
                String oldAvatarPath = uploadPath + oldAvatar;
                File oldFile = new File(oldAvatarPath);
                if (oldFile.exists() && oldFile.isFile()) {
                    oldFile.delete();
                }
            }
            
            // 更新用户头像
            user.setAvatar(filename);
            userService.saveUser(user);
            
            Map<String, String> result = new HashMap<>();
            result.put("avatar", "/uploads/" + filename);
            
            return ApiResponse.success("头像上传成功", result);
        } catch (IOException e) {
            log.error("头像上传失败", e);
            return ApiResponse.error("头像上传失败：" + e.getMessage());
        } catch (Exception e) {
            log.error("头像上传失败", e);
            return ApiResponse.error("头像上传失败：" + e.getMessage());
        }
    }
    
    /**
     * 更新用户信息
     */
    @PutMapping("/profile")
    public ApiResponse<User> updateProfile(
            @RequestBody Map<String, Object> requestData,
            HttpServletRequest request) {
        try {
            String token = request.getHeader("Authorization");
            if (token == null || !token.startsWith("Bearer ")) {
                return ApiResponse.error(401, "未登录");
            }
            
            token = token.substring(7);
            if (!jwtUtil.validateToken(token)) {
                return ApiResponse.error(401, "Token无效");
            }
            
            Long userId = jwtUtil.getUserIdFromToken(token);
            User user = userService.findById(userId)
                    .orElseThrow(() -> new RuntimeException("用户不存在"));
            
            // 更新用户信息
            if (requestData.containsKey("nickname")) {
                user.setNickname((String) requestData.get("nickname"));
            }
            if (requestData.containsKey("email")) {
                user.setEmail((String) requestData.get("email"));
            }
            if (requestData.containsKey("phone")) {
                user.setPhone((String) requestData.get("phone"));
            }
            
            user = userService.saveUser(user);
            
            return ApiResponse.success("更新成功", user);
        } catch (Exception e) {
            log.error("更新用户信息失败", e);
            return ApiResponse.error("更新用户信息失败：" + e.getMessage());
        }
    }
}

