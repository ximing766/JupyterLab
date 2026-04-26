# Backend Service

独立 Python 后端服务，负责调用现有 `agent_core`。

## Run

```powershell
cd e:\Work\Python\JupyterLab\langchain\demo_v1
pip install -r .\backend\requirements.txt
python -m uvicorn backend.server:app --host 127.0.0.1 --port 8000 --reload
```

## API

- `GET /health`
- `POST /chat`
