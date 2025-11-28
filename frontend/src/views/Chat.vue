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
                <div class="bot-loading-indicator" v-if="message.isLoading">
                  <i class="el-icon-loading"></i>
                  <span>{{ message.isStreaming ? '正在生成回答...' : '正在思考中...' }}</span>
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
                  v-html="formatAnswer(message.answer)"
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
          <el-input
            v-model="currentQuestion"
            type="textarea"
            :rows="3"
            placeholder="请输入您的问题...（按Enter发送，Shift+Enter换行）"
            :disabled="loading"
            @keydown.enter.native="handleKeyDown"
          ></el-input>
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
        <p>{{ selectedLaw.content }}</p>
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
import { askQuestion, askQuestionStream, submitFeedback, getConversationHistory, toggleFavorite } from '@/api/api'
import { marked } from 'marked'

marked.setOptions({
  gfm: true,
  breaks: true,
  smartLists: true,
  headerIds: false,
  mangle: false
})

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
      currentRequestController: null
    }
  },
  async mounted() {
    // 如果传递了sessionId，加载历史对话记录
    if (this.$route.query.sessionId) {
      await this.loadConversationHistory(this.$route.query.sessionId)
    } else if (this.$route.query.question) {
      // 如果传递了question，自动发送（用于新提问）
      this.currentQuestion = this.$route.query.question
      this.handleSend()
    }
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

      const userMessage = {
        type: 'user',
        content: this.currentQuestion
      }
      this.messages.push(userMessage)

      const question = this.currentQuestion
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
    handleClear() {
      if (this.currentRequestController) {
        this.currentRequestController.abort()
        this.currentRequestController = null
      }
      this.messages = []
      this.currentRelatedLaws = []
      this.currentRelatedCases = []
      this.currentEntities = {}
      this.loading = false
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
    formatAnswer(answer) {
      if (!answer) return ''
      const normalized = this.preprocessAnswer(answer)
      const html = marked.parse(normalized)
      return html
        .replace(/《([^》]+)》/g, '<span class="law-highlight">《$1》</span>')
        .replace(/第([一二三四五六七八九十百千\d]+)条/g, '<span class="article-highlight">第$1条</span>')
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
    preprocessAnswer(answer) {
      let text = answer
        .replace(/\r\n/g, '\n')
        .replace(/\t/g, '  ')
        .trim()

      text = text.replace(/([^\n])(\d+)[\.、]\s*/g, (_, prev, num) => `${prev}\n${num}. `)
      text = text.replace(/([^\n])([一二三四五六七八九十]+[、．.])/g, (_, prev, token) => `${prev}\n${token}`)
      text = text.replace(/：(?=[^\n])/g, '：\n')
      text = text.replace(/\n{3,}/g, '\n\n')
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
    async startStreamRequest(question, botMessage) {
      const controller = new AbortController()
      this.currentRequestController = controller
      let timedOut = false
      let hasReceivedChunk = false
      const timeoutId = setTimeout(() => {
        timedOut = true
        controller.abort()
      }, 8000)
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
          throw error
        }
        throw error
      } finally {
        clearTimeout(timeoutId)
        this.currentRequestController = null
        botMessage.isLoading = false
        botMessage.isStreaming = false
      }
    },
    processSseChunk(chunk, botMessage) {
      const lines = chunk.split('\n')
      let eventType = 'message'
      const dataLines = []

      lines.forEach(line => {
        const trimmed = line.trim()
        if (!trimmed) return
        if (trimmed.startsWith('event:')) {
          eventType = trimmed.substring(6).trim()
        } else if (trimmed.startsWith('data:')) {
          dataLines.push(trimmed.substring(5).trim())
        }
      })

      if (dataLines.length === 0) return false
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
          break
        default:
          botMessage.isLoading = false
          botMessage.answer = (botMessage.answer || '') + dataStr
          break
      }

      this.$nextTick(this.scrollToBottom)
      return true
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
          this.currentRelatedLaws = metadata.relatedLaws
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
        this.currentRelatedLaws = payload.relatedLaws || []
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

      this.currentRelatedLaws = response.data.relatedLaws || []
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
                this.currentRelatedLaws = laws.map(law => {
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
  line-height: 1.7;
  white-space: pre-wrap;
}

.answer-content p {
  margin: 0 0 12px 0;
}

.answer-content ul,
.answer-content ol {
  margin: 0 0 12px 18px;
  padding-left: 18px;
}

.answer-content li {
  margin-bottom: 6px;
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

.input-actions {
  margin-top: 10px;
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
</style>

