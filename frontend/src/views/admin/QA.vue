<template>
  <div class="admin-qa">
    <div class="admin-content">
      <div class="content-header">
        <h2>问答管理</h2>
        <div class="header-actions">
          <el-button 
            type="danger" 
            :disabled="selectedIds.length === 0"
            @click="handleBatchDelete"
          >
            批量删除 ({{ selectedIds.length }})
          </el-button>
        </div>
      </div>

      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索问题..."
          style="width: 300px;"
          @keyup.enter.native="handleSearch"
        >
          <el-button slot="append" icon="el-icon-search" @click="handleSearch"></el-button>
        </el-input>
      </div>

      <el-table 
        :data="qaList" 
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55"></el-table-column>
        <el-table-column prop="id" label="ID" width="80"></el-table-column>
        <el-table-column prop="question" label="问题" show-overflow-tooltip min-width="200"></el-table-column>
        <el-table-column prop="answer" label="答案" show-overflow-tooltip width="300"></el-table-column>
        <el-table-column prop="questionType" label="类型" width="120"></el-table-column>
        <el-table-column prop="confidenceScore" label="可信度" width="120">
          <template slot-scope="scope">
            <div v-if="scope.row.confidenceScore">
              <el-progress
                :percentage="Math.round(scope.row.confidenceScore * 100)"
                :color="getConfidenceColor(scope.row.confidenceScore)"
              ></el-progress>
              <span style="font-size: 12px; color: #666;">{{ Math.round(scope.row.confidenceScore * 100) }}%</span>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="feedbackType" label="反馈" width="100">
          <template slot-scope="scope">
            <el-tag v-if="scope.row.feedbackType === 'positive'" type="success">正面</el-tag>
            <el-tag v-else-if="scope.row.feedbackType === 'negative'" type="danger">负面</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="180">
          <template slot-scope="scope">
            {{ formatDate(scope.row.createTime) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template slot-scope="scope">
            <el-button size="mini" @click="handleViewDetail(scope.row)">查看详情</el-button>
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
    </div>

    <!-- 详情对话框 -->
    <el-dialog
      title="问答详情"
      :visible.sync="detailDialogVisible"
      width="800px"
    >
      <div class="detail-content" v-if="currentRecord">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="ID">{{ currentRecord.id }}</el-descriptions-item>
          <el-descriptions-item label="用户ID">{{ currentRecord.userId }}</el-descriptions-item>
          <el-descriptions-item label="问题类型" :span="2">{{ currentRecord.questionType || '-' }}</el-descriptions-item>
          <el-descriptions-item label="问题" :span="2">
            <div style="max-height: 100px; overflow-y: auto;">{{ currentRecord.question }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="答案" :span="2">
            <div style="max-height: 200px; overflow-y: auto; white-space: pre-wrap;">{{ currentRecord.answer }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="可信度">
            <div v-if="currentRecord.confidenceScore">
              <el-progress
                :percentage="Math.round(currentRecord.confidenceScore * 100)"
                :color="getConfidenceColor(currentRecord.confidenceScore)"
              ></el-progress>
              <span style="margin-left: 10px; color: #666;">{{ Math.round(currentRecord.confidenceScore * 100) }}%</span>
            </div>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="反馈">
            <el-tag v-if="currentRecord.feedbackType === 'positive'" type="success">正面</el-tag>
            <el-tag v-else-if="currentRecord.feedbackType === 'negative'" type="danger">负面</el-tag>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="是否收藏">
            <el-tag v-if="currentRecord.isFavorite" type="success">已收藏</el-tag>
            <span v-else>未收藏</span>
          </el-descriptions-item>
          <el-descriptions-item label="会话ID">{{ currentRecord.sessionId || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">{{ formatDate(currentRecord.createTime) }}</el-descriptions-item>
          <el-descriptions-item label="识别的实体" :span="2" v-if="currentRecord.entities">
            <div style="max-height: 150px; overflow-y: auto;">
              <div v-if="parsedEntities">
                <div v-if="parsedEntities.laws && parsedEntities.laws.length > 0" style="margin-bottom: 8px;">
                  <strong>法律：</strong>
                  <el-tag v-for="law in parsedEntities.laws" :key="law" size="small" style="margin-right: 5px; margin-bottom: 5px;">{{ law }}</el-tag>
                </div>
                <div v-if="parsedEntities.concepts && parsedEntities.concepts.length > 0" style="margin-bottom: 8px;">
                  <strong>概念：</strong>
                  <el-tag v-for="concept in parsedEntities.concepts" :key="concept" size="small" type="info" style="margin-right: 5px; margin-bottom: 5px;">{{ concept }}</el-tag>
                </div>
                <div v-if="parsedEntities.crimes && parsedEntities.crimes.length > 0" style="margin-bottom: 8px;">
                  <strong>罪名：</strong>
                  <el-tag v-for="crime in parsedEntities.crimes" :key="crime" size="small" type="warning" style="margin-right: 5px; margin-bottom: 5px;">{{ crime }}</el-tag>
                </div>
                <div v-if="parsedEntities.organizations && parsedEntities.organizations.length > 0" style="margin-bottom: 8px;">
                  <strong>组织：</strong>
                  <el-tag v-for="org in parsedEntities.organizations" :key="org" size="small" type="success" style="margin-right: 5px; margin-bottom: 5px;">{{ org }}</el-tag>
                </div>
                <div v-if="(!parsedEntities.laws || parsedEntities.laws.length === 0) && (!parsedEntities.concepts || parsedEntities.concepts.length === 0) && (!parsedEntities.crimes || parsedEntities.crimes.length === 0) && (!parsedEntities.organizations || parsedEntities.organizations.length === 0)" style="color: #999;">
                  无
                </div>
              </div>
              <div v-else style="color: #999; font-family: monospace; white-space: pre-wrap;">{{ currentRecord.entities }}</div>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="相关法条" :span="2" v-if="currentRecord.relatedLaws">
            <div style="max-height: 150px; overflow-y: auto;">
              <div v-if="parsedRelatedLaws && parsedRelatedLaws.length > 0">
                <div
                  v-for="(law, index) in parsedRelatedLaws"
                  :key="index"
                  style="margin-bottom: 5px; padding: 5px; background: #f5f7fa; border-radius: 4px;"
                >
                  {{ normalizeLawDisplay(law) }}
                </div>
              </div>
              <div v-else-if="parsedRelatedLaws && parsedRelatedLaws.length === 0" style="color: #999;">
                无
              </div>
              <div v-else style="color: #999; font-family: monospace; white-space: pre-wrap;">{{ currentRecord.relatedLaws }}</div>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="相关案例" :span="2" v-if="currentRecord.relatedCases">
            <div style="max-height: 150px; overflow-y: auto;">
              <div v-if="parsedRelatedCases && parsedRelatedCases.length > 0">
                <div v-for="(caseItem, index) in parsedRelatedCases" :key="index" style="margin-bottom: 5px; padding: 5px; background: #f5f7fa; border-radius: 4px;">
                  {{ caseItem }}
                </div>
              </div>
              <div v-else-if="parsedRelatedCases && parsedRelatedCases.length === 0" style="color: #999;">
                无
              </div>
              <div v-else style="color: #999; font-family: monospace; white-space: pre-wrap;">{{ currentRecord.relatedCases }}</div>
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { getQARecords, getQARecord, deleteQARecord, batchDeleteQARecords } from '@/api/api'

export default {
  name: 'AdminQA',
  data() {
    return {
      searchKeyword: '',
      qaList: [],
      page: 1,
      pageSize: 10,
      total: 0,
      selectedIds: [],
      detailDialogVisible: false,
      currentRecord: null,
      parsedEntities: null,
      parsedRelatedLaws: null,
      parsedRelatedCases: null
    }
  },
  watch: {
    currentRecord(newVal) {
      if (newVal) {
        this.parseRecordData(newVal)
      }
    }
  },
  mounted() {
    this.loadData()
  },
  methods: {
    async loadData() {
      try {
        const response = await getQARecords({
          keyword: this.searchKeyword,
          page: this.page - 1,
          size: this.pageSize
        })
        this.qaList = response.data.content
        this.total = response.data.totalElements
        // 清空选择
        this.selectedIds = []
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
    handleSelectionChange(selection) {
      this.selectedIds = selection.map(item => item.id)
    },
    async handleViewDetail(row) {
      try {
        const response = await getQARecord(row.id)
        this.currentRecord = response.data
        this.detailDialogVisible = true
      } catch (error) {
        this.$message.error('加载详情失败')
      }
    },
    handleDelete(row) {
      this.$confirm(`确定要删除这条问答记录吗？`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          await deleteQARecord(row.id)
          this.$message.success('删除成功')
          this.loadData()
        } catch (error) {
          this.$message.error('删除失败：' + (error.message || '未知错误'))
        }
      }).catch(() => {})
    },
    handleBatchDelete() {
      if (this.selectedIds.length === 0) {
        this.$message.warning('请选择要删除的记录')
        return
      }
      this.$confirm(`确定要删除选中的 ${this.selectedIds.length} 条记录吗？`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          await batchDeleteQARecords(this.selectedIds)
          this.$message.success('批量删除成功')
          this.loadData()
        } catch (error) {
          this.$message.error('批量删除失败：' + (error.message || '未知错误'))
        }
      }).catch(() => {})
    },
    getConfidenceColor(score) {
      if (score >= 0.8) return '#52c41a'
      if (score >= 0.6) return '#faad14'
      return '#f5222d'
    },
    formatDate(date) {
      if (!date) return ''
      return new Date(date).toLocaleString()
    },
    parseRecordData(record) {
      // 解析实体
      if (record.entities) {
        try {
          this.parsedEntities = JSON.parse(record.entities)
        } catch (e) {
          this.parsedEntities = null
        }
      } else {
        this.parsedEntities = null
      }
      
      // 解析相关法条
      if (record.relatedLaws) {
        try {
          const parsed = JSON.parse(record.relatedLaws)
          this.parsedRelatedLaws = Array.isArray(parsed) ? parsed : []
        } catch (e) {
          // 如果不是JSON，可能是字符串，尝试按换行分割
          this.parsedRelatedLaws = record.relatedLaws.split('\n').filter(item => item.trim())
        }
      } else {
        this.parsedRelatedLaws = []
      }
      
      // 解析相关案例
      if (record.relatedCases) {
        try {
          const parsed = JSON.parse(record.relatedCases)
          this.parsedRelatedCases = Array.isArray(parsed) ? parsed : []
        } catch (e) {
          // 如果不是JSON，可能是字符串，尝试按换行分割
          this.parsedRelatedCases = record.relatedCases.split('\n').filter(item => item.trim())
        }
      } else {
        this.parsedRelatedCases = []
      }
    },
    normalizeLawDisplay(law) {
      // law 可能是字符串或对象
      if (!law) return ''

      // 提取 title 和 num 的通用函数，匹配后统一重组为“标题第N条”
      const extract = (value) => {
        if (!value) return { title: '', num: '' }
        const str = String(value).trim().replace(/第+/g, '第').replace(/条+/g, '条')
        const match = str.match(/^(.*?)(?:第\s*)?([一二三四五六七八九十百千万0-9]+)\s*条?$/)
        if (match) {
          return {
            title: match[1].trim(),
            num: this.cleanArticleNumber(match[2])
          }
        }
        return { title: str, num: '' }
      }

      if (typeof law === 'object') {
        const title = law.title || ''
        let num = this.cleanArticleNumber(law.articleNumber || '')

        // 如果对象里条号为空，尝试从标题中解析
        if (!num) {
          const parsed = extract(title)
          if (parsed.num) {
            return parsed.title
              ? `${parsed.title}第${parsed.num}条`
              : `第${parsed.num}条`
          }
        }

        if (title && num) return `${title}第${num}条`
        if (title) return title
        if (num) return `第${num}条`
        return ''
      }

      // law 为字符串时，匹配到就强制重组，避免重复“第/条”
      const parsed = extract(law)
      const title = parsed.title
      const num = parsed.num
      if (title || num) {
        if (title && num) return `${title}第${num}条`
        if (title) return title
        if (num) return `第${num}条`
      }
      // 如果完全匹配不到，做一次去重后返回
      const cleaned = String(law).trim().replace(/第+/g, '第').replace(/条+/g, '条')
      return cleaned
    },
    cleanArticleNumber(num) {
      if (!num) return ''
      return String(num).replace(/第|条|\s/g, '').trim()
    }
  }
}
</script>

<style scoped>
.admin-qa {
  padding: 20px;
}

.admin-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
}

.content-header {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.content-header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.search-bar {
  margin-bottom: 20px;
}

.detail-content {
  max-height: 600px;
  overflow-y: auto;
}
</style>

