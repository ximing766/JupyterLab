# assistant-ui Frontend

独立前端工程，基于 `assistant-ui` + Next.js（App Router）。

## Install

```powershell
cd e:\Work\Python\JupyterLab\langchain\demo_v1\ui
npm install
```

## Configure

```powershell
copy .env.example .env.local
```

默认后端地址：

```text
NEXT_PUBLIC_AGENT_API_URL=http://127.0.0.1:8000
```

## Run

```powershell
npm run dev
```

浏览器打开 <http://localhost:3000>。

## One-Click Start (Recommended)

在项目根目录执行（自动检查并处理端口占用、后台拉起前后端并自动打开浏览器）：

```powershell
cd e:\Work\Python\JupyterLab\langchain\demo_v1
powershell -ExecutionPolicy Bypass -File .\Start-Demo.ps1
```
