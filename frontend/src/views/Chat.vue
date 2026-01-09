<template>
  <div class="chat">
    <NavBar />
    <div class="chat-container">
      <div class="chat-main">
        <div class="chat-messages" ref="messagesContainer">
          <div
            v-for="(message, index) in messages"
            :key="index"
            :class="['message', message.type]"
          >
            <div class="message-content" v-if="message.type === 'user'">
              <div class="message-bubble user-bubble">
                {{ message.content }}
              </div>
            </div>
            <div class="message-content" v-else>
              <div class="message-bubble bot-bubble">
                <div class="bot-loading-indicator" v-if="message.isLoading || message.isStreaming">
                  <i class="el-icon-loading"></i>
                  <span>{{ message.isStreaming ? '正在生成回答...' : '正在思考中...' }}</span>
                  <el-button 
                    v-if="message.isStreaming && currentRequestController" 
                    size="mini" 
                    type="danger" 
                    icon="el-icon-close" 
                    @click="stopStreaming(message)"
                    style="margin-left: 10px;"
                  >停止生成</el-button>
                </div>
                <div class="confidence-indicator" v-if="message.confidenceScore">
                  <span class="confidence-label">可信度：</span>
                  <el-progress
                    :percentage="message.confidenceScore * 100"
                    :color="getConfidenceColor(message.confidenceScore)"
                    :stroke-width="8"
                  ></el-progress>
                </div>
                <div
                  v-if="message.answer"
                  class="answer-content"
                  v-html="formatAnswer(message.answer, message.isStreaming, message.id)"
                ></div>
                <div class="message-actions">
                  <el-button size="mini" icon="el-icon-thumb" @click="handleFeedback(message.id, 'positive')">有用</el-button>
                  <el-button size="mini" icon="el-icon-close" @click="handleFeedback(message.id, 'negative')">无用</el-button>
                  <el-button size="mini" icon="el-icon-star-off" @click="handleCollect(message)">收藏</el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="chat-input-area">
          <div v-if="uploadedFile" class="uploaded-file-info">
            <div class="file-info-left">
              <i :class="uploadedFile.type === 'image' ? 'el-icon-picture' : 'el-icon-document'"></i>
              <div class="file-details">
                <span class="file-name">{{ uploadedFile.fileName }}</span>
                <span class="file-hint">正在分析此文件，您可以继续针对此文件提问</span>
              </div>
            </div>
            <el-button size="mini" type="text" icon="el-icon-close" @click="handleRemoveFile" title="移除文件"></el-button>
          </div>
          <div class="input-wrapper">
            <el-upload
              ref="chatUpload"
              action=""
              :http-request="handleChatUpload"
              :before-upload="beforeChatUpload"
              :show-file-list="false"
              accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.bmp,.webp"
              class="upload-btn-wrapper"
            >
              <el-button 
                size="small" 
                icon="el-icon-upload" 
                :disabled="loading || uploading" 
                :loading="uploading"
                circle
                class="upload-btn"
                title="上传文件（合同、证据图片等）"
              ></el-button>
            </el-upload>
            <el-input
              v-model="currentQuestion"
              type="textarea"
              :rows="3"
              :placeholder="uploadedFile ? '请输入您的问题，将自动关联当前文件...（按Enter发送，Shift+Enter换行）' : '请输入您的问题...（按Enter发送，Shift+Enter换行）'"
              :disabled="loading"
              @keydown.enter.native="handleKeyDown"
              class="question-textarea-input"
            ></el-input>
          </div>
          <div class="input-actions">
            <el-button @click="handleSend" type="primary" :loading="loading" :disabled="loading">发送</el-button>
            <el-button @click="handleClear" :disabled="loading">清空</el-button>
          </div>
        </div>
      </div>
      <div class="chat-sidebar">
        <div class="sidebar-section">
          <h3>📚 参考法条</h3>
          <div v-if="currentRelatedLaws.length > 0">
            <div
              v-for="(law, index) in currentRelatedLaws"
              :key="index"
              class="law-item"
              @click="showLawDetail(law)"
            >
              {{ law.title }}<span v-if="formatArticleNumber(law.articleNumber)"> {{ formatArticleNumber(law.articleNumber) }}</span>
            </div>
          </div>
          <div v-else class="empty-state">暂无相关法条</div>
        </div>
        <div class="sidebar-section">
          <h3>⚖️ 相似案例</h3>
          <div v-if="currentRelatedCases.length > 0">
            <div
              v-for="(caseItem, index) in currentRelatedCases"
              :key="index"
              class="case-item"
              @click="showCaseDetail(caseItem)"
            >
              <div class="case-title">{{ caseItem.title }}</div>
              <div class="case-meta">{{ caseItem.courtName }} · {{ formatDate(caseItem.judgeDate) }}</div>
            </div>
          </div>
          <div v-else class="empty-state">暂无相关案例</div>
        </div>
        <div class="sidebar-section">
          <h3>🔍 识别实体</h3>
          <div v-if="currentEntities && Object.keys(currentEntities).length > 0">
            <div v-for="(items, key) in currentEntities" :key="key" v-if="items && items.length > 0">
              <div class="entity-label">{{ getEntityLabel(key) }}</div>
              <el-tag
                v-for="(item, idx) in items"
                :key="idx"
                size="mini"
                :type="getEntityTagType(key)"
                class="entity-tag"
              >
                {{ formatEntityItem(item) }}
              </el-tag>
            </div>
          </div>
          <div v-else class="empty-state">暂无识别实体</div>
        </div>
      </div>
    </div>

    <el-dialog title="法条详情" :visible.sync="lawDialogVisible" width="60%">
      <div v-if="selectedLaw">
        <h3>{{ selectedLaw.title }}<span v-if="formatArticleNumber(selectedLaw.articleNumber)"> {{ formatArticleNumber(selectedLaw.articleNumber) }}</span></h3>
        <p>{{ cleanLawContent(selectedLaw.content) }}</p>
      </div>
    </el-dialog>

    <el-dialog title="案例详情" :visible.sync="caseDialogVisible" width="60%">
      <div v-if="selectedCase">
        <h3>{{ selectedCase.title }}</h3>
        <p><strong>案由：</strong>{{ selectedCase.caseType }}</p>
        <p><strong>审理法院：</strong>{{ selectedCase.courtName }}</p>
        <p><strong>核心争议点：</strong>{{ selectedCase.disputePoint }}</p>
        <p><strong>判决结果：</strong>{{ selectedCase.judgmentResult }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import NavBar from '@/components/NavBar.vue'
import { askQuestion, askQuestionStream, submitFeedback, getConversationHistory, toggleFavorite, uploadFile } from '@/api/api'
import md from '@/utils/markdownRenderer'

export default {
  name: 'Chat',
  components: {
    NavBar
  },
  data() {
    return {
      currentQuestion: '',
      messages: [],
      loading: false,
      sessionId: 'session_' + Date.now(),
      currentRelatedLaws: [],
      currentRelatedCases: [],
      currentEntities: {},
      lawDialogVisible: false,
      caseDialogVisible: false,
      selectedLaw: null,
      selectedCase: null,
      currentRequestController: null,
      uploadedFile: null, // 存储上传的文件信息
      uploading: false, // 文件上传中状态
      markdownParseTimers: {}, // 存储每个消息的防抖定时器
      markdownCache: {} // 缓存已解析的Markdown内容
    }
  },
  async mounted() {
    // 如果传递了文件信息，保存文件信息
    if (this.$route.query.fileUrl && this.$route.query.fileName) {
      this.uploadedFile = {
        url: this.$route.query.fileUrl,
        fileName: this.$route.query.fileName,
        type: this.$route.query.fileType || 'document'
      }
    }
    
    // 如果传递了sessionId，加载历史对话记录
    if (this.$route.query.sessionId) {
      await this.loadConversationHistory(this.$route.query.sessionId)
    } else if (this.$route.query.question) {
      // 如果传递了question，自动发送（用于新提问）
      this.currentQuestion = this.$route.query.question
      this.handleSend()
    }
  },
  beforeDestroy() {
    // 清理所有防抖定时器
    Object.values(this.markdownParseTimers).forEach(timer => {
      if (timer) clearTimeout(timer)
    })
    this.markdownParseTimers = {}
    // 清理缓存
    this.markdownCache = {}
  },
  methods: {
    handleKeyDown(event) {
      // 如果按的是Enter键且没有按Shift键，则提交
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault() // 阻止默认换行行为
        this.handleSend()
      }
      // 如果按的是Shift+Enter，允许默认行为（换行）
    },
    async handleSend() {
      if (!this.currentQuestion.trim()) {
        this.$message.warning('请输入问题')
        return
      }
      if (this.loading) {
        this.$message.warning('请等待当前回答完成')
        return
      }

      // 如果有上传的文件，将文件信息添加到问题中
      let questionText = this.currentQuestion
      if (this.uploadedFile) {
        questionText = `${this.currentQuestion}\n\n[附件：${this.uploadedFile.fileName} - ${this.uploadedFile.url}]`
      }

      const userMessage = {
        type: 'user',
        content: this.currentQuestion
      }
      this.messages.push(userMessage)

      const question = questionText
      this.currentQuestion = ''
      this.loading = true
      this.resetSidebar()

      try {
        const botMessage = {
          type: 'bot',
          answer: '',
          confidenceScore: null,
          questionType: null,
          id: null,
          isLoading: true,
          isStreaming: false
        }
        this.messages.push(botMessage)
        this.$nextTick(this.scrollToBottom)

        try {
          botMessage.isStreaming = true
          await this.startStreamRequest(question, botMessage)
        } catch (streamError) {
          if (streamError && streamError.message === 'STREAM_TIMEOUT') {
            console.warn('流式响应超时，回退到普通模式')
          } else if (this.isAbortError(streamError)) {
            throw streamError
          } else {
            console.warn('流式请求失败，回退到普通模式', streamError)
          }
          botMessage.isStreaming = false
          botMessage.isLoading = true
          await this.fetchStandardAnswer(question, botMessage)
          this.$message.warning('流式输出暂不可用，已切换为普通模式')
        }
      } catch (error) {
        const pendingBot = [...this.messages].reverse().find(msg => msg.type === 'bot' && msg.isLoading)
        if (pendingBot) {
          pendingBot.isLoading = false
          pendingBot.isStreaming = false
        }
        if (this.isAbortError(error)) {
          this.$message.info('已取消当前提问')
        } else {
          this.$message.error('提问失败：' + (error.message || '网络错误'))
        }
      } finally {
        this.loading = false
        if (this.currentRequestController) {
          this.currentRequestController.abort()
          this.currentRequestController = null
        }
      }
    },
    isAbortError(error) {
      return error && (error.name === 'AbortError' || error.message === 'The user aborted a request.')
    },
    /**
     * 停止流式输出
     * 终止当前请求并确保Markdown格式正确转换
     */
    stopStreaming(botMessage) {
      if (this.currentRequestController) {
        // 标记为主动终止，避免finally块重复处理
        botMessage._aborted = true
        
        // 终止请求
        this.currentRequestController.abort()
        this.currentRequestController = null
        
        // 更新消息状态
        botMessage.isLoading = false
        botMessage.isStreaming = false
        
        // 清除防抖定时器
        const messageIndex = this.messages.findIndex(msg => msg === botMessage)
        const timerKey = botMessage.id || `msg_${messageIndex}`
        if (this.markdownParseTimers[timerKey]) {
          clearTimeout(this.markdownParseTimers[timerKey])
          delete this.markdownParseTimers[timerKey]
        }
        
        // 清除缓存，确保使用完整解析模式
        if (botMessage.id) {
          delete this.markdownCache[botMessage.id]
        }
        
        // 强制更新视图，使用完整解析模式（isStreaming 已设为 false）
        this.$nextTick(() => {
          this.$forceUpdate()
        })
        
        this.loading = false
        this.$message.info('已停止生成，当前内容已保存')
      }
    },
    handleClear() {
      if (this.currentRequestController) {
        this.currentRequestController.abort()
        this.currentRequestController = null
      }
      
      // 如果有关联的文件，询问是否保留文件信息
      if (this.uploadedFile) {
        this.$confirm('清空对话后，文件信息也会被移除。是否继续？', '提示', {
          confirmButtonText: '清空并移除文件',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.messages = []
          this.currentRelatedLaws = []
          this.currentRelatedCases = []
          this.currentEntities = {}
          this.uploadedFile = null
          this.loading = false
          this.$message.success('对话已清空')
        }).catch(() => {
          // 用户取消，不做任何操作
        })
      } else {
        this.messages = []
        this.currentRelatedLaws = []
        this.currentRelatedCases = []
        this.currentEntities = {}
        this.loading = false
      }
    },
    handleRemoveFile() {
      this.$confirm('移除文件后，后续提问将不再关联此文件。是否继续？', '提示', {
        confirmButtonText: '移除',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.uploadedFile = null
        this.$message({
          message: '文件已移除',
          type: 'success',
          duration: 3000
        })
      }).catch(() => {
        // 用户取消，不做任何操作
      })
    },
    beforeChatUpload(file) {
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
    async handleChatUpload(options) {
      try {
        const file = options.file
        this.uploading = true
        
        // 根据文件类型自动判断
        const isImage = /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(file.name)
        const type = isImage ? 'image' : 'document'
        
        const response = await uploadFile(file, type)
        
        if (response.code === 200) {
          const fileInfo = response.data
          
          // 如果已有文件，询问是否替换
          if (this.uploadedFile) {
            this.$confirm(`已有关联文件：${this.uploadedFile.fileName}，是否替换为新文件？`, '提示', {
              confirmButtonText: '替换',
              cancelButtonText: '取消',
              type: 'info'
            }).then(() => {
              this.uploadedFile = {
                url: fileInfo.url,
                fileName: fileInfo.originalFilename,
                type: fileInfo.type
              }
              this.$message({
                message: `文件上传成功！已替换为：${fileInfo.originalFilename}，后续提问将关联此文件`,
                type: 'success',
                duration: 3000
              })
            }).catch(() => {
              // 用户取消，不做任何操作
            })
          } else {
            // 直接关联新文件
            this.uploadedFile = {
              url: fileInfo.url,
              fileName: fileInfo.originalFilename,
              type: fileInfo.type
            }
            this.$message({
              message: `文件上传成功！已关联文件：${fileInfo.originalFilename}，后续提问将自动关联此文件`,
              type: 'success',
              duration: 3000
            })
          }
        } else {
          this.$message.error(response.message || '上传失败')
        }
      } catch (error) {
        console.error('上传错误:', error)
        this.$message.error('文件上传失败，请重试')
      } finally {
        this.uploading = false
      }
    },
    handleFeedback(qaId, type) {
      submitFeedback({
        qaId,
        feedbackType: type
      }).then(() => {
        this.$message.success('反馈提交成功，感谢您的反馈！')
      })
    },
    handleCollect(message) {
      if (!message.id) {
        this.$message.warning('该消息尚未保存，无法收藏')
        return
      }
      toggleFavorite({ qaId: message.id })
        .then((response) => {
          const isFavorite = response.data.includes('收藏成功')
          this.$message.success(isFavorite ? '收藏成功' : '已取消收藏')
          // 更新消息的收藏状态
          message.isFavorite = isFavorite
        })
        .catch((error) => {
          this.$message.error('收藏操作失败：' + (error.message || '网络错误'))
        })
    },
    formatAnswer(answer, isStreaming = false, messageId = null) {
      if (!answer) return ''

      // 调试用：打印当前拿到的原始 Markdown 文本（流式和非流式都打印）
      try {
        // 避免在生产环境长期刷日志，如有需要可以加条件判断
        // console.groupCollapsed && console.groupCollapsed('RAW_MD')
        console.log('RAW_MD ===>', {
          isStreaming,
          messageId,
          text: answer
        })
        // console.groupEnd && console.groupEnd()
      } catch (e) {
        // 打印失败不影响正常渲染
      }

      // 如果不是流式输出，使用缓存
      if (!isStreaming && messageId && this.markdownCache[messageId]) {
        return this.markdownCache[messageId]
      }
      
      // 如果是流式输出模式，使用分段解析策略
      const html = isStreaming 
        ? this.parseMarkdownIncremental(answer)
        : this.parseMarkdownComplete(answer)
      
      const finalHtml = html
        .replace(/《([^》]+)》/g, '<span class="law-highlight">《$1》</span>')
        .replace(/第([一二三四五六七八九十百千\d]+)条/g, '<span class="article-highlight">第$1条</span>')
      
      // 缓存完整解析结果
      if (!isStreaming && messageId) {
        this.markdownCache[messageId] = finalHtml
      }
      
      return finalHtml
    },
    /**
     * 完整解析模式：用于非流式输出或流式输出结束后的最终解析
     * 目标：尽量「原样尊重」后端返回的 Markdown，不再做激进的正则改写。
     */
    parseMarkdownComplete(text) {
      if (!text) return ''
      const normalized = this.preprocessAnswer(text)
      try {
        return md.render(normalized)
      } catch (error) {
        console.error('❌ Markdown 解析失败:', error)
        console.warn('原始文本片段:', normalized.substring(0, 200))
        return this.escapeHtml(normalized)
      }
    },
    /**
     * 增量解析模式：用于流式输出
     * 为了保证和最终结果一致，这里不再做复杂的“修复/拆分”，
     * 而是直接对当前已收到的完整文本做一次普通 Markdown 渲染。
     */
    parseMarkdownIncremental(text) {
      if (!text) return ''
      const normalized = this.preprocessAnswer(text)
      try {
        return md.render(normalized)
      } catch (error) {
        console.warn('流式 Markdown 解析失败，使用转义文本显示', error)
        return this.renderUnsafeText(normalized)
      }
    },
    /**
     * 修复流式输出中被拆分的markdown标记
     * 只修复真正未完成的标记，避免误删列表项和有效标记
     */
    fixIncompleteMarkdownMarkers(text) {
      if (!text) return text
      
      let result = text
      
      // 1. 修复未完成的标题标记 ###（只在文本末尾检查）
      // 检查文本末尾是否有未完成的标题标记（以 # 结尾且后面没有内容）
      const trimmedEnd = result.trimEnd()
      if (trimmedEnd.endsWith('#')) {
        // 从末尾向前查找连续的 #
        let hashEnd = trimmedEnd.length - 1
        let hashStart = hashEnd
        while (hashStart > 0 && trimmedEnd[hashStart - 1] === '#') {
          hashStart--
        }
        const hashCount = hashEnd - hashStart + 1
        if (hashCount >= 1 && hashCount <= 6) {
          // 检查这些 # 前面是否有换行符（说明是行首的标题）
          const beforeHash = trimmedEnd.substring(0, hashStart)
          // 如果前面有换行符，说明可能是有效的标题标记（在流式输出中被拆分）
          // 只在后面完全没有内容时才移除
          if (beforeHash.endsWith('\n')) {
            // 检查原始文本中 # 后面是否有内容
            const originalAfterHash = result.substring(result.length - (trimmedEnd.length - hashEnd - 1))
            // 如果后面完全没有内容或只有空白，才移除
            if (originalAfterHash.trim().length === 0) {
              result = result.substring(0, result.length - (trimmedEnd.length - hashStart)) + trimmedEnd.substring(hashStart)
            }
          }
        }
      }
      
      // 2. 修复未完成的粗体标记 **（只在文本末尾检查）
      // 统计 ** 的数量
      let boldCount = 0
      let i = 0
      while (i < result.length - 1) {
        if (result[i] === '*' && result[i + 1] === '*') {
          boldCount++
          i += 2
        } else {
          i++
        }
      }
      
      // 如果有未完成的粗体标记（奇数个 **），且最后一个在文本末尾附近
      if (boldCount % 2 !== 0) {
        const lastBoldIndex = result.lastIndexOf('**')
        if (lastBoldIndex !== -1) {
          const afterBold = result.substring(lastBoldIndex + 2)
          // 只在后面内容很少（少于20个字符）且没有闭合标记时才移除
          if (afterBold.trim().length < 20 && !afterBold.includes('**')) {
            result = result.substring(0, lastBoldIndex) + result.substring(lastBoldIndex + 2)
          }
        }
      }
      
      // 3. 不修复斜体标记 *，因为：
      // - 列表项以 * 开头，不应该被误删
      // - markdown-it 会自动处理未完成的斜体标记
      // - 如果误删列表项的 *，会导致列表无法解析
      
      return result
    },
    /**
     * 修复被换行符分隔的粗体标记（保留用于renderUnsafeText）
     * 如果 **text\n 后面没有闭合的 **，移除开头的 **，避免解析错误
     */
    fixBoldMarkersSeparatedByNewline(text) {
      if (!text) return text
      
      // 统计 ** 的数量
      let boldCount = 0
      let i = 0
      while (i < text.length - 1) {
        if (text[i] === '*' && text[i + 1] === '*') {
          boldCount++
          i += 2
        } else {
          i++
        }
      }
      
      // 如果有未完成的粗体标记（奇数个 **）
      if (boldCount % 2 !== 0) {
        // 找到最后一个 ** 的位置
        const lastBoldIndex = text.lastIndexOf('**')
        if (lastBoldIndex !== -1) {
          const afterBold = text.substring(lastBoldIndex + 2)
          // 如果后面有换行符且没有闭合的 **，说明粗体被换行符分隔了
          // 移除这个 **，避免解析错误
          if (afterBold.includes('\n') && !afterBold.includes('**')) {
            // 移除最后一个 **
            return text.substring(0, lastBoldIndex) + text.substring(lastBoldIndex + 2)
          }
          // 如果后面内容很少（少于2个字符），也移除这个 **
          if (afterBold.trim().length < 2) {
            return text.substring(0, lastBoldIndex) + text.substring(lastBoldIndex + 2)
          }
        }
      }
      
      return text
    },
    /**
     * 分段解析：将文本分割为完整部分和未完成部分
     * 采用简单可靠的策略
     */
    splitAndParseIncremental(text) {
      // 1. 检查是否有未完成的markdown结构
      const codeBlockMarkers = (text.match(/```/g) || []).length
      const hasIncompleteCodeBlock = codeBlockMarkers % 2 !== 0
      
      // 2. 查找最后一个可能未完成的markdown标记位置
      let lastIncompleteMarkerIndex = -1
      
      // 检查未完成的标题标记（### 后面没有空格和内容）
      // 从后往前查找，找到最后一个 # 序列
      for (let i = text.length - 1; i >= 0; i--) {
        if (text[i] === '#') {
          // 向前查找连续的 #
          let hashStart = i
          while (hashStart > 0 && text[hashStart - 1] === '#') {
            hashStart--
          }
          const hashCount = i - hashStart + 1
          if (hashCount >= 1 && hashCount <= 6) {
            // 检查后面是否有空格和内容
            const afterHash = text.substring(i + 1)
            // 更严格：如果后面没有空格，或者只有很少的内容（少于10个字符），认为是未完成的
            if (!afterHash.match(/^\s/) || (afterHash.match(/^\s/) && afterHash.trim().length < 10)) {
              // 找到未完成的标题标记
              lastIncompleteMarkerIndex = Math.max(lastIncompleteMarkerIndex, hashStart)
              break
            }
          }
        }
      }
      
      // 检查未完成的粗体标记（奇数个 **）
      const boldMatches = text.match(/\*\*/g)
      if (boldMatches && boldMatches.length % 2 !== 0) {
        const lastBoldIndex = text.lastIndexOf('**')
        if (lastBoldIndex !== -1) {
          const afterBold = text.substring(lastBoldIndex + 2)
          // 更严格：如果后面内容少于50个字符且没有闭合标记，认为是不完整的
          if (afterBold.trim().length < 50 && !afterBold.includes('**')) {
            lastIncompleteMarkerIndex = Math.max(lastIncompleteMarkerIndex, lastBoldIndex)
          }
        }
      }
      
      // 检查未完成的代码块
      if (hasIncompleteCodeBlock) {
        const lastCodeBlockIndex = text.lastIndexOf('```')
        if (lastCodeBlockIndex !== -1) {
          lastIncompleteMarkerIndex = Math.max(lastIncompleteMarkerIndex, lastCodeBlockIndex)
        }
      }
      
      // 3. 确定安全解析的结束位置
      let safeEndIndex = text.length
      
      if (lastIncompleteMarkerIndex !== -1) {
        // 如果有未完成的标记，在标记之前找安全边界
        const beforeMarker = text.substring(0, lastIncompleteMarkerIndex)
        safeEndIndex = this.findSimpleBoundary(beforeMarker)
      } else {
        // 没有未完成的标记，使用简单策略找边界
        safeEndIndex = this.findSimpleBoundary(text)
      }
      
      // 4. 如果有未完成的标记，不要强制保留90%，应该更保守
      // 只有在没有未完成标记时，才保留90%的内容
      if (lastIncompleteMarkerIndex === -1 && text.length > 100) {
        const minSafeIndex = Math.floor(text.length * 0.9)
        if (safeEndIndex < minSafeIndex) {
          safeEndIndex = minSafeIndex
        }
      }
      
      // 确保安全索引不会超过文本长度
      safeEndIndex = Math.min(safeEndIndex, text.length)
      
      // 5. 分割文本
      const safeText = text.substring(0, safeEndIndex)
      const unsafeText = text.substring(safeEndIndex)
      
      // 6. 解析安全部分
      let safeHtml = ''
      if (safeText.trim()) {
        try {
          safeHtml = md.render(safeText)
        } catch (error) {
          console.warn('安全部分解析失败', error)
          safeHtml = this.escapeHtml(safeText)
        }
      }
      
      // 7. 未完成部分：不解析，只转义显示（避免解析错误）
      let unsafeHtml = ''
      if (unsafeText) {
        // 对未完成部分只进行转义显示，不尝试markdown解析
        unsafeHtml = this.renderUnsafeText(unsafeText)
      }
      
      return safeHtml + unsafeHtml
    },
    /**
     * 简单的边界查找策略：只找明显的段落分隔
     * 避免过度检测导致误判
     * 特别考虑粗体、列表等Markdown结构的完整性
     */
    findSimpleBoundary(text) {
      if (!text) return 0
      
      // 1. 优先找最后一个双换行符（段落分隔，最可靠）
      const lastDoubleNewline = text.lastIndexOf('\n\n')
      if (lastDoubleNewline !== -1 && lastDoubleNewline > text.length * 0.3) {
        return lastDoubleNewline + 2
      }
      
      // 2. 找最后一个以句号、问号、感叹号结尾的句子，后面跟换行
      const sentenceEndRegex = /[。！？]\s*\n/g
      let lastMatch = null
      let match
      while ((match = sentenceEndRegex.exec(text)) !== null) {
        lastMatch = match
      }
      if (lastMatch && lastMatch.index > text.length * 0.3) {
        return lastMatch.index + lastMatch[0].length
      }
      
      // 3. 找最后一个换行符，但前面至少有一些内容
      const lastNewline = text.lastIndexOf('\n')
      if (lastNewline > text.length * 0.4) {
        return lastNewline + 1
      }
      
      // 4. 如果都没有，返回文本长度的90%（避免过度截断）
      return Math.max(0, Math.floor(text.length * 0.9))
    },
    /**
     * HTML转义
     */
    escapeHtml(text) {
      if (!text) return ''
      return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/\n/g, '<br>')
    },
    /**
     * 渲染未完成的文本，保留粗体标记和换行符
     * 用于流式输出的未完成部分，当markdown-it解析失败时使用
     * 注意：不处理斜体，避免误处理列表项
     */
    renderUnsafeText(text) {
      if (!text) return ''
      
      // 先修复被拆分的markdown标记
      text = this.fixIncompleteMarkdownMarkers(text)
      
      // 转义HTML特殊字符
      let escaped = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
      
      // 处理完整的粗体标记：**text** 转换为 <strong>text</strong>
      escaped = escaped.replace(/\*\*([^*]+?)\*\*/g, '<strong>$1</strong>')
      
      // 不处理斜体标记 *text*，因为：
      // 1. 列表项以 * 开头，会被误处理
      // 2. markdown-it 应该能正确处理，如果它失败了，我们也不应该手动处理
      
      // 处理换行符（保留所有换行）
      escaped = escaped.replace(/\n/g, '<br>')
      
      return escaped
    },
    getConfidenceColor(score) {
      if (score >= 0.8) return '#52c41a'
      if (score >= 0.6) return '#faad14'
      return '#f5222d'
    },
    showLawDetail(law) {
      this.selectedLaw = law
      this.lawDialogVisible = true
    },
    showCaseDetail(caseItem) {
      this.selectedCase = caseItem
      this.caseDialogVisible = true
    },
    getEntityLabel(key) {
      const labels = {
        laws: '法条',
        crimes: '罪名',
        organizations: '机构',
        concepts: '概念'
      }
      return labels[key] || key
    },
    getEntityTagType(key) {
      const types = {
        laws: 'primary',
        crimes: 'danger',
        organizations: 'warning',
        concepts: 'info'
      }
      return types[key] || ''
    },
    normalizeEntities(entities) {
      // 规范化entities数据，确保所有项都是可显示的格式
      if (!entities || typeof entities !== 'object') {
        return {}
      }
      
      const normalized = {}
      for (const [key, items] of Object.entries(entities)) {
        if (Array.isArray(items)) {
          normalized[key] = items.map(item => {
            // 如果item是字符串，尝试解析为JSON
            if (typeof item === 'string') {
              // 检查是否是JSON字符串
              if (item.trim().startsWith('{') && item.trim().endsWith('}')) {
                try {
                  return JSON.parse(item)
                } catch (e) {
                  // 解析失败，返回原始字符串
                  return item
                }
              }
              // 不是JSON字符串，直接返回
              return item
            }
            // 如果已经是对象，直接返回
            return item
          })
        } else {
          normalized[key] = items
        }
      }
      return normalized
    },
    formatEntityItem(item) {
      // 如果item是字符串，尝试解析为JSON
      if (typeof item === 'string') {
        // 检查是否是JSON字符串
        if (item.trim().startsWith('{') && item.trim().endsWith('}')) {
          try {
            const parsed = JSON.parse(item)
            // 如果有name字段，显示name
            if (parsed.name) {
              return parsed.name
            }
            // 如果有title字段，显示title
            if (parsed.title) {
              return parsed.title
            }
            // 如果有article字段，显示article
            if (parsed.article) {
              return parsed.article
            }
            // 如果解析成功但没有特定字段，返回原始字符串
            return item
          } catch (e) {
            // 解析失败，返回原始字符串
            return item
          }
        }
        // 不是JSON字符串，直接返回
        return item
      }
      // 如果item是对象
      if (typeof item === 'object' && item !== null) {
        if (item.name) return item.name
        if (item.title) return item.title
        if (item.article) return item.article
        // 如果都没有，返回对象的字符串表示
        return JSON.stringify(item)
      }
      // 其他情况，转换为字符串
      return String(item)
    },
    formatDate(date) {
      if (!date) return ''
      return new Date(date).toLocaleDateString()
    },
    /**
     * 对后端返回的 Markdown 做预处理：
     * 1. 统一换行符 / 制表符
     * 2. **轻量级地修复一些常见的「挤在一行里的 Markdown」问题**
     *    - 把「……：### 一、」这种模式拆成换行标题
     *    - 把「……1.  **条目**」这种模式拆成有序列表
     *    - 把「……*   **子项**」这种模式拆成无序列表
     *   这些规则只在标记前面是中文标点或句号时才生效，尽量避免误伤正常英文 Markdown。
     */
    preprocessAnswer(answer) {
      if (!answer) return ''
      
      let text = answer
        .replace(/\r\n/g, '\n') // Windows -> Unix 换行
        .replace(/\r/g, '')     // 去掉孤立的 \r
        .replace(/\t/g, '  ')   // 制表符 -> 两个空格，避免缩进混乱

      // ------------- 轻量级 Markdown 结构修复 -------------

      // 1) 把「：### 一、」这类挤在一行里的标题拆出来（在标题前补一个换行）
      // 示例："...如下：### 一、明确违约情形" -> "...如下：\n### 一、明确违约情形"
      text = text.replace(
        /([：。；\?？!！])\s*###\s+/g,
        '$1\n### '
      )

      // 2) 把「：1.  xxx」/「：2.  xxx」这种内嵌的有序列表拆出来（在列表前换行）
      // 示例："包括：1.  情形一；2.  情形二" -> "包括：\n1.  情形一；\n2.  情形二"
      text = text.replace(
        /([：。；\?？!！])\s*(\d+\.\s+)/g,
        '$1\n$2'
      )

      // 3) 把「：*   xxx」这类内嵌无序列表拆出来（在无序列表前换行）
      // 示例："包括：*   情形一 *   情形二" -> "包括：\n*   情形一\n*   情形二"
      text = text.replace(
        /([：。；\?？!！])\s*\*\s{2,}/g,
        '$1\n*   '
      )

      // 4) 标题行后面如果紧跟内容（比如 "### 一、...1. ..."），在标题后面强制换行
      // 示例："### 一、主要法律依据1.  xxx" -> "### 一、主要法律依据\n1.  xxx"
      text = text.replace(/(###[^\n]*?)(\d+\.\s+)/g, '$1\n$2')
      // 示例："### 二、具体处理步骤与方式**第一步：..." -> "### 二、具体处理步骤与方式\n**第一步：..."
      text = text.replace(/(###[^\n]*?)(\*\*第[一二三四五六七八九十]+步)/g, '$1\n$2')
      // 示例当前问题："### 一、 确定违约情形及责任首先需要明确……：1." ->
      // "### 一、 确定违约情形及责任\n首先需要明确……：1."
      text = text.replace(
        /(###\s*[一二三四五六七八九十]+、[^\n]*?)(首先[^\n]*：)/g,
        '$1\n$2'
      )

      // 5) 处理中文大标题行（不带 ###，例如 "一、 确定违约情形：XXXX"）
      // 在大标题后的第一个全角冒号 "：" 后面补一个换行
      // 示例："一、 确定违约情形：首先需要明确..." -> "一、 确定违约情形：\n首先需要明确..."
      text = text.replace(
        /(^|\n)([一二三四五六七八九十]+、[^\n：]*：)\s*/g,
        '$1$2\n'
      )

      // 6) 如果连续出现多个标题 / 列表标记，中间只有少量空格，也补一个换行
      // 避免 "### 一、### 二、" 挤在一起
      text = text.replace(/(###\s+[^\n]+?)\s+(###\s+)/g, '$1\n$2')
      text = text.replace(/(\d+\.\s+[^\n]+?)\s+(\d+\.\s+)/g, '$1\n$2')

      return text
    },
    formatArticleNumber(articleNumber) {
      if (!articleNumber) return ''
      // 如果已经包含"第"和"条"，直接返回
      if (articleNumber.includes('第') && articleNumber.includes('条')) {
        return articleNumber
      }
      // 否则添加"第"和"条"
      return `第${articleNumber}条`
    },
    scrollToBottom() {
      const container = this.$refs.messagesContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },
    resetSidebar() {
      this.currentRelatedLaws = []
      this.currentRelatedCases = []
      this.currentEntities = {}
    },
    /**
     * 只保留“第X条”这类具体条文，过滤掉“第X章”等章节级别记录
     */
    filterLawArticles(laws) {
      if (!Array.isArray(laws)) return []
      return laws.filter(law => {
        if (!law) return false
        const article = (law.articleNumber || '').toString().trim()
        // 必须包含“条”，且不包含“章”
        return article && article.includes('条') && !article.includes('章')
      })
    },
    /**
     * 清洗法条内容：去掉内容中的“第X章 / 第X节”标题行，只保留具体条文内容
     */
    cleanLawContent(content) {
      if (!content) return ''
      return content
        .split('\n')
        .filter(line => {
          const trimmed = line.trim()
          if (!trimmed) return true
          // 去掉 Markdown 标题前缀，例如 "## 第五章 工资"
          const withoutHashes = trimmed.replace(/^#{1,6}\s*/, '')
          // 过滤以“第X章”或“第X节”开头的行
          if (/^第[一二三四五六七八九十百千万0-9]+(章|节)/.test(withoutHashes)) {
            return false
          }
          return true
        })
        .join('\n')
    },
    async startStreamRequest(question, botMessage) {
      const controller = new AbortController()
      this.currentRequestController = controller
      let timedOut = false
      let hasReceivedChunk = false
      // 增加超时时间到120秒，因为DeepSeek API可能响应较慢
      const timeoutId = setTimeout(() => {
        timedOut = true
        controller.abort()
      }, 120000)
      const response = await askQuestionStream(
        {
          question,
          sessionId: this.sessionId
        },
        { signal: controller.signal }
      )

      if (!response || !response.ok || !response.body) {
        throw new Error(`流式接口响应异常 (${response ? response.status : '无响应'})`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      try {
        while (true) {
          const { value, done } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true }).replace(/\r/g, '')

          let separatorIndex
          while ((separatorIndex = buffer.indexOf('\n\n')) !== -1) {
            const chunk = buffer.slice(0, separatorIndex)
            buffer = buffer.slice(separatorIndex + 2)
            if (chunk.trim()) {
              const received = this.processSseChunk(chunk, botMessage)
              if (received && !hasReceivedChunk) {
                hasReceivedChunk = true
                clearTimeout(timeoutId)
              }
            }
          }
        }

        buffer += decoder.decode().replace(/\r/g, '')
        if (buffer.trim()) {
          const received = this.processSseChunk(buffer, botMessage)
          if (received && !hasReceivedChunk) {
            hasReceivedChunk = true
            clearTimeout(timeoutId)
          }
        }
      } catch (error) {
        if (timedOut) {
          throw new Error('STREAM_TIMEOUT')
        }
        if (this.isAbortError(error)) {
          // 用户主动终止，不抛出错误，让finally块处理清理
          // 但需要标记为已终止，避免重复处理
          botMessage._aborted = true
          return
        }
        throw error
      } finally {
        clearTimeout(timeoutId)
        // 只有在不是用户主动终止的情况下才清空controller
        // 如果用户主动终止，stopStreaming已经处理了
        if (!botMessage._aborted) {
          this.currentRequestController = null
          // 只有在流式输出真正结束时才隐藏加载指示器
          botMessage.isLoading = false
          botMessage.isStreaming = false
        }
        // 确保清除防抖定时器
        const messageIndex = this.messages.findIndex(msg => msg === botMessage)
        const timerKey = botMessage.id || `msg_${messageIndex}`
        if (this.markdownParseTimers[timerKey]) {
          clearTimeout(this.markdownParseTimers[timerKey])
          delete this.markdownParseTimers[timerKey]
        }
        // 流式输出结束后，清除缓存并强制进行最终完整解析
        if (botMessage.id) {
          delete this.markdownCache[botMessage.id]
        }
        // 强制更新视图，此时 isStreaming 已为 false，会使用完整解析模式
        this.$nextTick(() => {
          this.$forceUpdate()
        })
        // 清除终止标记
        delete botMessage._aborted
      }
    },
    processSseChunk(chunk, botMessage) {
      const lines = chunk.split('\n')
      let eventType = 'message'
      const dataLines = []

      lines.forEach((line, index) => {
        // 检查是否是event行（不trim，因为可能需要保留空格）
        if (line.trim().startsWith('event:')) {
          eventType = line.trim().substring(6).trim()
          return
        }
        
        // 检查是否是data行（使用startsWith而不是trimmed.startsWith，以正确处理data:后跟空格的情况）
        if (line.startsWith('data:')) {
          const dataPrefix = 'data:'
          const dataIndex = line.indexOf(dataPrefix)
          if (dataIndex !== -1) {
            // 提取data:后面的所有内容（包括空格和换行符信息）
            let dataContent = line.substring(dataIndex + dataPrefix.length)
            // SSE规范允许data:后有一个空格，但这个空格不是数据的一部分
            // 但如果data:后直接是换行符（即空内容），应该保留为空字符串
            if (dataContent.startsWith(' ')) {
              // 去掉前导空格（这是SSE规范允许的格式，但空格不是数据内容）
              dataContent = dataContent.substring(1)
            }
            // 保留原始内容，包括空字符串（表示空行）
            // 这样 data: 后面什么都没有时，会保留为空字符串，在join时形成换行
            dataLines.push(dataContent)
          }
          return
        }
        
        // 完全空的行（没有任何前缀）表示SSE消息结束，跳过
        // 注意：这里的空行不应该被当作data内容的一部分
        // 因为如果它是data内容，它应该以 "data: " 或 "data:" 开头
        if (!line.trim()) {
          // 这是一个SSE消息结束标记，跳过
          return
        }
      })

      if (dataLines.length === 0) return false
      // 使用换行符连接多个data行，保留所有内容
      // 注意：如果某个data行是空字符串（即后端发送了 "data: \n"），
      // 在join时会形成换行符，这样可以正确保留空行
      const dataStr = dataLines.join('\n')

      switch (eventType) {
        case 'start':
          if (dataStr) {
            this.sessionId = dataStr
          }
          break
        case 'metadata':
          this.applyMetadata(dataStr, botMessage)
          break
        case 'related':
          this.applyRelatedData(dataStr)
          break
        case 'error':
          botMessage.isLoading = false
          botMessage.isStreaming = false
          throw new Error(dataStr || '流式输出发生错误')
        case 'end':
          botMessage.isLoading = false
          botMessage.isStreaming = false
          // 流式输出结束时，清除防抖定时器
          const messageIndex = this.messages.findIndex(msg => msg === botMessage)
          const timerKey = botMessage.id || `msg_${messageIndex}`
          if (this.markdownParseTimers[timerKey]) {
            clearTimeout(this.markdownParseTimers[timerKey])
            delete this.markdownParseTimers[timerKey]
          }
          // 清除缓存，确保使用完整解析模式
          if (botMessage.id) {
            delete this.markdownCache[botMessage.id]
          }
          // 强制更新视图，使用完整解析模式（isStreaming 已设为 false）
          this.$nextTick(() => {
            this.$forceUpdate()
          })
          break
        default:
          // 流式输出进行中，保持加载状态
          botMessage.isLoading = true
          botMessage.isStreaming = true
          botMessage.answer = (botMessage.answer || '') + dataStr
          // 使用防抖机制，避免频繁重新解析 Markdown
          this.debounceMarkdownParse(botMessage)
          break
      }

      this.$nextTick(this.scrollToBottom)
      return true
    },
    /**
     * 防抖处理 Markdown 解析，减少样式跳动
     * 使用更短的延迟，因为现在使用增量解析，不会导致结构大幅变化
     */
    debounceMarkdownParse(botMessage) {
      // 使用消息在数组中的索引作为唯一标识
      const messageIndex = this.messages.findIndex(msg => msg === botMessage)
      const timerKey = botMessage.id || `msg_${messageIndex}`
      
      // 清除之前的定时器
      if (this.markdownParseTimers[timerKey]) {
        clearTimeout(this.markdownParseTimers[timerKey])
      }
      
      // 使用较短的延迟（150ms），因为增量解析已经避免了结构大幅变化
      this.markdownParseTimers[timerKey] = setTimeout(() => {
        // 强制更新视图
        this.$forceUpdate()
        delete this.markdownParseTimers[timerKey]
      }, 150)
    },
    applyMetadata(dataStr, botMessage) {
      try {
        const metadata = JSON.parse(dataStr)
        botMessage.id = metadata.id
        botMessage.confidenceScore = metadata.confidenceScore
        botMessage.questionType = metadata.questionType
        if (metadata.sessionId) {
          this.sessionId = metadata.sessionId
        }
        if (Array.isArray(metadata.relatedLaws) && metadata.relatedLaws.length > 0) {
          this.currentRelatedLaws = this.filterLawArticles(metadata.relatedLaws)
        }
        if (Array.isArray(metadata.relatedCases) && metadata.relatedCases.length > 0) {
          this.currentRelatedCases = metadata.relatedCases
        }
        if (metadata.entities) {
          this.currentEntities = this.normalizeEntities(metadata.entities)
        }
      } catch (error) {
        console.warn('解析metadata失败', error)
      }
    },
    applyRelatedData(dataStr) {
      try {
        const payload = JSON.parse(dataStr)
        this.currentRelatedLaws = this.filterLawArticles(payload.relatedLaws || [])
        this.currentRelatedCases = payload.relatedCases || []
        this.currentEntities = this.normalizeEntities(payload.entities || {})
      } catch (error) {
        console.warn('解析related数据失败', error)
      }
    },
    async fetchStandardAnswer(question, botMessage) {
      const response = await askQuestion({
        question,
        sessionId: this.sessionId
      })

      botMessage.answer = response.data.answer
      botMessage.confidenceScore = response.data.confidenceScore
      botMessage.questionType = response.data.questionType
      botMessage.id = response.data.id

      this.currentRelatedLaws = this.filterLawArticles(response.data.relatedLaws || [])
      this.currentRelatedCases = response.data.relatedCases || []
      this.currentEntities = this.normalizeEntities(response.data.entities || {})
      botMessage.isLoading = false
      botMessage.isStreaming = false
      this.$nextTick(this.scrollToBottom)
    },
    async loadConversationHistory(sessionId) {
      try {
        this.sessionId = sessionId
        const response = await getConversationHistory(sessionId)
        const historyList = response.data || []
        
        // 清空当前消息
        this.messages = []
        this.resetSidebar()
        
        // 按创建时间排序（确保顺序正确）
        const sortedHistory = [...historyList].sort((a, b) => {
          return new Date(a.createTime) - new Date(b.createTime)
        })
        
        // 将历史记录转换为消息格式
        sortedHistory.forEach(item => {
          // 添加用户消息
          this.messages.push({
            type: 'user',
            content: item.question
          })
          
          // 添加机器人回复
          const botMessage = {
            type: 'bot',
            answer: item.answer || '',
            confidenceScore: item.confidenceScore,
            questionType: item.questionType,
            id: item.id,
            isLoading: false,
            isStreaming: false
          }
          this.messages.push(botMessage)
          
          // 处理相关数据（法条、案例、实体）
          // 使用最后一条记录的相关数据作为侧边栏显示
          if (item.relatedLaws) {
            try {
              const laws = typeof item.relatedLaws === 'string' 
                ? JSON.parse(item.relatedLaws) 
                : item.relatedLaws
              if (Array.isArray(laws) && laws.length > 0) {
                // 如果是字符串数组，转换为对象格式
                const mappedLaws = laws.map(law => {
                  if (typeof law === 'string') {
                    // 解析字符串格式，如 "刑法第1条"
                    const match = law.match(/^(.+?)第(.+?)条$/)
                    if (match) {
                      return { title: match[1], articleNumber: match[2] }
                    }
                    return { title: law, articleNumber: '' }
                  }
                  return law
                })
                // 只保留“第X条”级别的记录
                this.currentRelatedLaws = this.filterLawArticles(mappedLaws)
              }
            } catch (e) {
              console.warn('解析相关法条失败', e)
            }
          }
          
          if (item.relatedCases) {
            try {
              const cases = typeof item.relatedCases === 'string' 
                ? JSON.parse(item.relatedCases) 
                : item.relatedCases
              if (Array.isArray(cases) && cases.length > 0) {
                // 如果是字符串数组，转换为对象格式
                this.currentRelatedCases = cases.map(caseItem => {
                  if (typeof caseItem === 'string') {
                    return { title: caseItem, courtName: '', judgeDate: null }
                  }
                  return caseItem
                })
              }
            } catch (e) {
              console.warn('解析相关案例失败', e)
            }
          }
          
          if (item.entities) {
            try {
              const entities = typeof item.entities === 'string' 
                ? JSON.parse(item.entities) 
                : item.entities
              if (entities && Object.keys(entities).length > 0) {
                this.currentEntities = this.normalizeEntities(entities)
              }
            } catch (e) {
              console.warn('解析实体失败', e)
            }
          }
        })
        
        // 滚动到底部
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      } catch (error) {
        console.error('加载历史对话失败', error)
        this.$message.error('加载历史对话失败：' + (error.message || '网络错误'))
      }
    }
  }
}
</script>

<style scoped>
.chat {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.chat-container {
  flex: 1;
  display: flex;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  padding: 20px;
  gap: 20px;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  min-height: 500px;
}

.message {
  margin-bottom: 20px;
}

.message-content {
  display: flex;
}

.message.user .message-content {
  justify-content: flex-end;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 8px;
  word-wrap: break-word;
}

/* 机器人消息气泡增加左侧内边距，确保序号和内容不会超出 */
.message-bubble.bot-bubble {
  padding-left: 24px; /* 增加左侧内边距，为列表 marker 预留空间 */
}

.user-bubble {
  background: var(--primary-color);
  color: white;
}

.bot-bubble {
  background: #f5f5f5;
  color: #333;
}

.bot-loading-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
  margin-bottom: 10px;
}

.bot-loading-indicator i {
  font-size: 16px;
}

.confidence-indicator {
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ddd;
}

.confidence-label {
  font-size: 12px;
  color: #666;
  margin-right: 10px;
}

.answer-content {
  line-height: 1.8;
  word-wrap: break-word;
  white-space: pre-wrap; /* 保留换行和空格 */
}

.answer-content br {
  display: block;
  margin: 0.2em 0;
  line-height: 1.8;
  content: '';
  height: 0;
}

.answer-content p {
  margin: 0 0 8px 0;
  line-height: 1.8;
  white-space: normal; /* 段落内正常换行，但保留 <br> 标签 */
}

/* 处理空段落，减少不必要的间距 */
.answer-content p:empty {
  margin: 0;
  height: 0;
  display: none;
}

/* 减少连续段落之间的间距 */
.answer-content p + p {
  margin-top: 0;
}

.answer-content h1,
.answer-content h2,
.answer-content h3,
.answer-content h4,
.answer-content h5,
.answer-content h6 {
  margin: 12px 0 8px 0;
  font-weight: bold;
  line-height: 1.4;
}

/* 标题后的第一个段落减少上边距 */
.answer-content h1 + p,
.answer-content h2 + p,
.answer-content h3 + p,
.answer-content h4 + p,
.answer-content h5 + p,
.answer-content h6 + p {
  margin-top: 0;
}

.answer-content h1 {
  font-size: 24px;
}

.answer-content h2 {
  font-size: 20px;
}

.answer-content h3 {
  font-size: 18px;
}

.answer-content h4 {
  font-size: 16px;
}

.answer-content h5 {
  font-size: 14px;
}

.answer-content h6 {
  font-size: 12px;
}

.answer-content ul,
.answer-content ol {
  margin: 0 0 8px 0;
  padding-left: 0; /* 移除列表容器的 padding，由 li 控制 */
  list-style-position: outside; /* marker 在内容框外 */
}

.answer-content li {
  margin-bottom: 4px;
  line-height: 1.8;
  display: list-item;
  padding-left: 28px; /* 为 marker 预留空间，确保 marker 在气泡框内 */
  margin-left: 0; /* 确保没有额外的左边距 */
  position: relative; /* 为 marker 定位做准备 */
}

/* 确保有序列表的序号有足够空间（数字可能比项目符号更宽） */
.answer-content ol li {
  padding-left: 32px; /* 有序列表需要更多空间来容纳序号 */
}

/* 列表后的段落减少上边距 */
.answer-content ul + p,
.answer-content ol + p {
  margin-top: 0;
}

/* 段落后的列表减少上边距 */
.answer-content p + ul,
.answer-content p + ol {
  margin-top: 0;
}

.answer-content strong {
  font-weight: bold;
}

.answer-content em {
  font-style: italic;
}

.answer-content code {
  background-color: #f4f4f4;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.answer-content pre {
  background-color: #f4f4f4;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 12px 0;
}

.answer-content pre code {
  background-color: transparent;
  padding: 0;
}

.answer-content blockquote {
  border-left: 4px solid #ddd;
  margin: 12px 0;
  padding-left: 16px;
  color: #666;
}

.answer-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.answer-content table th,
.answer-content table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.answer-content table th {
  background-color: #f5f5f5;
  font-weight: bold;
}

.answer-content hr {
  border: none;
  border-top: 1px solid #ddd;
  margin: 16px 0;
}

.law-highlight {
  color: var(--primary-color);
  font-weight: bold;
}

.article-highlight {
  color: #faad14;
  font-weight: bold;
}

.message-actions {
  margin-top: 10px;
  display: flex;
  gap: 5px;
}

.chat-input-area {
  padding: 20px;
  border-top: 1px solid #eee;
}

.input-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
}

.upload-btn-wrapper {
  flex-shrink: 0;
}

.upload-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid #dcdfe6;
  background: #fff;
  color: #606266;
  transition: all 0.3s;
}

.upload-btn:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background: #f0f9ff;
}

.upload-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.question-textarea-input {
  flex: 1;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.chat-sidebar {
  width: 300px;
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  max-height: calc(100vh - 120px);
  position: sticky;
  top: 80px;
  align-self: flex-start;
}

.sidebar-section {
  margin-bottom: 30px;
}

.sidebar-section h3 {
  font-size: 16px;
  color: #333;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--primary-color);
}

.law-item,
.case-item {
  padding: 10px;
  margin-bottom: 8px;
  background: #f9f9f9;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.law-item:hover,
.case-item:hover {
  background: var(--secondary-color);
  color: var(--primary-color);
}

.case-title {
  font-weight: bold;
  margin-bottom: 5px;
}

.case-meta {
  font-size: 12px;
  color: #999;
}

.entity-label {
  font-size: 12px;
  color: #666;
  margin: 10px 0 5px 0;
}

.entity-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}

.empty-state {
  color: #999;
  text-align: center;
  padding: 20px;
  font-size: 14px;
}

.uploaded-file-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae6fd;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.uploaded-file-info .file-info-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.uploaded-file-info i {
  color: var(--primary-color);
  font-size: 20px;
  flex-shrink: 0;
}

.uploaded-file-info .file-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.uploaded-file-info .file-name {
  color: #333;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.uploaded-file-info .file-hint {
  color: #666;
  font-size: 12px;
}

.uploaded-file-info .el-button {
  padding: 4px;
  color: #999;
  flex-shrink: 0;
}

.uploaded-file-info .el-button:hover {
  color: #f56c6c;
}
</style>