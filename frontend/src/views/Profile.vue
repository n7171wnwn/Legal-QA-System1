<template>
  <div class="profile">
    <NavBar />
    <div class="profile-container">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="问答历史" name="history">
          <div class="history-list">
            <el-card
              v-for="item in historyList"
              :key="item.id"
              class="history-item"
            >
              <div class="history-question">
                <strong>Q:</strong> {{ item.question }}
              </div>
              <div class="history-answer">
                <strong>A:</strong> {{ item.answer }}
              </div>
              <div class="history-meta">
                <span>{{ formatDate(item.createTime) }}</span>
                <span class="history-type">{{ item.questionType }}</span>
                <el-button size="mini" @click="viewDetail(item)">查看详情</el-button>
              </div>
            </el-card>
            <el-pagination
              v-if="historyTotal > 0"
              @current-change="handlePageChange"
              :current-page="historyPage"
              :page-size="historyPageSize"
              :total="historyTotal"
              layout="total, prev, pager, next"
            ></el-pagination>
          </div>
        </el-tab-pane>
        <el-tab-pane label="我的收藏" name="favorites">
          <div class="history-list">
            <el-card
              v-for="item in favoritesList"
              :key="item.id"
              class="history-item"
            >
              <div class="history-question">
                <strong>Q:</strong> {{ item.question }}
              </div>
              <div class="history-answer">
                <strong>A:</strong> {{ item.answer }}
              </div>
              <div class="history-meta">
                <span>{{ formatDate(item.createTime) }}</span>
                <span class="history-type">{{ item.questionType }}</span>
                <el-button size="mini" @click="viewDetail(item)">查看详情</el-button>
              </div>
            </el-card>
            <div v-if="favoritesList.length === 0" class="empty-state">
              <i class="el-icon-star-off"></i>
              <p>暂无收藏</p>
            </div>
            <el-pagination
              v-if="favoritesTotal > 0"
              @current-change="handleFavoritesPageChange"
              :current-page="favoritesPage"
              :page-size="favoritesPageSize"
              :total="favoritesTotal"
              layout="total, prev, pager, next"
            ></el-pagination>
          </div>
        </el-tab-pane>
        <el-tab-pane label="个人信息" name="info">
          <el-card>
            <div class="user-info">
              <div class="avatar-section">
                <el-avatar 
                  :size="100" 
                  :src="avatarUrl"
                  :icon="!avatarUrl ? 'el-icon-user-solid' : ''"
                ></el-avatar>
                <el-upload
                  class="avatar-uploader"
                  action="#"
                  :show-file-list="false"
                  :before-upload="beforeAvatarUpload"
                  :http-request="handleAvatarUpload"
                  accept="image/*"
                >
                  <el-button style="margin-top: 20px;" :loading="avatarUploading">
                    {{ avatarUploading ? '上传中...' : '更换头像' }}
                  </el-button>
                </el-upload>
              </div>
              <div class="info-section">
                <el-form label-width="100px">
                  <el-form-item label="用户名">
                    <el-input v-model="userInfo.username" disabled></el-input>
                  </el-form-item>
                  <el-form-item label="昵称">
                    <el-input v-model="userInfo.nickname"></el-input>
                  </el-form-item>
                  <el-form-item label="邮箱">
                    <el-input v-model="userInfo.email"></el-input>
                  </el-form-item>
                  <el-form-item label="手机号">
                    <el-input v-model="userInfo.phone"></el-input>
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" @click="saveUserInfo">保存</el-button>
                  </el-form-item>
                </el-form>
              </div>
            </div>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script>
import NavBar from '@/components/NavBar.vue'
import { getQuestionHistory, getFavorites, uploadAvatar, updateProfile } from '@/api/api'

