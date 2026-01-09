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
                        {{ getLawAbbr(law) }}
                      </el-tag>
                    </div>
                    <div class="law-title-info">
                      
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
                        {{ getLawAbbr(law) }}
                      </el-tag>
                    </div>
                    <div class="law-title-info">
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
                  {{ selectedLawTitle ? getLawAbbr({ title: selectedLawTitle, publishOrg: article.publishOrg }) : getLawAbbr(article) }}
                </el-tag>
                </div>
                <p class="article-content">{{ cleanLawContent(article.content) }}</p>
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
          <p>{{ cleanLawContent(selectedItem.content) }}</p>
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
import { searchArticles, searchCases, searchConcepts, getAllTitles, getLawSummaries } from '@/api/api'

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

        // 排序函数
        const sortLaws = (list) => {
          return list.sort((a, b) => {
            // 获取法律分类优先级
            const getCategoryPriority = (law) => {
              const title = (law.title || '').toLowerCase()
              const publishOrg = (law.publishOrg || '').toLowerCase()
              
              // 特殊处理：将"中华人民共和国宪法（2018年修正文本）"放在第一位
              const constitution2018 = '中华人民共和国宪法（2018年修正文本）'.toLowerCase()
              const constitution2018Alt = '中华人民共和国宪法(2018年修正文本)'.toLowerCase()
              if (title === constitution2018 || title === constitution2018Alt) {
                return -1 // 最高优先级，排在第一位
              }
              
              // 首先判断是否是修正案、老版本、地方法规或司法解释，这些都要放在后面
              // 注意：排除"中华人民共和国宪法（2018年修正文本）"，因为它已经在上面特殊处理了
              const isAmendment = (title.includes('修正案') || title.includes('修正文本') || title.includes('修正')) &&
                                  !(title === constitution2018 || title === constitution2018Alt)
              const isOldVersion = title.includes('废止') || title.includes('旧版') || title.includes('原') || 
                                   title.match(/\(\d{4}年\)/) || title.match(/\d{4}年/) || 
                                   title.includes('已废止') || title.includes('失效')
              
              // 判断是否是地方法规（省、市、自治区、县、自治县、施行等）
              const isLocalLaw = title.match(/省|市|自治区|特别行政区|地方|县|自治县|施行|变通/) || 
                                title.includes('施行《') ||
                                (publishOrg && publishOrg.match(/省|市|自治区|特别行政区|地方|县|自治县/) &&
                                 !publishOrg.includes('最高') && !publishOrg.includes('国务院') && 
                                 !publishOrg.includes('全国'))
              
              // 判断是否是司法解释（最高人民法院、最高人民检察院）
              const isJudicialInterpretation = (publishOrg.includes('最高') && (publishOrg.includes('法院') || publishOrg.includes('检察院'))) ||
                                              (title.includes('解释') && (publishOrg.includes('法院') || publishOrg.includes('检察院'))) ||
                                              (title.includes('规定') && publishOrg.includes('最高') && (publishOrg.includes('法院') || publishOrg.includes('检察院'))) ||
                                              (title.includes('意见') && publishOrg.includes('最高') && (publishOrg.includes('法院') || publishOrg.includes('检察院')))
              
              // 如果是修正案、老版本、地方法规或司法解释，直接返回低优先级（放在后面）
              if (isAmendment || isOldVersion || isLocalLaw || isJudicialInterpretation) {
                // 修正案优先级最低（950）
                if (isAmendment) return 950
                // 司法解释（900）
                if (isJudicialInterpretation) return 900
                // 老版本次之（850）
                if (isOldVersion) return 850
                // 地方法规（800）
                if (isLocalLaw) return 800
              }
              
              // 1. 常用法律法规的官方版本（最高优先级，按重要性排序）
              // 注意：只匹配官方版本，不包含修正案、年份、地方等标识
              const commonLaws = [
                '中华人民共和国宪法',                    // 宪法最优先（索引 0）
                '中华人民共和国民法典',                  // 民法（索引 1）
                '中华人民共和国刑法',                    // 刑法（索引 2）
                '中华人民共和国劳动法',                  // 劳动法（索引 3）
                '中华人民共和国未成年人保护法',          // 未成年保护法（索引 4）
                '中华人民共和国刑事诉讼法',              // 刑事诉讼法（索引 5）
                '中华人民共和国民事诉讼法',              // 民事诉讼法（索引 6）
                '中华人民共和国行政诉讼法',              // 行政诉讼法（索引 7）
                '中华人民共和国合同法',                  // 合同法（索引 8）
                '中华人民共和国公司法',                  // 公司法（索引 9）
                '中华人民共和国证券法',                  // 证券法（索引 10）
                '中华人民共和国婚姻法',                  // 婚姻法（索引 11）
                '中华人民共和国继承法',                  // 继承法（索引 12）
                '中华人民共和国物权法',                  // 物权法（索引 13）
                '中华人民共和国侵权责任法',              // 侵权责任法（索引 14）
                '中华人民共和国立法法',                  // 立法法（索引 15）
                '中华人民共和国行政处罚法',              // 行政处罚法（索引 16）
                '中华人民共和国行政许可法',              // 行政许可法（索引 17）
                '中华人民共和国行政复议法'               // 行政复议法（索引 18）
              ]
              
              // 精确匹配常用法律的官方版本（不包含修正案、年份、地方等）
              for (let i = 0; i < commonLaws.length; i++) {
                const lawKeyword = commonLaws[i].toLowerCase()
                // 精确匹配或标题以该法律名称开头且不包含年份、修正案、地方等标识
                if (title === lawKeyword || 
                    (title.startsWith(lawKeyword) && 
                     !title.match(/\(\d{4}年\)/) && 
                     !title.match(/\d{4}年/) &&
                     !title.includes('修正') &&
                     !title.match(/省|市|自治区|特别行政区|地方|县|自治县|施行|变通/))) {
                  return i // 返回索引，越小优先级越高
                }
              }
              
              // 2. 其他法律（中华人民共和国XX法，优先级 200）
              if (title.includes('中华人民共和国') && title.includes('法') && 
                  !title.match(/省|市|自治区|特别行政区|地方|县|自治县|施行|变通/) &&
                  !title.includes('修正') && !title.match(/\(\d{4}年\)/) && !title.match(/\d{4}年/)) {
                return 200
              }
              
              // 3. 行政法规（国务院发布的条例、办法、规定等，优先级 300）
              if ((publishOrg.includes('国务院') || publishOrg.includes('中华人民共和国国务院')) &&
                  (title.includes('条例') || title.includes('办法') || title.includes('规定') || title.includes('决定')) &&
                  !title.match(/省|市|自治区|特别行政区|地方|县|自治县|施行|变通/)) {
                return 300
              }
              
              // 4. 监察法规（优先级 350）
              if ((title.includes('监察') || publishOrg.includes('监察')) &&
                  !title.match(/省|市|自治区|特别行政区|地方|县|自治县|施行|变通/)) {
                return 350
              }
              
              // 5. 其他（优先级 600）
              return 600
            }

            const categoryA = getCategoryPriority(a)
            const categoryB = getCategoryPriority(b)

            // 先按分类优先级排序
            if (categoryA !== categoryB) {
              return categoryA - categoryB
            }

            // 同一分类内，按常用法律类型排序
            const commonLawTypes = ['民法', '刑法', '行政法', '合同法', '劳动法', '婚姻法', '继承法', '侵权责任法', '物权法']
            const getLawTypePriority = (lawType) => {
              if (!lawType) return 999
              const index = commonLawTypes.findIndex(type => lawType.includes(type))
              return index === -1 ? 999 : index
            }

            const typePriorityA = getLawTypePriority(a.lawType)
            const typePriorityB = getLawTypePriority(b.lawType)

            if (typePriorityA !== typePriorityB) {
              return typePriorityA - typePriorityB
            }

            // 最后按标题排序
            return a.title.localeCompare(b.title)
          })
        }

        if (!keyword) {
          // 无搜索关键词，获取所有法律列表
          const response = await getLawSummaries({})
          const allLawTitles = sortLaws(response.data || [])
          
          this.lawTitleTotal = allLawTitles.length
          this.lawTitles = allLawTitles
          this.lawTitlesByName = []
          this.lawTitlesByContent = []
          this.lawTitleNameTotal = 0
          this.lawTitleContentTotal = 0
          
          // 清空 allArticles，因为不再需要用它来构建法律列表
          this.allArticles = []
          
          this.updateTagWidth(allLawTitles)
          
          // 更新缓存
          lawCache.loaded = true
          lawCache.lawTitles = allLawTitles
          lawCache.lawTitleTotal = this.lawTitleTotal
          lawCache.tagWidth = this.tagWidth
        } else {
          // 有关键词，分别获取名称匹配和内容匹配的法律列表
          const [nameResponse, contentResponse] = await Promise.all([
            getLawSummaries({ keyword: keywordRaw, type: 'name' }),
            getLawSummaries({ keyword: keywordRaw, type: 'content' })
          ])
          
          this.lawTitlesByName = sortLaws(nameResponse.data || [])
          this.lawTitlesByContent = sortLaws(contentResponse.data || [])
          
          this.lawTitleNameTotal = this.lawTitlesByName.length
          this.lawTitleContentTotal = this.lawTitlesByContent.length
          this.lawTitleTotal = this.lawTitleNameTotal + this.lawTitleContentTotal
          
          // 清空 allArticles，因为不再需要用它来构建法律列表
          this.allArticles = []
          
          this.updateTagWidth(this.lawTitlesByName.concat(this.lawTitlesByContent))
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

        // 只剔除完全没有条号的记录，其余全部保留，避免误删正常条文（如“第一百零一条至第一百零九条”等）
        let lawArticles = rawLawArticles.filter(article => {
          const articleNumber = (article.articleNumber || '').trim()
          return articleNumber !== ''
        })
        if (lawArticles.length === 0) {
          lawArticles = rawLawArticles
        }
        
        // 按条号排序
        const sortedArticles = lawArticles.sort((a, b) => {
          return this.compareArticleNumber(a.articleNumber, b.articleNumber)
        })
        // 只保留“第X条”级别的法条，丢弃“第X章/第X节”等
        const filteredArticles = this.filterLawArticles(sortedArticles)
        this.currentLawArticles = filteredArticles.length > 0 ? filteredArticles : sortedArticles
        
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
      // 禁用缓存，始终拉取最新法律列表
      this.loadLawTitles()
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
        const sortedArticles = fetched.sort((a, b) => this.compareArticleNumber(a.articleNumber, b.articleNumber))
        const filteredArticles = this.filterLawArticles(sortedArticles)
        this.currentLawArticles = filteredArticles.length > 0 ? filteredArticles : sortedArticles
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
    /**
     * 只保留“第X条”这类具体条文，过滤掉“第X章/第X节”等章节级别记录
     */
    filterLawArticles(articles) {
      if (!Array.isArray(articles)) return []
      return articles.filter(article => {
        if (!article) return false
        const num = (article.articleNumber || '').toString().trim()
        // 必须包含“条”，且不包含“章”或“节”
        return num && num.includes('条') && !num.includes('章') && !num.includes('节')
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
    updateTagWidth(laws = []) {
      if (!laws.length) {
        this.tagWidth = 88
        return
      }
      // 支持传入 law 对象数组或 title 字符串数组（向后兼容）
      const abbrs = laws.map(law => {
        if (typeof law === 'string') {
          return this.getLawAbbr(law)
        } else {
          return this.getLawAbbr(law)
        }
      })
      const maxLen = Math.max(...abbrs.map(a => a.length || 0))
      // 粗略估算宽度：截断后字符数 * 14px + padding；设置上下限防止过大或过小
      const estimated = maxLen * 14 + 20
      this.tagWidth = Math.min(Math.max(estimated, 88), 240)
    },
    getLawAbbr(lawOrTitle) {
      // 支持传入 law 对象或 title 字符串
      let title = ''
      let publishOrg = ''
      
      if (typeof lawOrTitle === 'string') {
        title = lawOrTitle
      } else if (lawOrTitle && typeof lawOrTitle === 'object') {
        title = lawOrTitle.title || ''
        publishOrg = (lawOrTitle.publishOrg || '').toLowerCase()
      } else {
        return ''
      }
      
      if (!title) return ''
      
      const titleLower = title.toLowerCase()
      
      // 判断是否是地方法规
      const isLocalLaw = titleLower.match(/省|市|自治区|特别行政区|地方|县|自治县|施行|变通/) || 
                        titleLower.includes('施行《') ||
                        (publishOrg && publishOrg.match(/省|市|自治区|特别行政区|地方|县|自治县/) &&
                         !publishOrg.includes('最高') && !publishOrg.includes('国务院') && 
                         !publishOrg.includes('全国'))
      
      // 判断是否是司法解释
      const isJudicialInterpretation = (publishOrg.includes('最高') && (publishOrg.includes('法院') || publishOrg.includes('检察院'))) ||
                                      (titleLower.includes('解释') && (publishOrg.includes('法院') || publishOrg.includes('检察院'))) ||
                                      (titleLower.includes('规定') && publishOrg.includes('最高') && (publishOrg.includes('法院') || publishOrg.includes('检察院'))) ||
                                      (titleLower.includes('意见') && publishOrg.includes('最高') && (publishOrg.includes('法院') || publishOrg.includes('检察院')))
      
      // 判断是否是宪法
      const isConstitution = titleLower.includes('宪法') && !titleLower.includes('修正') && !titleLower.match(/\(\d{4}年\)/) && !titleLower.match(/\d{4}年/)
      
      // 判断是否是法律（中华人民共和国XX法）
      const isLaw = titleLower.includes('中华人民共和国') && titleLower.includes('法') && 
                   !titleLower.match(/省|市|自治区|特别行政区|地方|县|自治县|施行|变通/) &&
                   !titleLower.includes('修正') && !titleLower.match(/\(\d{4}年\)/) && !titleLower.match(/\d{4}年/)
      
      // 判断是否是行政法规
      const isAdministrativeRegulation = (publishOrg.includes('国务院') || publishOrg.includes('中华人民共和国国务院')) &&
                                        (titleLower.includes('条例') || titleLower.includes('办法') || titleLower.includes('规定') || titleLower.includes('决定')) &&
                                        !titleLower.match(/省|市|自治区|特别行政区|地方|县|自治县|施行|变通/)
      
      // 判断是否是监察法规
      const isSupervisionRegulation = (titleLower.includes('监察') || publishOrg.includes('监察')) &&
                                     !titleLower.match(/省|市|自治区|特别行政区|地方|县|自治县|施行|变通/)
      
      // 根据类型返回相应标签
      if (isLocalLaw) {
        return '地方法规'
      } else if (isJudicialInterpretation) {
        return '司法解释'
      } else if (isConstitution) {
        // 宪法显示简称
        let abbr = title.replace(/^中华人民共和国/, '').replace(/^中华人民共和/, '').replace(/^中国/, '').trim()
        if (!abbr) abbr = title
        const maxLen = 10
        if (abbr.length > maxLen) {
          abbr = abbr.slice(0, maxLen) + '...'
        }
        return abbr
      } else if (isLaw) {
        // 法律显示简称
        let abbr = title.replace(/^中华人民共和国/, '').replace(/^中华人民共和/, '').replace(/^中国/, '').trim()
        if (!abbr) abbr = title
        const maxLen = 10
        if (abbr.length > maxLen) {
          abbr = abbr.slice(0, maxLen) + '...'
        }
        return abbr
      } else if (isAdministrativeRegulation) {
        // 行政法规显示简称
        let abbr = title.replace(/^中华人民共和国/, '').replace(/^中华人民共和/, '').replace(/^中国/, '').trim()
        if (!abbr) abbr = title
        const maxLen = 10
        if (abbr.length > maxLen) {
          abbr = abbr.slice(0, maxLen) + '...'
        }
        return abbr
      } else if (isSupervisionRegulation) {
        // 监察法规显示简称
        let abbr = title.replace(/^中华人民共和国/, '').replace(/^中华人民共和/, '').replace(/^中国/, '').trim()
        if (!abbr) abbr = title
        const maxLen = 10
        if (abbr.length > maxLen) {
          abbr = abbr.slice(0, maxLen) + '...'
        }
        return abbr
      } else {
        // 其他情况显示简称（向后兼容）
        let abbr = title.replace(/^中华人民共和国/, '').replace(/^中华人民共和/, '').replace(/^中国/, '').trim()
        if (!abbr) abbr = title
        const maxLen = 10
        if (abbr.length > maxLen) {
          abbr = abbr.slice(0, maxLen) + '...'
        }
        return abbr
      }
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