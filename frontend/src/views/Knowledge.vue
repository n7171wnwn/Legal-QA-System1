<template>
  <div class="knowledge">
    <NavBar />
    <div class="knowledge-container">
      <div class="knowledge-header">
        <h1>法律知识库</h1>
        <div class="search-bar">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索法条、案例、概念..."
            size="large"
            @keyup.enter.native="handleSearch"
          >
            <el-button
              slot="append"
              icon="el-icon-search"
              class="search-cta"
              @click="handleSearch"
            >搜索</el-button>
          </el-input>
        </div>
        <div class="filter-tabs">
          <el-radio-group v-model="activeTab" @change="handleTabChange">
            <el-radio-button label="article">法条</el-radio-button>
            <el-radio-button label="case">案例</el-radio-button>
            <el-radio-button label="concept">概念</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <div class="knowledge-content">
        <!-- 法条列表 -->
        <div v-if="activeTab === 'article'" class="article-list">
          <div v-if="lawLoading" class="loading-state">
            <i class="el-icon-loading loading-icon"></i>
            <span>法条加载中，请稍候...</span>
          </div>
          <template v-else>
            <!-- 法律名称列表（默认显示 / 搜索时分为名称命中与内容命中） -->
            <div v-if="!selectedLawTitle" class="law-title-list">
              <div v-if="searchKeyword && searchKeyword.trim()" class="search-result-header search-toggle">
                <div>
                  <h3>搜索结果：名称命中 {{ lawTitleNameTotal }} 部，内容命中 {{ lawTitleContentTotal }} 部</h3>
                </div>
                <el-button-group>
                  <el-button
                    size="mini"
                    type="primary"
                    :plain="searchResultView !== 'name'"
                    @click="searchResultView = 'name'"
                  >法律名称含关键词</el-button>
                  <el-button
                    size="mini"
                    type="primary"
                    :plain="searchResultView !== 'content'"
                    @click="searchResultView = 'content'"
                  >法条内容含关键词</el-button>
                </el-button-group>
              </div>

              <!-- 名称命中 -->
              <template v-if="searchKeyword && searchKeyword.trim()">
                <!-- 仅显示当前视图 -->
                <template v-if="searchResultView === 'name'">
                  <el-card
                    v-for="law in displayedNameLawTitles"
                    :key="law.title + '_name'"
                    class="law-title-card"
                    @click.native="selectLaw(law.title)"
                  >
                    <div class="law-title-header">
                      <h3>{{ law.title }}</h3>
                      <el-tag
                        size="small"
                        type="info"
                        class="fixed-tag"
                        :style="{ width: tagWidth + 'px' }"
                      >
                        {{ getLawAbbr(law.title) }}
                      </el-tag>
                    </div>
                    <div class="law-title-info">
                      <span class="article-count">{{ law.count }} 条</span>
                      <span class="law-org" v-if="law.publishOrg">{{ law.publishOrg }}</span>
                    </div>
                  </el-card>
                  <el-pagination
                    v-if="lawTitleNameTotal > 0"
                    @current-change="handleLawTitleNamePageChange"
                    :current-page="lawTitleNamePage"
                    :page-size="lawTitlePageSize"
                    :total="lawTitleNameTotal"
                    layout="total, prev, pager, next"
                  ></el-pagination>
                </template>

                <template v-else>
                  <el-card
                    v-for="law in displayedContentLawTitles"
                    :key="law.title + '_content'"
                    class="law-title-card"
                    @click.native="selectLaw(law.title)"
                  >
                    <div class="law-title-header">
                      <h3>{{ law.title }}</h3>
                      <el-tag
                        size="small"
                        type="info"
                        class="fixed-tag"
                        :style="{ width: tagWidth + 'px' }"
                      >
                        {{ getLawAbbr(law.title) }}
                      </el-tag>
                    </div>
                    <div class="law-title-info">
                      <span class="article-count">{{ law.count }} 条</span>
                      <span class="law-org" v-if="law.publishOrg">{{ law.publishOrg }}</span>
                    </div>
                  </el-card>
                  <el-pagination
                    v-if="lawTitleContentTotal > 0"
                    @current-change="handleLawTitleContentPageChange"
                    :current-page="lawTitleContentPage"
                    :page-size="lawTitlePageSize"
                    :total="lawTitleContentTotal"
                    layout="total, prev, pager, next"
                  ></el-pagination>
                </template>

                <!-- 无搜索结果 -->
                <div v-if="lawTitleNameTotal === 0 && lawTitleContentTotal === 0" class="empty-result">
                  <el-empty description="未找到相关法律"></el-empty>
                </div>
              </template>

              <!-- 无搜索关键词，保持原有列表 -->
              <template v-else>
                <el-card
                  v-for="law in displayedNameLawTitles"
                  :key="law.title"
                  class="law-title-card"
                  @click.native="selectLaw(law.title)"
                >
                  <div class="law-title-header">
                    <h3>{{ law.title }}</h3>
                    <el-tag
                      size="small"
                      type="info"
                      class="fixed-tag"
                      :style="{ width: tagWidth + 'px' }"
                    >
                      {{ getLawAbbr(law.title) }}
                    </el-tag>
                  </div>
                  <div class="law-title-info">
                    <span class="article-count">{{ law.count }} 条</span>
                    <span class="law-org" v-if="law.publishOrg">{{ law.publishOrg }}</span>
                  </div>
                </el-card>
                <el-pagination
                  v-if="lawTitleTotal > 0"
                  @current-change="handleLawTitlePageChange"
                  :current-page="lawTitlePage"
                  :page-size="lawTitlePageSize"
                  :total="lawTitleTotal"
                  layout="total, prev, pager, next"
                ></el-pagination>
              </template>
            </div>

            <!-- 法条列表（点击法律名称后显示） -->
            <div v-else-if="selectedLawTitle" class="article-detail-list">
              <div class="law-header">
                <el-button icon="el-icon-arrow-left" @click="backToLawList" size="small">返回法律列表</el-button>
                <h2>{{ selectedLawTitle }}</h2>
              </div>
              <el-card
                v-for="article in paginatedLawArticles"
                :key="article.id"
                class="article-card"
                @click.native="showArticleDetail(article)"
              >
                <div class="article-header">
                  <h3 class="article-number-title">{{ formatArticleNumber(article.articleNumber) }}</h3>
                <el-tag
                  size="small"
                  class="fixed-tag"
                  :style="{ width: tagWidth + 'px' }"
                  @click.stop="loadFullLaw(selectedLawTitle || article.title)"
                >
                  {{ selectedLawTitle ? getLawAbbr(selectedLawTitle) : getLawAbbr(article.title) }}
                </el-tag>
                </div>
                <p class="article-content">{{ article.content }}</p>
                <div class="article-footer">
                  <span class="article-org" v-if="article.publishOrg">{{ article.publishOrg }}</span>
                  <span class="article-date" v-if="article.publishDate">{{ formatDate(article.publishDate) }}</span>
                </div>
              </el-card>
              <el-pagination
                v-if="currentLawArticlesTotal > 0"
                @current-change="handleLawArticlePageChange"
                :current-page="lawArticlePage"
                :page-size="lawArticlePageSize"
                :total="currentLawArticlesTotal"
                layout="total, prev, pager, next"
                style="margin-top: 20px; text-align: center;"
              ></el-pagination>
            </div>
          </template>
        </div>

        <!-- 案例列表 -->
        <div v-if="activeTab === 'case'" class="case-list">
          <el-card
            v-for="caseItem in cases"
            :key="caseItem.id"
            class="case-card"
            @click.native="showCaseDetail(caseItem)"
          >
            <div class="case-header">
              <h3>{{ caseItem.title }}</h3>
              <el-tag size="small" type="warning">{{ caseItem.caseType }}</el-tag>
            </div>
            <p class="case-court">{{ caseItem.courtName }}</p>
            <p class="case-point">{{ caseItem.disputePoint }}</p>
            <div class="case-footer">
              <span>判决日期：{{ formatDate(caseItem.judgeDate) }}</span>
            </div>
          </el-card>
          <el-pagination
            v-if="caseTotal > 0"
            @current-change="handleCasePageChange"
            :current-page="casePage"
            :page-size="casePageSize"
            :total="caseTotal"
            layout="total, prev, pager, next"
          ></el-pagination>
        </div>

        <!-- 概念列表 -->
        <div v-if="activeTab === 'concept'" class="concept-list">
          <el-card
            v-for="concept in concepts"
            :key="concept.id"
            class="concept-card"
            @click.native="showConceptDetail(concept)"
          >
            <h3>{{ concept.name }}</h3>
            <p class="concept-definition">{{ concept.definition }}</p>
            <el-tag size="small">{{ concept.lawType }}</el-tag>
          </el-card>
          <el-pagination
            v-if="conceptTotal > 0"
            @current-change="handleConceptPageChange"
            :current-page="conceptPage"
            :page-size="conceptPageSize"
            :total="conceptTotal"
            layout="total, prev, pager, next"
          ></el-pagination>
        </div>
      </div>
    </div>

    <!-- 详情对话框 -->
    <el-dialog
      :title="detailTitle"
      :visible.sync="detailVisible"
      width="60%"
    >
      <div v-if="selectedItem">
        <div v-if="activeTab === 'article'">
          <h3>{{ selectedItem.title }}<span v-if="formatArticleNumber(selectedItem.articleNumber)"> {{ formatArticleNumber(selectedItem.articleNumber) }}</span></h3>
          <p>{{ selectedItem.content }}</p>
          <p><strong>发布机构：</strong>{{ selectedItem.publishOrg || '未知' }}</p>
          <p><strong>发布日期：</strong>{{ formatDate(selectedItem.publishDate) || '未知' }}</p>
        </div>
        <div v-if="activeTab === 'case'" class="case-detail">
          <h3>{{ selectedItem.title }}</h3>
          <div class="case-meta-info">
            <p v-if="selectedItem.caseType"><strong>案由：</strong>{{ selectedItem.caseType }}</p>
            <p v-if="selectedItem.courtName"><strong>审理法院：</strong>{{ selectedItem.courtName }}</p>
            <p v-if="selectedItem.judgeDate"><strong>判决日期：</strong>{{ formatDate(selectedItem.judgeDate) }}</p>
            <p v-if="selectedItem.lawType"><strong>法律领域：</strong>{{ selectedItem.lawType }}</p>
          </div>
          <div v-if="selectedItem.disputePoint" class="case-section">
            <h4>核心争议点</h4>
            <p>{{ selectedItem.disputePoint }}</p>
          </div>
          <div v-if="selectedItem.judgmentResult" class="case-section">
            <h4>判决结果</h4>
            <p>{{ selectedItem.judgmentResult }}</p>
          </div>
          <div v-if="selectedItem.content" class="case-section">
            <h4>案例内容</h4>
            <div class="case-content" v-html="formatCaseContent(selectedItem.content)"></div>
          </div>
        </div>
        <div v-if="activeTab === 'concept'">
          <h3>{{ selectedItem.name }}</h3>
          <p><strong>定义：</strong>{{ selectedItem.definition }}</p>
          <p><strong>详细解释：</strong>{{ selectedItem.explanation }}</p>
          <p><strong>所属领域：</strong>{{ selectedItem.lawType }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import NavBar from '@/components/NavBar.vue'
import { searchArticles, searchCases, searchConcepts, getAllTitles } from '@/api/api'

// 简单的模块级缓存，组件卸载后仍可复用
const lawCache = {
  loaded: false,
  allArticles: [],
  lawTitles: [],
  lawTitleTotal: 0,
  tagWidth: 88
}

export default {
  name: 'Knowledge',
  components: {
    NavBar
  },
  data() {
    return {
      searchKeyword: '',
      activeTab: 'article',
      articles: [],
      cases: [],
      concepts: [],
      articlePage: 1,
      articlePageSize: 10,
      articleTotal: 0,
      casePage: 1,
      casePageSize: 10,
      caseTotal: 0,
      conceptPage: 1,
      conceptPageSize: 10,
      conceptTotal: 0,
      detailVisible: false,
      selectedItem: null,
      detailTitle: '',
      // 法条相关的新状态
      lawTitles: [], // 法律名称列表
      lawTitlesByName: [], // 法律名称命中列表
      lawTitlesByContent: [], // 法条内容命中列表
      lawTitlePage: 1,
      lawTitleNamePage: 1,
      lawTitleContentPage: 1,
      lawTitlePageSize: 20,
      lawTitleTotal: 0,
      lawTitleNameTotal: 0,
      lawTitleContentTotal: 0,
      searchResultView: 'name', // name | content
      selectedLawTitle: null, // 当前选中的法律名称
      currentLawArticles: [], // 当前法律下的所有法条列表
      allArticles: [], // 所有法条数据（用于分组）
      // 法条分页相关
      lawArticlePage: 1,
      lawArticlePageSize: 20,
      currentLawArticlesTotal: 0,
      lawLoading: false, // 法条加载状态
      hasLoadedArticles: false, // 是否已加载过法条列表（无搜索条件）
      lastSearchKeyword: '', // 上一次加载使用的关键词
      tagWidth: 88, // 角标宽度，根据最长简称计算
    }
  },
  mounted() {
    const type = this.$route.query.type
    if (type) {
      this.activeTab = type
    }
    this.loadData()
  },
  computed: {
    // 分页后的法条列表
    paginatedLawArticles() {
      if (!this.currentLawArticles || this.currentLawArticles.length === 0) {
        return []
      }
      const start = (this.lawArticlePage - 1) * this.lawArticlePageSize
      const end = start + this.lawArticlePageSize
      return this.currentLawArticles.slice(start, end)
    },
    displayedNameLawTitles() {
      const keyword = (this.searchKeyword || '').trim()
      if (!keyword) {
        const start = (this.lawTitlePage - 1) * this.lawTitlePageSize
        const end = start + this.lawTitlePageSize
        return this.lawTitles.slice(start, end)
      }
      const start = (this.lawTitleNamePage - 1) * this.lawTitlePageSize
      const end = start + this.lawTitlePageSize
      return this.lawTitlesByName.slice(start, end)
    },
    displayedContentLawTitles() {
      const keyword = (this.searchKeyword || '').trim()
      if (!keyword) {
        return []
      }
      const start = (this.lawTitleContentPage - 1) * this.lawTitlePageSize
      const end = start + this.lawTitlePageSize
      return this.lawTitlesByContent.slice(start, end)
    }
  },
  methods: {
    handleSearch() {
      // 搜索时重置状态
      if (this.activeTab === 'article') {
        this.selectedLawTitle = null
        this.currentLawArticles = []
        this.lawTitlePage = 1 // 重置法律列表分页
        this.lawTitleNamePage = 1
        this.lawTitleContentPage = 1
        this.searchResultView = 'name'
      }
      this.loadData()
    },
    handleTabChange() {
      // 切换标签时重置法条相关状态
      this.selectedLawTitle = null
      this.currentLawArticles = []
      this.loadData()
    },
    async loadData() {
      if (this.activeTab === 'article') {
        await this.loadArticles()
      } else if (this.activeTab === 'case') {
        await this.loadCases()
      } else if (this.activeTab === 'concept') {
        await this.loadConcepts()
      }
    },
    async loadArticles() {
      const keyword = (this.searchKeyword || '').trim()
      // 关键词变化时重置分页
      if (keyword !== this.lastSearchKeyword) {
        this.lawTitlePage = 1
      }

      try {
        this.lawLoading = true
        // 无论是否有搜索关键词，都显示法律名称列表
        // 搜索关键词用于过滤法律名称
        this.selectedLawTitle = null
        this.currentLawArticles = []
        await this.loadLawTitles()
        // 仅当无搜索或搜索成功后，标记已加载
        if (!keyword) {
          this.hasLoadedArticles = true
        }
        this.lastSearchKeyword = keyword
      } catch (error) {
        this.$message.error('加载法条失败')
      } finally {
        this.lawLoading = false
      }
    },
    async loadLawTitles() {
      try {
        const keywordRaw = (this.searchKeyword || '').trim()
        const keyword = keywordRaw.toLowerCase()
        const useCache = !keyword && lawCache.loaded
        if (useCache) {
          this.allArticles = lawCache.allArticles
          // 使用全部缓存数据，让计算属性处理分页
          this.lawTitleTotal = lawCache.lawTitleTotal
          this.lawTitles = lawCache.lawTitles  // 使用全部数据，不要在这里分页
          this.tagWidth = lawCache.tagWidth
          return
        }

        // 1) 获取全部法律标题
        const titlesResponse = await getAllTitles()
        const allTitles = titlesResponse.data || []

        // 2) 根据标题匹配和内容匹配合并过滤列表
        let filteredTitlesByName = allTitles
        if (keyword) {
          filteredTitlesByName = allTitles.filter(title =>
            title.toLowerCase().includes(keyword)
          )
        }

        // 3) 依据关键词搜索法条（关键词为空则取全部），用于内容命中
        const articlesResp = await searchArticles({
          keyword: keywordRaw,
          page: 0,
          size: 50000
        })
        this.allArticles = articlesResp.data.content || []

        // 4) 按法律名称分组（处理全部 articles，后续按命中拆分）
        const lawMap = new Map()
        this.allArticles.forEach(article => {
          const title = article.title
          if (!title) return
          if (!lawMap.has(title)) {
            lawMap.set(title, {
              title: title,
              lawType: article.lawType,
              publishOrg: article.publishOrg,
              count: 0,
              articles: []
            })
          }
          const law = lawMap.get(title)
          law.count++
          law.articles.push(article)
        })

        // 5) 构建名称命中与内容命中列表
        const lawListByName = filteredTitlesByName
          .map(title => lawMap.get(title))
          .filter(Boolean)

        const lawListByContent = this.allArticles
          .map(a => a.title)
          .filter(Boolean)
          .filter((t, idx, arr) => arr.indexOf(t) === idx)
          .map(title => lawMap.get(title))
          .filter(Boolean)
          // 若内容命中中与名称命中重复，则保留（需求未要求去重）
          ;

        // 6) 排序函数
        const sortLaws = (list) => {
          return list.sort((a, b) => {
            const isAmendmentA = a.title.includes('修正案')
            const isAmendmentB = b.title.includes('修正案')

            if (isAmendmentA !== isAmendmentB) {
              return isAmendmentA ? 1 : -1
            }

            const commonLawTypes = ['民法', '刑法', '行政法', '合同法', '劳动法', '婚姻法', '继承法', '侵权责任法', '物权法']

            const getLawTypePriority = (lawType) => {
              if (!lawType) return 999
              const index = commonLawTypes.findIndex(type => lawType.includes(type))
              return index === -1 ? 999 : index
            }

            const priorityA = getLawTypePriority(a.lawType)
            const priorityB = getLawTypePriority(b.lawType)

            if (priorityA !== priorityB) {
              return priorityA - priorityB
            }

            if (a.lawType !== b.lawType) {
              return (a.lawType || '').localeCompare(b.lawType || '')
            }
            return a.title.localeCompare(b.title)
          })
        }

        this.lawTitlesByName = sortLaws(lawListByName)
        this.lawTitlesByContent = sortLaws(lawListByContent)

        // 7) 分页处理与计数
        this.lawTitleNameTotal = this.lawTitlesByName.length
        this.lawTitleContentTotal = this.lawTitlesByContent.length

        // 当无关键词时，仍使用全部列表并缓存
        let allLawTitles = []
        if (!keyword) {
          allLawTitles = Array.from(lawMap.values())
          .sort((a, b) => {
                const isAmendmentA = a.title.includes('修正案')
                const isAmendmentB = b.title.includes('修正案')
                if (isAmendmentA !== isAmendmentB) return isAmendmentA ? 1 : -1
                const commonLawTypes = ['民法', '刑法', '行政法', '合同法', '劳动法', '婚姻法', '继承法', '侵权责任法', '物权法']
                const getLawTypePriority = (lawType) => {
                  if (!lawType) return 999
                  const index = commonLawTypes.findIndex(type => lawType.includes(type))
                  return index === -1 ? 999 : index
                }
                const priorityA = getLawTypePriority(a.lawType)
                const priorityB = getLawTypePriority(b.lawType)
                if (priorityA !== priorityB) return priorityA - priorityB
                if (a.lawType !== b.lawType) return (a.lawType || '').localeCompare(b.lawType || '')
                return a.title.localeCompare(b.title)
              })
          this.lawTitleTotal = allLawTitles.length
          // 存储全部数据，让计算属性处理分页
          this.lawTitles = allLawTitles
          this.updateTagWidth(allLawTitles.map(law => law.title))
          lawCache.loaded = true
          lawCache.allArticles = this.allArticles
          lawCache.lawTitles = allLawTitles
          lawCache.lawTitleTotal = this.lawTitleTotal
          lawCache.tagWidth = this.tagWidth
        } else {
          this.lawTitleTotal = this.lawTitleNameTotal + this.lawTitleContentTotal
          this.updateTagWidth(this.lawTitlesByName.concat(this.lawTitlesByContent).map(law => law.title))
        }
      } catch (error) {
        console.error('加载法律名称列表失败:', error)
        this.$message.error('加载法律名称列表失败')
      } finally {
        this.lawLoading = false
      }
    },
    async loadArticlesBySearch() {
      try {
        const response = await searchArticles({
          keyword: this.searchKeyword || '',
          page: this.articlePage - 1,
          size: this.articlePageSize
        })
        
        // 搜索结果显示法条列表，按条号排序
        this.articles = (response.data.content || []).sort((a, b) => {
          return this.compareArticleNumber(a.articleNumber, b.articleNumber)
        })
        this.articleTotal = response.data.totalElements
        
        // 如果有搜索结果，显示法条列表视图
        if (this.articles.length > 0) {
          this.selectedLawTitle = null
        }
      } catch (error) {
        console.error('搜索法条失败:', error)
        this.$message.error('搜索法条失败')
      }
    },
    async selectLaw(lawTitle) {
      this.lawLoading = true
      try {
        const keywordRaw = (this.searchKeyword || '').trim()
        // 从已加载的数据中查找该法律的所有法条
        let rawLawArticles = this.allArticles.filter(article => article.title === lawTitle)

        // 如果有关键词，优先仅展示该法律中“内容含关键词”的命中
        if (keywordRaw) {
          const lowerKey = keywordRaw.toLowerCase()
          rawLawArticles = rawLawArticles.filter(a => (a.content || '').toLowerCase().includes(lowerKey))
        }

        // 如果是无搜索或过滤后为空，则补全整部法律
        if (!keywordRaw || rawLawArticles.length === 0) {
          const res = await searchArticles({
            keyword: lawTitle,
            page: 0,
            size: 2000
          })
          const fetched = (res && res.data && res.data.content) ? res.data.content.filter(a => a.title === lawTitle) : []
          if (fetched.length) {
            rawLawArticles = keywordRaw
              ? fetched.filter(a => (a.content || '').toLowerCase().includes(keywordRaw.toLowerCase()))
              : fetched
            // 更新缓存，避免重复请求（同一法律去重）
            this.allArticles = this.allArticles.concat(
              fetched.filter(a => !this.allArticles.some(b => b.id === a.id))
            )
          }
        }

        // 过滤掉明显错误的条号（如"第第一款条"、"第第X条"等）
        let lawArticles = rawLawArticles.filter(article => {
          const articleNumber = article.articleNumber || ''
          
          // 过滤掉空条号
          if (!articleNumber || articleNumber.trim() === '') {
            return false
          }
          
          const cleanNumber = articleNumber.replace(/\s/g, '')
          
          // 排除包含"款"、"项"、"目"的条目（这些是条款的子项，不是条号）
          // 例如："第一款"、"第一项"、"第一目"等
          if (/[款项目]/.test(cleanNumber)) {
            return false
          }
          
          // 排除重复"第"的格式（如"第第X条"、"第第一款条"）
          if (/第.*第/.test(cleanNumber)) {
            return false
          }
          
          // 检查是否是有效的条号格式
          // 有效格式：第X条、第X章、第X节、X条等（X可以是中文数字或阿拉伯数字）
          const isValidFormat = /^第?[一二三四五六七八九十百千万\d]+[条章节]?$/.test(cleanNumber)
          
          if (!isValidFormat) {
            return false
          }
          
          return true
        })

        // 如果严格过滤后为空，回退使用原始数据，避免因条号缺失导致列表空白
        if (lawArticles.length === 0) {
          lawArticles = rawLawArticles
        }
        
        // 按条号排序
        this.currentLawArticles = lawArticles.sort((a, b) => {
          return this.compareArticleNumber(a.articleNumber, b.articleNumber)
        })
        
        // 重置分页
        this.lawArticlePage = 1
        this.currentLawArticlesTotal = this.currentLawArticles.length
        this.selectedLawTitle = lawTitle
      } catch (err) {
        this.$message.error('加载该法律的法条失败')
        console.error('加载法条失败', err)
      } finally {
        this.lawLoading = false
      }
    },
    handleLawArticlePageChange(page) {
      this.lawArticlePage = page
      // 滚动到顶部
      this.$nextTick(() => {
        const container = document.querySelector('.article-detail-list')
        if (container) {
          container.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      })
    },
    compareArticleNumber(num1, num2) {
      // 将中文数字转换为阿拉伯数字（完整实现）
      const chineseToNumber = (chinese) => {
        if (!chinese || chinese === '') return 0
        
        const chineseNumbers = {
          '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
          '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
        }
        
        // 处理简单的个位数
        if (chineseNumbers[chinese] !== undefined) {
          return chineseNumbers[chinese]
        }
        
        let result = 0
        let temp = 0
        
        // 从大到小处理：万、千、百、十
        // 处理"万"
        if (chinese.includes('万')) {
          const parts = chinese.split('万')
          if (parts[0]) {
            // 递归处理万前面的部分
            result += chineseToNumber(parts[0]) * 10000
          } else {
            result += 10000
          }
          if (parts[1]) {
            result += chineseToNumber(parts[1])
          }
          return result
        }
        
        // 处理"千"（必须先处理千，再处理百）
        if (chinese.includes('千')) {
          const parts = chinese.split('千')
          // 处理千前面的部分
          if (parts[0] && parts[0].length > 0) {
            const thousandPart = parts[0]
            // 如果是个位数，直接转换
            if (chineseNumbers[thousandPart] !== undefined) {
              result += chineseNumbers[thousandPart] * 1000
            } else {
              // 否则递归处理（如"十"、"二十"等）
              result += chineseToNumber(thousandPart) * 1000
            }
          } else {
            // 前面没有数字，默认为1
            result += 1000
          }
          // 处理千后面的部分（可能是"二百"、"三十"、"五"等）
          if (parts[1] && parts[1].length > 0) {
            result += chineseToNumber(parts[1])
          }
          return result
        }
        
        // 处理"百"
        if (chinese.includes('百')) {
          const parts = chinese.split('百')
          // 处理百前面的部分
          if (parts[0] && parts[0].length > 0) {
            const hundredPart = parts[0]
            if (chineseNumbers[hundredPart] !== undefined) {
              result += chineseNumbers[hundredPart] * 100
            } else {
              result += chineseToNumber(hundredPart) * 100
            }
          } else {
            result += 100
          }
          // 处理百后面的部分（可能是"三十"、"五"等）
          if (parts[1] && parts[1].length > 0) {
            result += chineseToNumber(parts[1])
          }
          return result
        }
        
        // 处理"十"
        if (chinese.includes('十')) {
          // 处理"十"（10）
          if (chinese === '十') {
            return 10
          }
          
          // 处理"十X"格式（如"十一"、"十二"）
          if (chinese.startsWith('十') && chinese.length === 2) {
            const second = chineseNumbers[chinese[1]]
            return second !== undefined ? 10 + second : 10
          }
          
          // 处理"X十"格式（如"二十"、"三十"）
          if (chinese.endsWith('十') && chinese.length === 2) {
            const first = chineseNumbers[chinese[0]]
            return first !== undefined ? first * 10 : 10
          }
          
          // 处理"X十Y"格式（如"二十一"、"三十五"）
          if (chinese.length === 3) {
            const first = chineseNumbers[chinese[0]]
            const last = chineseNumbers[chinese[2]]
            if (first !== undefined && last !== undefined) {
              return first * 10 + last
            }
          }
        }
        
        return 0
      }
      
      // 提取数字部分进行比较
      const extractNumber = (str) => {
        if (!str) return 0
        
        // 先尝试提取阿拉伯数字（完整数字）
        // 匹配：第123条、123条、第123、123等
        const arabicMatch = str.match(/第?\s*(\d+)\s*[条章节款项]?/)
        if (arabicMatch) {
          return parseInt(arabicMatch[1], 10)
        }
        
        // 尝试提取中文数字
        // 匹配格式：第一条、第一、一、一千二百条、第一千二百条等
        // 注意：要匹配"第一千二百条"这种格式，需要确保正则能匹配到"一千二百"
        const chineseMatch = str.match(/第\s*([一二三四五六七八九十百千万]+)\s*[条章节款项]?/) || 
                            str.match(/([一二三四五六七八九十百千万]+)\s*[条章节款项]?/)
        if (chineseMatch) {
          const chineseNum = chineseMatch[1]
          const number = chineseToNumber(chineseNum)
          return number
        }
        
        return 0
      }
      
      const num1Value = extractNumber(num1)
      const num2Value = extractNumber(num2)
      
      // 如果都是0，按原始字符串排序
      if (num1Value === 0 && num2Value === 0) {
        return (num1 || '').localeCompare(num2 || '')
      }
      
      return num1Value - num2Value
    },
    backToLawList() {
      this.selectedLawTitle = null
      this.currentLawArticles = []
      this.lawArticlePage = 1
      this.currentLawArticlesTotal = 0
    },
    handleLawTitlePageChange(page) {
      this.lawTitlePage = page
      // 如果使用缓存，不需要重新加载，计算属性会自动更新
      const keyword = (this.searchKeyword || '').trim()
      const useCache = !keyword && lawCache.loaded
      if (!useCache) {
        this.loadLawTitles()
      }
    },
    handleLawTitleNamePageChange(page) {
      this.lawTitleNamePage = page
    },
    handleLawTitleContentPageChange(page) {
      this.lawTitleContentPage = page
    },
    async loadFullLaw(lawTitle) {
      if (!lawTitle) return
      this.lawLoading = true
      try {
        const res = await searchArticles({
          keyword: lawTitle,
          page: 0,
          size: 2000
        })
        const fetched = (res && res.data && res.data.content) ? res.data.content.filter(a => a.title === lawTitle) : []
        this.currentLawArticles = fetched.sort((a, b) => this.compareArticleNumber(a.articleNumber, b.articleNumber))
        this.currentLawArticlesTotal = this.currentLawArticles.length
        this.lawArticlePage = 1
        this.selectedLawTitle = lawTitle
      } catch (err) {
        console.error('加载完整法条失败', err)
        this.$message.error('加载该法律的全部法条失败')
      } finally {
        this.lawLoading = false
      }
    },
    async loadCases() {
      try {
        const response = await searchCases({
          keyword: this.searchKeyword || '',
          page: this.casePage - 1,
          size: this.casePageSize
        })
        this.cases = response.data.content
        this.caseTotal = response.data.totalElements
      } catch (error) {
        this.$message.error('加载案例失败')
      }
    },
    async loadConcepts() {
      try {
        const response = await searchConcepts({
          keyword: this.searchKeyword || '',
          page: this.conceptPage - 1,
          size: this.conceptPageSize
        })
        this.concepts = response.data.content
        this.conceptTotal = response.data.totalElements
      } catch (error) {
        this.$message.error('加载概念失败')
      }
    },
    handleArticlePageChange(page) {
      this.articlePage = page
      this.loadArticles()
    },
    handleCasePageChange(page) {
      this.casePage = page
      this.loadCases()
    },
    handleConceptPageChange(page) {
      this.conceptPage = page
      this.loadConcepts()
    },
    showArticleDetail(article) {
      this.selectedItem = article
      this.detailTitle = '法条详情'
      this.detailVisible = true
    },
    showCaseDetail(caseItem) {
      this.selectedItem = caseItem
      this.detailTitle = '案例详情'
      this.detailVisible = true
    },
    showConceptDetail(concept) {
      this.selectedItem = concept
      this.detailTitle = '概念详情'
      this.detailVisible = true
    },
    formatDate(date) {
      if (!date) return ''
      return new Date(date).toLocaleDateString()
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
    formatCaseContent(content) {
      if (!content) return ''
      // 将 markdown 格式的标题转换为 HTML
      let formatted = content
        // 转换 ## 标题为 <h4>
        .replace(/^##\s+(.+)$/gm, '<h4>$1</h4>')
        // 转换 ### 标题为 <h5>
        .replace(/^###\s+(.+)$/gm, '<h5>$1</h5>')
        // 转换换行为 <br>
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')
      
      // 包装段落
      formatted = '<p>' + formatted + '</p>'
      
      // 清理多余的 <p> 标签
      formatted = formatted.replace(/<p><\/p>/g, '')
      formatted = formatted.replace(/<p>(<h[45]>)/g, '$1')
      formatted = formatted.replace(/(<\/h[45]>)<\/p>/g, '$1')
      
      return formatted
    },
    updateTagWidth(titles = []) {
      if (!titles.length) {
        this.tagWidth = 88
        return
      }
      const abbrs = titles.map(t => this.getLawAbbr(t))
      const maxLen = Math.max(...abbrs.map(a => a.length || 0))
      // 粗略估算宽度：截断后字符数 * 14px + padding；设置上下限防止过大或过小
      const estimated = maxLen * 14 + 20
      this.tagWidth = Math.min(Math.max(estimated, 88), 240)
    },
    getLawAbbr(title) {
      if (!title) return ''
      // 简单前缀清理，取核心简称
      let abbr = title
        .replace(/^中华人民共和国/, '')
        .replace(/^中华人民共和/, '')
        .replace(/^中国/, '')
        .trim()
      if (!abbr) abbr = title
      // 过长时截断并加省略，避免角标过宽
      const maxLen = 10
      if (abbr.length > maxLen) {
        abbr = abbr.slice(0, maxLen) + '...'
      }
      return abbr
    }
  }
}
</script>

<style scoped>
.knowledge {
  min-height: 100vh;
  background: #f5f5f5;
}

.knowledge-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.knowledge-header {
  background: white;
  padding: 30px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.knowledge-header h1 {
  font-size: 32px;
  color: var(--primary-color);
  margin-bottom: 20px;
}

.search-cta {
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.25);
}

.search-cta:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(64, 158, 255, 0.35);
}

.search-cta:active {
  transform: translateY(0);
  box-shadow: 0 3px 10px rgba(64, 158, 255, 0.3);
}

.search-bar {
  margin-bottom: 20px;
}

.filter-tabs {
  margin-top: 20px;
}

.knowledge-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.loading-state {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  color: #606266;
  gap: 12px;
}

.loading-icon {
  font-size: 32px;
  color: var(--primary-color);
}

.fixed-tag {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}

.law-title-card,
.article-card,
.case-card,
.concept-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.law-title-card:hover,
.article-card:hover,
.case-card:hover,
.concept-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.law-title-list {
  width: 100%;
}

.law-title-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.law-title-header h3 {
  margin: 0;
  color: var(--primary-color);
  font-size: 18px;
}

.law-title-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  font-size: 14px;
  color: #666;
}

.article-count {
  color: var(--primary-color);
  font-weight: 500;
}

.law-org {
  color: #999;
}

.article-detail-list {
  width: 100%;
}

.law-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e4e7ed;
}

.law-header h2 {
  margin: 0;
  color: var(--primary-color);
  font-size: 24px;
}

.article-number-title {
  margin: 0;
  color: var(--primary-color);
  font-size: 18px;
}

.article-search-list {
  width: 100%;
}

.search-result-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.search-result-header > div:first-child {
  flex: 1;
  min-width: 200px;
}

.search-result-header h3 {
  margin: 0;
  color: #333;
  font-size: 18px;
  line-height: 1.5;
}

.search-result-header .el-button-group {
  flex-shrink: 0;
}

.empty-result {
  padding: 60px 20px;
  text-align: center;
}


.minor-laws-list {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 5px;
}

.minor-laws-list .el-tag {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  color: white;
}

.article-header,
.case-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.article-header h3,
.case-header h3 {
  margin: 0;
  color: #333;
}

.article-number {
  color: var(--primary-color);
  font-weight: bold;
  margin: 10px 0;
}

.article-content {
  color: #666;
  line-height: 1.6;
  margin: 10px 0;
  display: -webkit-box;
  line-clamp: 3;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.article-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 12px;
  color: #999;
}

.case-court {
  color: #666;
  margin: 10px 0;
}

.case-point {
  color: #666;
  line-height: 1.6;
  margin: 10px 0;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.case-footer {
  margin-top: 10px;
  font-size: 12px;
  color: #999;
}

.concept-card h3 {
  color: var(--primary-color);
  margin-bottom: 10px;
}

.concept-definition {
  color: #666;
  line-height: 1.6;
  margin: 10px 0;
}

.case-detail {
  line-height: 1.8;
}

.case-detail h3 {
  color: var(--primary-color);
  margin-bottom: 20px;
  font-size: 24px;
}

.case-meta-info {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.case-meta-info p {
  margin: 8px 0;
  color: #606266;
}

.case-section {
  margin-bottom: 25px;
}

.case-section h4 {
  color: #303133;
  font-size: 18px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e4e7ed;
}

.case-content {
  color: #606266;
  line-height: 1.8;
}

.case-content h4 {
  color: #303133;
  font-size: 16px;
  margin: 20px 0 10px 0;
  padding-bottom: 6px;
  border-bottom: 1px solid #e4e7ed;
}

.case-content h5 {
  color: #606266;
  font-size: 14px;
  margin: 15px 0 8px 0;
  font-weight: 600;
}

.case-content p {
  margin: 10px 0;
  text-align: justify;
}
</style>