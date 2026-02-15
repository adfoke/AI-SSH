# AI-SSH MVP

## 1. 安装依赖 (uv)

确保已安装 [uv](https://github.com/astral-sh/uv)。

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

## 2. 配置环境

```bash
cp .env.example .env
```

编辑 `.env`，填写 OpenRouter API Key 与 `CREDENTIALS_ENCRYPT_KEY`。

生成加密 key 示例：
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 3. 运行

```bash
uv run streamlit run ai_ssh/app.py
```

## 4. 功能
- 服务器列表管理（新增/删除）
- AI 生成命令并执行（IP/域名脱敏）
- 风险命令确认
- 执行结果审计（流式输出）

## 5. 注意事项
- 支持 key/password 登录
- 私钥路径需为本地绝对路径
- `.env` 不应提交到版本库
