<template>
  <div class="home">
    <NavBar />
    <div class="home-content">
      <div class="hero-section">
        <h1 class="hero-title">智慧司法问答系统</h1>
        <p class="hero-subtitle">基于AI技术的专业法律咨询服务</p>
        <div class="search-box">
          <el-input
            v-model="question"
            placeholder="请输入您的法律问题，例如：'劳动合同违约如何赔偿？'"
            size="large"
            @keyup.enter.native="handleAsk"
            class="question-input"
          >
            <el-button
              slot="append"
              icon="el-icon-search"
              class="cta-button"
              @click="handleAsk"
            >提问</el-button>
          </el-input>
          <div class="search-actions">
            <el-upload
              ref="upload"
              :http-request="customUpload"
              :before-upload="beforeUpload"
              :show-file-list="false"
              accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.bmp,.webp"
            >
              <el-button icon="el-icon-upload" circle title="上传文件（合同、证据图片等）"></el-button>
            </el-upload>
          </div>
        </div>
      </div>

      <div class="quick-actions">
        <el-row :gutter="20">
          <el-col :span="6" v-for="action in quickActions" :key="action.key">
            <div class="action-card" @click="handleQuickAction(action)">
              <i :class="action.icon" class="action-icon"></i>
              <h3>{{ action.title }}</h3>
              <p>{{ action.desc }}</p>
            </div>
          </el-col>
        </el-row>
      </div>

      <div class="popular-questions">
        <h2>热门问题</h2>
        <el-row :gutter="20">
          <el-col :span="12" v-for="(q, index) in popularQuestions" :key="index">
            <div class="question-item" @click="handleQuestionClick(q)">
              <i class="el-icon-question"></i>
              <span>{{ q }}</span>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 文件上传后的问题输入对话框 -->
    <el-dialog
      title="文件上传成功！请输入您的问题"
      :visible.sync="questionDialogVisible"
      width="600px"
      :close-on-click-modal="false"
      :close-on-press-escape="true"
      @close="handleDialogClose"
    >
      <div class="file-upload-dialog">
        <div class="file-info">
          <i :class="uploadedFileInfo && uploadedFileInfo.type === 'image' ? 'el-icon-picture' : 'el-icon-document'" class="file-icon"></i>
          <span class="file-name">{{ uploadedFileInfo ? uploadedFileInfo.originalFilename : '' }}</span>
        </div>
        <div class="question-label">
          <i class="el-icon-chat-line-round"></i>
          <span>您想针对这个文件咨询什么问题？</span>
        </div>
        <el-input
          v-model="fileQuestion"
          type="textarea"
          :rows="5"
          :placeholder="questionPlaceholder"
          class="question-textarea"
        ></el-input>
        <div class="dialog-tips">
          <i class="el-icon-info"></i>
          <span>输入具体问题可以帮助AI更准确地分析文件内容</span>
        </div>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button @click="handleSkipQuestion">跳过，使用默认问题</el-button>
        <el-button type="primary" @click="handleConfirmQuestion" :disabled="!fileQuestion.trim()">确认并开始分析</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import NavBar from '@/components/NavBar.vue'
import { uploadFile, getStats } from '@/api/api'
import store from '@/store'

