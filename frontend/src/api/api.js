import request from './request'

// 认证相关
export const login = (data) => request.post('/auth/login', data)
export const register = (data) => request.post('/auth/register', data)
export const uploadAvatar = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/auth/avatar', formData)
}
export const updateProfile = (data) => request.put('/auth/profile', data)

// 问答相关
export const askQuestion = (data) => request.post('/qa/ask', data)
export const askQuestionStream = (data, config = {}) => {
  return fetch('/api/qa/ask/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(config.headers || {})
    },
    body: JSON.stringify(data),
    signal: config.signal
  })
}
export const getQuestionHistory = (params) => request.get('/qa/history', { params })
export const getConversationHistory = (sessionId) => request.get(`/qa/conversation/${sessionId}`)
export const submitFeedback = (data) => request.post('/qa/feedback', data)
export const toggleFavorite = (data) => request.post('/qa/favorite', data)
export const getFavorites = (params) => request.get('/qa/favorites', { params })

// 法条相关
export const searchArticles = (params) => request.get('/legal/article/search', { params })
export const getArticlesByType = (lawType) => request.get(`/legal/article/type/${lawType}`)
export const getArticleById = (id) => request.get(`/legal/article/${id}`)
export const getAllArticles = () => request.get('/legal/article/all')
export const getAllTitles = () => request.get('/legal/article/titles')
export const getArticleStatistics = () => request.get('/legal/article/stats')

// 案例相关
export const searchCases = (params) => request.get('/legal/case/search', { params })
export const getCasesByType = (lawType) => request.get(`/legal/case/type/${lawType}`)
export const getCaseById = (id) => request.get(`/legal/case/${id}`)

// 概念相关
export const searchConcepts = (params) => request.get('/legal/concept/search', { params })
export const getConceptByName = (name) => request.get(`/legal/concept/name/${name}`)
export const getConceptById = (id) => request.get(`/legal/concept/${id}`)

// 管理员相关
export const getKnowledge = (params) => request.get('/admin/knowledge', { params })
export const createKnowledge = (data) => request.post('/admin/knowledge', data)
export const updateKnowledge = (id, data) => request.put(`/admin/knowledge/${id}`, data)
export const deleteKnowledge = (id) => request.delete(`/admin/knowledge/${id}`)

export const createArticle = (data) => request.post('/admin/article', data)
export const updateArticle = (id, data) => request.put(`/admin/article/${id}`, data)
export const deleteArticle = (id) => request.delete(`/admin/article/${id}`)

export const createCase = (data) => request.post('/admin/case', data)
export const updateCase = (id, data) => request.put(`/admin/case/${id}`, data)
export const deleteCase = (id) => request.delete(`/admin/case/${id}`)

export const createConcept = (data) => request.post('/admin/concept', data)
export const updateConcept = (id, data) => request.put(`/admin/concept/${id}`, data)
export const deleteConcept = (id) => request.delete(`/admin/concept/${id}`)

export const getStats = () => request.get('/admin/stats')
export const getQARecords = (params) => request.get('/admin/qa', { params })
export const getQARecord = (id) => request.get(`/admin/qa/${id}`)
export const deleteQARecord = (id) => request.delete(`/admin/qa/${id}`)
export const batchDeleteQARecords = (ids) => request.delete('/admin/qa/batch', { data: ids })

// 文件上传相关
export const uploadFile = (file, type = 'document') => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('type', type)
  // 不设置 Content-Type，让浏览器自动设置（包含 boundary）
  return request.post('/file/upload', formData)
}

