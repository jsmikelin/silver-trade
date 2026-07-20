# Silver Trade — 开发员风险管理方案

## 一、权限分级（最低权限原则）

### GitHub 权限
```
你的主账号 jsmikelin (Owner)
  └── 开发员账号 (Collaborator, Write access)
        ├── ✅ 可以: 创建分支、提交代码、发起 PR
        ├── ❌ 不可以: 直接 push main、删除仓库、修改 Settings
        └── ⚠️ 需要你 Approve 才能合并到 main
```

**设置步骤:**
1. GitHub → silver-trade → Settings → Collaborators → Add people
2. 开发员用自己的 GitHub 账号
3. Settings → Branches → Add rule → `main`
   - ☑ Require a pull request before merging
   - ☑ Require approvals (1)
   - ☑ Dismiss stale pull request approvals when new commits are pushed

### Render 权限
```
❌ 不给开发员 Render 账号权限
✅ 只有你登录 Render.com 管理
```
Render 部署自动从 GitHub main 分支触发。开发员只能通过 PR 间接影响部署。

### 域名权限
```
❌ 不给开发员 DNS 管理权限
✅ 域名注册商账号只有你持有
```

## 二、敏感信息隔离

### ✅ 已在安全位置（不在此仓库中）
| 信息 | 存储位置 |
|------|----------|
| Telegram Bot Token | `~/.hermes/.env`（本地） |
| Feishu App Secret | `~/.hermes/.env`（本地） |
| Google Analytics ID | 硬编码在 HTML 中（公开，无风险） |
| Render API Key | Render.com 控制台 |
| 域名 DNS | 域名注册商 |

### ⚠️ 需要确认
- [ ] Render 环境变量中是否有敏感值？
- [ ] 数据库 `db.sqlite3` 是否包含客户信息？（目前是本地文件，未上线）

## 三、代码审查流程

```
开发员创建 feature 分支 → 写代码 → git push → 创建 PR
    ↓
你审查 PR（看 diff，确认没有恶意代码）
    ↓
你点 Merge → Render 自动部署
```

**审查清单（每次 PR 必查）：**
- [ ] 有没有新增网络请求到未知域名？
- [ ] 有没有修改 `render.yaml` / `Procfile` / `requirements.txt`？
- [ ] 有没有嵌入 iframe 或外部脚本？
- [ ] 有没有修改 `.env` 相关配置？
- [ ] 有没有添加后门代码（eval、exec、base64_decode 等）？
- [ ] 有没有修改付款/定价相关内容？
- [ ] SEO 元数据有没有被篡改？

## 四、数据库保护

当前 `db.sqlite3` 在 repo 中（6月23日），需要：
- [ ] **立即从 repo 中删除 db.sqlite3** 并加入 .gitignore
- [ ] Render 用 PostgreSQL（render.yaml 已配置），生产数据库在 Render 上
- [ ] 本地开发用 SQLite，生产用 PostgreSQL

## 五、合同与法律

建议准备：
1. **NDA（保密协议）** — 禁止泄露客户信息、业务流程、定价策略
2. **Non-compete（竞业禁止）** — 离职后 N 个月内不得从事同类白银贸易
3. **代码归属声明** — 所有工作产出归属公司

## 六、监控与审计

| 监控点 | 方式 |
|--------|------|
| 代码变更 | GitHub commit history + PR review |
| 部署记录 | Render.com → Deploys 页面 |
| 网站内容变化 | 定期访问 helinsilver.com 检查 |
| Google Analytics | 检查是否有异常流量或跳转 |

## 七、紧急响应

如果发现开发员恶意行为：
1. GitHub → Settings → Collaborators → Remove（立即撤销权限）
2. GitHub → 检查并 revert 恶意提交
3. Render → 手动回滚到上一个正常部署
4. 修改所有可能泄露的 API Key/Token