export default {
  name: 'Home',
  components: {
    NavBar
  },
  data() {
    return {
      question: '',
      questionDialogVisible: false,
      fileQuestion: '',
      uploadedFileInfo: null,
      questionPlaceholder: '请输入您的问题，例如：\n\n• 这份合同有哪些风险点？\n• 这张证据图片能证明什么？\n• 这份文档中的条款是否合法？\n• 这份合同是否符合法律规定？\n\n提示：如果不输入问题，可以点击跳过按钮使用默认问题进行分析。',
      quickActions: [
        {
          key: 'article',
          title: '法条查询',
          desc: '查询法律条文',
          icon: 'el-icon-document',
          route: '/knowledge?type=article'
        },
        {
          key: 'concept',
          title: '概念百科',
          desc: '法律概念定义',
          icon: 'el-icon-info',
          route: '/knowledge?type=concept'
        },
        {
          key: 'procedure',
          title: '程序指南',
          desc: '司法程序咨询',
          icon: 'el-icon-guide',
          route: '/chat'
        },
        {
          key: 'case',
          title: '案例参考',
          desc: '案例分析问答',
          icon: 'el-icon-folder-opened',
          route: '/knowledge?type=case'
        }
      ],
      // 默认补充用的热门问题
      popularFallback: [
        '劳动合同违约如何赔偿？',
        '交通事故责任如何认定？',
        '离婚财产如何分割？',
        '欠款不还怎么办？',
        '工伤认定需要哪些材料？',
        '房屋买卖合同违约如何处理？'
      ],
      popularQuestions: []
    }
  },
  created() {
    this.loadPopularQuestions()
  },
  methods: {
    async loadPopularQuestions() {
      const normalize = (q) => {
        if (!q) return ''
        return q
          .toLowerCase()
          .replace(/[^\u4e00-\u9fa50-9a-z]+/g, '') // 去掉标点和空白
      }
      const isSimilar = (n, seenArr) => {
        if (!n) return true
        return seenArr.some((item) => item.includes(n) || n.includes(item))
      }

      const seen = []
      const result = []

      try {
        const res = await getStats()
        const hot = res && res.data && res.data.hotQuestions ? res.data.hotQuestions : []
        hot.forEach((item) => {
          const q = typeof item === 'string' ? item : item.question
          const norm = normalize(q)
          if (!q || !norm) return
          if (isSimilar(norm, seen)) return
          seen.push(norm)
          result.push(q)
        })
      } catch (e) {
        console.warn('获取热门问题失败，使用默认列表', e)
      }

      // 不足时，用写死的补足
      this.popularFallback.forEach((q) => {
        const norm = normalize(q)
        if (!norm) return
        if (isSimilar(norm, seen)) return
        if (result.length >= 6) return
        seen.push(norm)
        result.push(q)
      })

      this.popularQuestions = result.length > 0 ? result : this.popularFallback
    },
    handleAsk() {
      if (!this.question.trim()) {
        this.$message.warning('请输入问题')
        return
      }
      this.$router.push({
        path: '/chat',
        query: { question: this.question }
      })
    },
    handleQuickAction(action) {
      this.$router.push(action.route)
    },
    handleQuestionClick(question) {
      this.$router.push({
        path: '/chat',
        query: { question }
      })
    },
    beforeUpload(file) {
      // 检查文件类型
      const isImage = /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(file.name)
      const isDocument = /\.(pdf|doc|docx|txt)$/i.test(file.name)
      
      if (!isImage && !isDocument) {
        this.$message.error('文件格式不支持！仅支持图片（jpg, jpeg, png, gif, bmp, webp）和文档（pdf, doc, docx, txt）')
        return false
      }
      
      // 检查文件大小（10MB）
      const isLt10M = file.size / 1024 / 1024 < 10
      if (!isLt10M) {
        this.$message.error('文件大小不能超过 10MB！')
        return false
      }
      
      return true
    },
    async customUpload(options) {
      try {
        const file = options.file
        // 根据文件类型自动判断
        const isImage = /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(file.name)
        const type = isImage ? 'image' : 'document'
        
        const response = await uploadFile(file, type)
        
        if (response.code === 200) {
          this.$message.success('文件上传成功！')
          const fileInfo = response.data
          console.log('上传的文件信息:', fileInfo)
          
          // 保存文件信息并显示问题输入对话框
          this.uploadedFileInfo = fileInfo
          this.fileQuestion = ''
          this.questionDialogVisible = true
        } else {
          this.$message.error(response.message || '上传失败')
        }
      } catch (error) {
        console.error('上传错误:', error)
        this.$message.error('文件上传失败，请重试')
      }
    },
    handleConfirmQuestion() {
      if (!this.fileQuestion.trim()) {
        this.$message.warning('请输入问题')
        return
      }
      this.navigateToChat(this.fileQuestion.trim())
    },
    handleSkipQuestion() {
      // 使用默认问题
      const defaultQuestion = `请帮我分析一下这个${this.uploadedFileInfo.type === 'image' ? '图片' : '文档'}：${this.uploadedFileInfo.originalFilename}`
      this.navigateToChat(defaultQuestion)
    },
    navigateToChat(question) {
      // 关闭对话框
      this.questionDialogVisible = false
      
      // 跳转到聊天页面，并携带文件信息和问题
      this.$router.push({
        path: '/chat',
        query: { 
          fileUrl: this.uploadedFileInfo.url,
          fileName: this.uploadedFileInfo.originalFilename,
          fileType: this.uploadedFileInfo.type,
          question: question
        }
      })
      
      // 清空临时数据
      this.uploadedFileInfo = null
      this.fileQuestion = ''
    },
    handleDialogClose() {
      // 对话框关闭时清空数据
      this.uploadedFileInfo = null
      this.fileQuestion = ''
    }
  }
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: linear-gradient(to bottom, var(--secondary-color), #f5f5f5);
}

.home-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.hero-section {
  text-align: center;
  padding: 60px 0;
}

.hero-title {
  font-size: 48px;
  color: var(--primary-color);
  margin-bottom: 20px;
  font-weight: bold;
}

.hero-subtitle {
  font-size: 20px;
  color: #666;
  margin-bottom: 40px;
}

.search-box {
  max-width: 800px;
  margin: 0 auto;
}

.question-input {
  margin-bottom: 20px;
}

.search-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.quick-actions {
  margin: 60px 0;
}

.action-card {
  background: white;
  border-radius: 8px;
  padding: 30px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.action-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.action-icon {
  font-size: 48px;
  color: var(--primary-color);
  margin-bottom: 20px;
}

.action-card h3 {
  font-size: 20px;
  color: #333;
  margin-bottom: 10px;
}

.action-card p {
  color: #999;
  font-size: 14px;
}

.popular-questions {
  margin-top: 60px;
  background: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.popular-questions h2 {
  font-size: 24px;
  color: #333;
  margin-bottom: 20px;
}

.question-item {
  padding: 15px;
  margin-bottom: 10px;
  background: #f9f9f9;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
}

.question-item:hover {
  background: var(--secondary-color);
  color: var(--primary-color);
}

.question-item i {
  margin-right: 10px;
  color: var(--primary-color);
}

.cta-button {
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.25);
}

.cta-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(64, 158, 255, 0.35);
}

.cta-button:active {
  transform: translateY(0);
  box-shadow: 0 3px 10px rgba(64, 158, 255, 0.3);
}

/* 文件上传对话框样式 */
.file-upload-dialog {
  padding: 10px 0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 4px;
  margin-bottom: 20px;
}

.file-icon {
  font-size: 24px;
  color: var(--primary-color);
}

.file-name {
  flex: 1;
  font-size: 14px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.question-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.question-label i {
  color: var(--primary-color);
  font-size: 16px;
}

.question-textarea {
  margin-bottom: 10px;
}

.dialog-tips {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #999;
  margin-top: 10px;
}

.dialog-tips i {
  color: #409eff;
}
</style>

