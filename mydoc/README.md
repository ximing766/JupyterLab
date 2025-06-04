# 📚 ximing766 技术文档中心

这是一个多项目文档管理中心，包含多个独立的GitHub项目，每个项目都部署到GitHub Pages。

## 🏗️ 项目结构

```
mydoc/
├── github.io/              # 主页项目 (https://ximing766.github.io/)
├── UwbKnowledgePoints/     # UWB技术文档
├── UWB_Application_Plan/   # UWB应用计划文档
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
python deploy_all.py deploy

# 部署所有项目并指定提交信息
python deploy_all.py deploy -m "更新文档内容"

# 部署单个项目
python deploy_all.py deploy -p github.io -m "更新主页"

# 查看所有项目状态
python deploy_all.py status

# 排除某些项目进行部署
python deploy_all.py deploy -e github.io my-project-doc

# 查看配置
python deploy_all.py config

# 添加新项目到配置
python deploy_all.py init --name new-project --path new-project --desc "新项目描述"
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
  "global_settings": {
    "default_commit_message": "docs: 更新文档内容",
    "auto_add_all": true,
    "push_after_commit": true,
    "deploy_to_gh_pages": true
  }
}
```

### 配置项说明

- `path`: 项目相对路径
- `branch`: Git分支名称
- `description`: 项目描述
- `build_command`: 构建命令（如 `mkdocs build`）
- `deploy_to_pages`: 是否部署到GitHub Pages

## 🎯 主要功能

### 1. 批量部署
- ✅ 自动检测所有项目的Git状态
- ✅ 批量提交和推送变更
- ✅ 自动构建和部署到GitHub Pages
- ✅ 智能跳过无变更的项目
- ✅ 详细的操作日志和结果统计

### 2. 状态监控
- ✅ 查看所有项目的Git状态
- ✅ 显示未提交的变更文件
- ✅ 项目路径和配置验证

### 3. 灵活配置
- ✅ 支持自定义提交信息
- ✅ 可排除特定项目
- ✅ 支持单项目操作
- ✅ 可配置构建和部署流程

## 🛠️ 使用场景

### 场景1：检查项目状态
```bash
# 查看哪些项目有未提交的变更
deploy.bat status
```

### 场景2：部署特定项目
```bash
# 只部署主页项目
python deploy_all.py deploy -p github.io -m "更新主页样式"
```

### 场景3：排除某些项目
```bash
# 部署除了模板项目外的所有项目
python deploy_all.py deploy -e my-project-doc -m "批量更新文档"
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

## ⚠️ 注意事项

1. **Git配置**：确保每个项目都已正确配置Git远程仓库
2. **权限设置**：确保有推送到各个仓库的权限
3. **MkDocs项目**：对于使用MkDocs的项目，确保已安装相关依赖
4. **网络连接**：部署过程需要稳定的网络连接
5. **备份重要数据**：建议在批量操作前备份重要文件

## 🔧 故障排除

### 常见问题

**Q: 提示"Not a git repository"**
A: 确保项目目录已初始化为Git仓库并配置了远程仓库

**Q: 推送失败**
A: 检查Git凭据和网络连接，确保有推送权限

**Q: MkDocs构建失败**
A: 检查项目依赖是否已安装，配置文件是否正确

**Q: GitHub Pages部署失败**
A: 检查仓库是否启用了GitHub Pages功能

### 调试模式

如果遇到问题，可以单独测试每个步骤：

```bash
# 只查看状态，不执行操作
python deploy_all.py status

# 测试单个项目
python deploy_all.py deploy -p github.io

# 查看详细配置
python deploy_all.py config
```

## 🎉 优势

相比手动逐个处理每个项目，使用这个自动化工具的优势：

- ⏱️ **节省时间**：一次命令处理所有项目，从几分钟缩短到几秒钟
- 🔒 **减少错误**：自动化流程避免手动操作失误
- 📊 **状态可视**：清晰显示每个项目的处理结果
- 🎯 **灵活控制**：支持选择性部署和自定义配置
- 📝 **操作记录**：详细的日志记录便于追踪问题

## 📞 支持

如果在使用过程中遇到问题，可以：

1. 查看本README的故障排除部分
2. 检查 `deploy_config.json` 配置是否正确

---

**作者**: ximing766  
**创建时间**: 2024  
**许可证**: MIT