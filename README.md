# AI-SSH
**Manage your server with AI**

AI-SSH 智能运维工具架构设计方案 (OpenRouter + SQLite)

## 1. 系统愿景
打造一个“对话即运维”的本地化工具。用户通过自然语言描述运维目标，系统通过 OpenRouter 调用顶级 AI 模型（如 Claude 3.5 Sonnet 或 GPT-4o）生成指令，并在本地通过 SQLite 管理的 SSH 凭据安全地执行任务。

## 2. 技术栈选型

| 维度 | 选型 | 说明 |
| :--- | :--- | :--- |
| **编程语言** | Python 3.10+ | 强大的生态，支持异步 IO。 |
| **AI 接口** | OpenRouter API | 统一接入多模型，无需为每个厂商申请 API。 |
| **数据库** | SQLite | 无需部署，单文件存储，适合个人/内网本地化使用。 |
| **SSH 引擎** | Paramiko / Fabric | 成熟的 Python SSH 实现，支持密钥和密码认证。 |
| **Web UI** | Streamlit | 专为 AI 交互设计的响应式框架，开发速度极快。 |
| **ORM 框架** | SQLAlchemy | 方便管理 SQLite 数据表结构。 |

## 3. 系统架构图

### 3.1 核心组件说明
*   **交互层 (Streamlit UI):** 提供聊天窗口、服务器列表管理面板、以及实时命令执行滚动条。
*   **大脑层 (OpenRouter Agent):**
    *   构造 System Prompt，注入 Linux 专家知识。
    *   利用 Function Calling（或结构化输出）将用户语言转为 JSON 格式的操作指令。
*   **数据层 (SQLite DB):**
    *   `hosts`: 存储主机名、IP、端口、用户、认证方式。
    *   `credentials`: 存储加密后的私钥路径或密码（不存私钥本身）。
    *   `audit_logs`: 记录每一条 AI 生成的命令及其执行反馈。
*   **执行层 (SSH Coordinator):**
    *   从 SQLite 获取凭据，建立加密通道。
    *   执行命令并实时流式（Streaming）返回标准输出（stdout）。

## 4. 数据库设计 (SQLite)
使用 SQLite 存储关键配置，确保重启后环境不丢失。

```sql
-- 服务器清单表
CREATE TABLE hosts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alias TEXT NOT NULL,         -- 服务器别名，如 "北京生产机"
    hostname TEXT NOT NULL,      -- IP 或 域名
    port INTEGER DEFAULT 22,
    username TEXT NOT NULL,
    auth_type TEXT CHECK(auth_type IN ('key', 'password')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 凭据表
CREATE TABLE credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL,
    auth_type TEXT CHECK(auth_type IN ('key', 'password')),
    encrypted_key_path TEXT,
    encrypted_password TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(host_id) REFERENCES hosts(id)
);

-- 审计日志表
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER,
    user_query TEXT,             -- 用户原始提问
    ai_command TEXT,             -- AI 生成的命令
    exit_code INTEGER,
    output TEXT,                 -- 执行结果快照
    executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(host_id) REFERENCES hosts(id)
);
```

## 5. 核心业务流程

### 第一步：意图识别与参数补全
用户输入：“帮我查一下 Web 服务器的内存。”
系统会先尝试从用户输入中直接匹配别名，若未命中则交由 OpenRouter 从可选别名中选择目标：
*   **Action:** `check_memory`
*   **Target:** Web 服务器 (系统自动匹配 SQLite 中的别名)
*   **Prompt:** 结合历史，生成 `free -h`。

### 第二步：安全决策（Security Guardrail）
系统检测生成命令的危险等级：
*   **Safe:** 直接执行（如 `ls`, `df`, `uptime`）。
*   **Risky:** 暂停并弹出 UI 确认框（如 `rm`, `kill`, `docker stop`）。

### 第三步：SSH 异步执行
利用 Python 的 `threading` 或 `asyncio` 开启 SSH 任务，防止长时间执行导致 UI 卡死，并通过回调函数将结果存入 SQLite 审计表。

## 6. 关键代码片段预览 (Python)

### 6.1 OpenRouter 交互封装

```python
import requests
import json

def generate_command(user_input, server_context):
    api_key = "YOUR_OPENROUTER_API_KEY"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # 构造 System Prompt 确保 AI 只输出 JSON 命令
    system_prompt = "You are a Linux Expert. Output only valid shell commands inside a JSON object: {'cmd': '...'}"
    
    payload = {
        "model": "google/gemini-3-flash-preview",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {server_context}. Task: {user_input}"}
        ]
    }
    
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']
```

## 7. 安全性与隐私设计
*   **API 密钥保护:** OpenRouter 的 `API KEY` 与 `CREDENTIALS_ENCRYPT_KEY` 存储在本地 `.env` 文件中，不进入代码。
*   **凭据解耦:** SQLite 仅存储私钥路径或密码的**加密值**。用户需保证本地文件系统的权限安全。
*   **脱敏处理:** 在发送给 OpenRouter 的 Prompt 中，自动过滤掉服务器的真实 IP，仅使用“别名”替代，防止网络拓扑泄露。
*   **本地审计:** 即使 AI 误删了文件，用户也可以在本地 SQLite 中查到具体是哪一秒、生成的哪条命令导致的，方便溯源。
*   **密钥生成:** 可使用 `Fernet.generate_key()` 生成 `CREDENTIALS_ENCRYPT_KEY`。

## 8. 未来扩展
*   **RAG 增强:** 将服务器的 `/etc/*` 配置文件索引到本地向量库，AI 以后能回答“我的 Nginx 为什么报错？”
*   **多机并发:** 一键对 SQLite 选中的 10 台服务器执行相同命令。
*   **监控可视化:** AI 定时轮询 SQLite 中的主机，生成资源占用图表。
