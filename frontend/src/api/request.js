import axios from 'axios'
import { Message } from 'element-ui'
import store from '@/store'

const service = axios.create({
  baseURL: '/api',
  timeout: 120000 // 增加到120秒，因为DeepSeek API可能响应较慢
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    const token = store.state.user.token
    if (token) {
      config.headers['Authorization'] = 'Bearer ' + token
    }
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code !== 200) {
      Message.error(res.message || '请求失败')
      if (res.code === 401) {
        store.dispatch('user/logout')
      }
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  error => {
    console.error('响应错误:', error)
    
    // 更友好的错误提示
    let errorMessage = '网络错误'
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      errorMessage = '请求超时，请稍后再试'
    } else if (error.message.includes('Network Error')) {
      errorMessage = '网络连接失败，请检查网络'
    } else if (error.response) {
      const status = error.response.status
      if (status === 500) {
        errorMessage = '服务器错误，请稍后再试'
      } else if (status === 503) {
        errorMessage = '服务暂时不可用，请稍后再试'
      } else {
        errorMessage = (error.response.data && error.response.data.message) || `请求失败 (${status})`
      }
    } else {
      errorMessage = error.message || '网络错误'
    }
    
    Message.error(errorMessage)
    return Promise.reject(error)
  }
)

export default service