export default {
  name: 'Profile',
  components: {
    NavBar
  },
  data() {
    return {
      activeTab: 'history',
      historyList: [],
      historyPage: 1,
      historyPageSize: 10,
      historyTotal: 0,
      favoritesList: [],
      favoritesPage: 1,
      favoritesPageSize: 10,
      favoritesTotal: 0,
      userInfo: {},
      avatarUploading: false
    }
  },
  computed: {
    avatarUrl() {
      if (this.userInfo && this.userInfo.avatar) {
        const avatar = this.userInfo.avatar
        // 如果是完整URL，直接返回
        if (avatar.startsWith('http')) {
          return avatar
        }
        // 如果已经是/api/uploads/开头，直接返回
        if (avatar.startsWith('/api/uploads/')) {
          return avatar
        }
        // 如果以/uploads/开头，添加/api前缀
        if (avatar.startsWith('/uploads/')) {
          return '/api' + avatar
        }
        // 否则，假设是文件名，添加完整路径
        return `/api/uploads/${avatar}`
      }
      return null
    }
  },
  mounted() {
    this.userInfo = this.$store.state.user.userInfo || {}
    this.loadHistory()
  },
  watch: {
    activeTab(newTab) {
      if (newTab === 'favorites') {
        this.loadFavorites()
      }
    }
  },
  methods: {
    async loadHistory() {
      try {
        const response = await getQuestionHistory({
          page: this.historyPage - 1,
          size: this.historyPageSize
        })
        this.historyList = response.data.content
        this.historyTotal = response.data.totalElements
      } catch (error) {
        this.$message.error('加载历史记录失败')
      }
    },
    handlePageChange(page) {
      this.historyPage = page
      this.loadHistory()
    },
    viewDetail(item) {
      this.$router.push({
        path: '/chat',
        query: { sessionId: item.sessionId }
      })
    },
    beforeAvatarUpload(file) {
      const isImage = file.type.startsWith('image/')
      const isLt5M = file.size / 1024 / 1024 < 5

      if (!isImage) {
        this.$message.error('只能上传图片文件!')
        return false
      }
      if (!isLt5M) {
        this.$message.error('图片大小不能超过 5MB!')
        return false
      }
      return true
    },
    async handleAvatarUpload(options) {
      this.avatarUploading = true
      try {
        const response = await uploadAvatar(options.file)
        if (response.data && response.data.avatar) {
          // 更新本地用户信息
          this.userInfo = { ...this.userInfo, avatar: response.data.avatar }
          // 更新store中的用户信息
          this.$store.commit('user/UPDATE_USER_INFO', { avatar: response.data.avatar })
          this.$message.success('头像上传成功')
        }
      } catch (error) {
        this.$message.error('头像上传失败：' + (error.message || '网络错误'))
      } finally {
        this.avatarUploading = false
      }
    },
    async saveUserInfo() {
      try {
        const response = await updateProfile({
          nickname: this.userInfo.nickname,
          email: this.userInfo.email,
          phone: this.userInfo.phone
        })
        if (response.data) {
          this.userInfo = response.data
          // 更新store中的用户信息
          this.$store.commit('user/UPDATE_USER_INFO', this.userInfo)
          this.$message.success('保存成功')
        }
      } catch (error) {
        this.$message.error('保存失败：' + (error.message || '网络错误'))
      }
    },
    formatDate(date) {
      if (!date) return ''
      return new Date(date).toLocaleString()
    },
    async loadFavorites() {
      try {
        const response = await getFavorites({
          page: this.favoritesPage - 1,
          size: this.favoritesPageSize
        })
        this.favoritesList = response.data.content || []
        this.favoritesTotal = response.data.totalElements || 0
      } catch (error) {
        this.$message.error('加载收藏列表失败')
      }
    },
    handleFavoritesPageChange(page) {
      this.favoritesPage = page
      this.loadFavorites()
    }
  }
}
</script>

<style scoped>
.profile {
  min-height: 100vh;
  background: #f5f5f5;
}

.profile-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.history-list {
  background: white;
  padding: 20px;
  border-radius: 8px;
}

.history-item {
  margin-bottom: 20px;
}

.history-question {
  margin-bottom: 10px;
  color: #333;
}

.history-answer {
  margin-bottom: 10px;
  color: #666;
  line-height: 1.6;
}

.history-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #999;
}

.history-type {
  background: var(--primary-color);
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
}

.empty-state {
  text-align: center;
  padding: 60px;
  color: #999;
}

.empty-state i {
  font-size: 48px;
  margin-bottom: 20px;
}

.user-info {
  display: flex;
  gap: 40px;
}

.avatar-section {
  text-align: center;
}

.info-section {
  flex: 1;
}
</style>

