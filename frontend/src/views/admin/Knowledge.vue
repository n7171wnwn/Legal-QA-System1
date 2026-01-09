<template>
  <div class="admin-knowledge">
    <div class="admin-content">
      <el-tabs v-model="activeTab" @tab-click="handleTabChange">
        <!-- 问答知识 -->
        <el-tab-pane label="问答知识" name="qa">
          <div class="content-header">
            <h2>知识库管理</h2>
            <el-button type="primary" @click="handleAdd">添加知识</el-button>
          </div>

          <div class="search-bar">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索问题或答案..."
              style="width: 300px;"
              @keyup.enter.native="handleSearch"
            >
              <el-button slot="append" icon="el-icon-search" @click="handleSearch"></el-button>
            </el-input>
          </div>

          <el-table :data="knowledgeList" style="width: 100%">
            <el-table-column prop="id" label="ID" width="80"></el-table-column>
            <el-table-column prop="question" label="问题" show-overflow-tooltip></el-table-column>
            <el-table-column prop="answer" label="答案" show-overflow-tooltip></el-table-column>
            <el-table-column prop="questionType" label="类型" width="120"></el-table-column>
            <el-table-column prop="lawType" label="法律领域" width="120"></el-table-column>
            <el-table-column prop="usageCount" label="使用次数" width="100"></el-table-column>
            <el-table-column label="操作" width="200">
              <template slot-scope="scope">
                <el-button size="mini" @click="handleEdit(scope.row)">编辑</el-button>
                <el-button size="mini" type="danger" @click="handleDelete(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            @current-change="handlePageChange"
            :current-page="page"
            :page-size="pageSize"
            :total="total"
            layout="total, prev, pager, next"
            style="margin-top: 20px;"
          ></el-pagination>
        </el-tab-pane>

        <!-- 法条库（来自 legal_articles 表） -->
        <el-tab-pane label="法条库（数据库）" name="laws">
          <div class="content-header">
            <h2>法条库（数据库实时数据）</h2>
            <div>
              <el-button @click="loadLaws" :loading="lawLoading">刷新</el-button>
            </div>
          </div>

          <div class="law-stats">
            <div class="stat-item">
              <div class="stat-label">法律/法规部数</div>
              <div class="stat-value">{{ lawStats.totalLaws | numberFormat }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">法条总数</div>
              <div class="stat-value">{{ lawStats.totalArticles | numberFormat }}</div>
            </div>
          </div>

          <el-table
            :data="lawTitles"
            height="600px"
            style="width: 100%; margin-top: 12px;"
            v-loading="lawLoading"
          >
            <el-table-column type="index" label="#" width="60"></el-table-column>
            <el-table-column prop="title" label="法律名称" show-overflow-tooltip></el-table-column>
          </el-table>
          <div class="hint">数据来源：数据库表 legal_articles（仅显示去重后的 title 字段）</div>
        </el-tab-pane>
      </el-tabs>

      <el-dialog
        :title="dialogTitle"
        :visible.sync="dialogVisible"
        width="60%"
      >
        <el-form :model="form" label-width="100px">
          <el-form-item label="问题">
            <el-input v-model="form.question" type="textarea" :rows="3"></el-input>
          </el-form-item>
          <el-form-item label="答案">
            <el-input v-model="form.answer" type="textarea" :rows="5"></el-input>
          </el-form-item>
          <el-form-item label="问题类型">
            <el-select v-model="form.questionType">
              <el-option label="法条查询" value="法条查询"></el-option>
              <el-option label="概念定义" value="概念定义"></el-option>
              <el-option label="程序咨询" value="程序咨询"></el-option>
              <el-option label="案例分析" value="案例分析"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="法律领域">
            <el-input v-model="form.lawType"></el-input>
          </el-form-item>
        </el-form>
        <div slot="footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script>
import {
  getKnowledge,
  createKnowledge,
  updateKnowledge,
  deleteKnowledge,
  getAllTitles,
  getArticleStatistics
} from '@/api/api'

export default {
  name: 'AdminKnowledge',
  data() {
    return {
      activeTab: 'qa',
      searchKeyword: '',
      knowledgeList: [],
      page: 1,
      pageSize: 10,
      total: 0,
      lawTitles: [],
      lawStats: {
        totalLaws: 0,
        totalArticles: 0
      },
      lawLoading: false,
      dialogVisible: false,
      dialogTitle: '添加知识',
      form: {
        id: null,
        question: '',
        answer: '',
        questionType: '',
        lawType: ''
      }
    }
  },
  mounted() {
    this.loadData()
  },
  methods: {
    async handleTabChange(tab) {
      if (tab.name === 'laws' && this.lawTitles.length === 0) {
        this.loadLaws()
      }
    },
    async loadLaws() {
      this.lawLoading = true
      try {
        const [titlesResp, statsResp] = await Promise.all([
          getAllTitles(),
          getArticleStatistics()
        ])
        this.lawTitles = (titlesResp && titlesResp.data) ? titlesResp.data.map(t => ({ title: t })) : []
        if (statsResp && statsResp.data) {
          this.lawStats.totalLaws = statsResp.data.totalLaws || 0
          this.lawStats.totalArticles = statsResp.data.totalArticles || 0
        }
      } catch (e) {
        this.$message.error('加载法条库失败')
      } finally {
        this.lawLoading = false
      }
    },
    async loadData() {
      try {
        const response = await getKnowledge({
          keyword: this.searchKeyword,
          page: this.page - 1,
          size: this.pageSize
        })
        this.knowledgeList = response.data.content
        this.total = response.data.totalElements
      } catch (error) {
        this.$message.error('加载数据失败')
      }
    },
    handleSearch() {
      this.page = 1
      this.loadData()
    },
    handlePageChange(page) {
      this.page = page
      this.loadData()
    },
    handleAdd() {
      this.dialogTitle = '添加知识'
      this.form = {
        id: null,
        question: '',
        answer: '',
        questionType: '',
        lawType: ''
      }
      this.dialogVisible = true
    },
    handleEdit(row) {
      this.dialogTitle = '编辑知识'
      this.form = { ...row }
      this.dialogVisible = true
    },
    async handleDelete(row) {
      try {
        await this.$confirm('确定要删除这条知识吗？', '提示', {
          type: 'warning'
        })
        await deleteKnowledge(row.id)
        this.$message.success('删除成功')
        this.loadData()
      } catch (error) {
        if (error !== 'cancel') {
          this.$message.error('删除失败')
        }
      }
    },
    async handleSubmit() {
      try {
        if (this.form.id) {
          await updateKnowledge(this.form.id, this.form)
          this.$message.success('更新成功')
        } else {
          await createKnowledge(this.form)
          this.$message.success('添加成功')
        }
        this.dialogVisible = false
        this.loadData()
      } catch (error) {
        this.$message.error('操作失败')
      }
    }
  }
}
</script>

<style scoped>
.admin-knowledge {
  padding: 20px;
}

.admin-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.content-header h2 {
  margin: 0;
}

.search-bar {
  margin-bottom: 20px;
}

.law-stats {
  display: flex;
  gap: 16px;
  margin: 12px 0;
}

.stat-item {
  background: #f7f7f7;
  padding: 12px 16px;
  border-radius: 6px;
  min-width: 160px;
}

.stat-label {
  color: #666;
  font-size: 13px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
}

.hint {
  margin-top: 8px;
  color: #888;
  font-size: 12px;
}
</style>

