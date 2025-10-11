# 📚 ximing766 技术文档中心

这是一个多项目文档管理中心，包含多个独立的GitHub项目，每个项目都部署到GitHub Pages。

## 🏗️ 项目结构

```
mydoc/
├── github.io/              # 主页项目 (https://ximing766.github.io/)
├── UwbKnowledgePoints/     # UWB技术文档
├── my-project-doc/         # 项目文档模板
├── deploy_all.py          # 自动化部署脚本
├── deploy.bat             # Windows批处理脚本
├── deploy_config.json     # 部署配置文件（自动生成）
└── README.md              # 本文件
```

## 🚀 快速开始

### 使用Python脚本

```bash
# 部署所有项目
uv run deploy_all.py deploy

# 部署所有项目并指定提交信息
uv run deploy_all.py deploy -m "更新文档内容"

# 部署单个项目
uv run deploy_all.py deploy -p github.io -m "更新主页"

# 查看所有项目状态
uv run deploy_all.py status

# 排除某些项目进行部署
uv run deploy_all.py deploy -e github.io my-project-doc

# 查看配置
uv run deploy_all.py config

# 添加新项目到配置
uv run deploy_all.py init --name new-project --path new-project --desc "新项目描述"

# 本地调试页面 进入项目目录
uv run mkdocs serve
```

## ⚙️ 配置说明

首次运行时会自动生成 `deploy_config.json` 配置文件：

```json
{
  "projects": {
    "github.io": {
      "path": "github.io",
      "branch": "master",
      "description": "主页项目",
      "build_command": null,
      "deploy_to_pages": true
    },
    "UwbKnowledgePoints": {
      "path": "UwbKnowledgePoints",
      "branch": "master",
      "description": "UWB技术文档",
      "build_command": "mkdocs build",
      "deploy_to_pages": true
    }
  },
}
```

## 📋 操作流程

脚本会按以下顺序处理每个项目：

1. **检查项目路径** - 验证项目目录是否存在
2. **检查Git状态** - 确认是否为Git仓库且有变更
3. **添加变更文件** - 执行 `git add .`
4. **提交变更** - 执行 `git commit` 并添加时间戳
5. **推送到远程** - 执行 `git push origin [branch]`
6. **构建文档** - 如果配置了构建命令，执行构建
7. **部署到Pages** - 执行 `mkdocs gh-deploy` 部署到GitHub Pages

**作者**: ximing766  
**创建时间**: 2025  