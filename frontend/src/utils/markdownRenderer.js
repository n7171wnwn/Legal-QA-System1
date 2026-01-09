import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

// 初始化 markdown-it 实例
// 按照标准配置，确保正确解析所有 Markdown 格式（粗体、斜体、标题、列表等）
const md = new MarkdownIt({
  html: true,        // 启用 HTML 标签
  linkify: true,     // 自动识别链接
  breaks: true,      // 将单个换行符转换为 <br>
  typographer: false, // 禁用排版优化，避免干扰中文标点
  // 使用默认的所有规则（包括粗体 **text**、斜体 *text*、标题 # 等）
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return '<pre class="hljs"><code class="hljs language-' + 
               MarkdownIt.utils.escapeHtml(lang) + '">' +
               hljs.highlight(str, { language: lang }).value +
               '</code></pre>'
      } catch (__) {}
    }
    // 如果没有指定语言或语言不支持，使用默认的转义
    return '<pre class="hljs"><code>' + MarkdownIt.utils.escapeHtml(str) + '</code></pre>'
  }
})

// 确保所有默认规则都启用
// markdown-it 默认启用以下规则：
// - 标题 (# ## ### 等)
// - 粗体 (**text** 或 __text__)
// - 斜体 (*text* 或 _text_)
// - 列表 (- * + 或数字)
// - 代码块 (```code```)
// - 行内代码 (`code`)
// - 链接、图片等

export default md

