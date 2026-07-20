# Silver Trade — 多开发员分工方案

## 模块拆分（每人独立，避免冲突）

### 模块 A：首页 & 产品页 (Frontend)
```
index.html            # 首页
products/index.html   # 产品页
css/style.css         # 全局样式
js/main.js            # 交互脚本
js/comex-pricing.js   # 价格组件
images/               # 图片资源
```
**负责人需掌握**: HTML, CSS, JavaScript  
**互不冲突**: 和模块 B/C/D 文件无重叠

### 模块 B：Django 后台 (Backend)
```
config/settings.py    # Django 配置
config/urls.py        # 路由
config/wsgi.py        # 部署入口
trading/models.py     # 数据模型
trading/views.py      # 视图逻辑
trading/admin.py      # 管理后台
trading/urls.py       # API 路由
requirements.txt      # 依赖（需审批）
manage.py             # CLI
```
**负责人需掌握**: Python, Django  
**互不冲突**: 和模块 A/C/D 文件无重叠  
**⚠️ 限制**: 不得修改 render.yaml / Procfile / requirements.txt

### 模块 C：SEO & 内容 (Content)
```
blog/*.html           # 博客文章
about/index.html      # 关于我们
contact/index.html    # 联系页面
sitemap.xml           # 站点地图
robots.txt            # 爬虫规则
llms.txt              # AI 可读内容
google*.html          # Google 验证文件
```
**负责人需掌握**: HTML, SEO 基础  
**互不冲突**: 和模块 A/B/D 文件无重叠

### 模块 D：日文版 (Japanese)
```
jp/index.html         # 日文首页
jp/products/          # 日文产品页（待建）
jp/about/             # 日文关于（待建）
jp/blog/              # 日文博客（待建）
```
**负责人需掌握**: HTML, 日语  
**互不冲突**: 和模块 A/B/C 文件无重叠

## 协作规则

### 每人只改自己的模块
```
dev-A 只提交 module-A/ 下的文件
dev-B 只提交 module-B/ 下的文件
...
跨模块改动 = 需要单独讨论 PR
```

### 公共文件冲突处理
`index.html` 和 `css/style.css` 可能被多人改 → 用独立的 CSS 文件隔离：

```html
<!-- 每个模块的样式独立文件 -->
<link rel="stylesheet" href="/css/module-a.css">
<link rel="stylesheet" href="/css/module-b-blog.css">
```

### GitHub 设置
```bash
# 为每个模块设置 CODEOWNERS (可选)
echo "index.html @dev-A-username" >> .github/CODEOWNERS
echo "products/ @dev-A-username" >> .github/CODEOWNERS
echo "blog/ @dev-C-username" >> .github/CODEOWNERS
```

## 当前建议的初始分工

| 模块 | 内容 | 建议给 |
|------|------|--------|
| A - 首页 & 产品 | HTML/CSS/JS 前端 | `52575725` |
| B - Django 后台 | Python 后端 | 留给自己或另招 |
| C - SEO & 内容 | 博客/SEO/多语言 | `52575725` 或内容编辑 |
| D - 日文版 | 日语翻译 | 另招日语人员 |

## 提交流程

```
dev-A: git checkout -b feature/new-hero-section
  → 只改 index.html + css/style.css
  → PR: [模块A] 新增英雄区域

dev-C: git checkout -b blog/new-article  
  → 只改 blog/*.html
  → PR: [模块C] 新增市场分析文章

dev-D: git checkout -b jp/update-homepage
  → 只改 jp/*
  → PR: [模块D] 更新日文首页
```

各自独立的 PR，互不阻塞，分别审查合并。
