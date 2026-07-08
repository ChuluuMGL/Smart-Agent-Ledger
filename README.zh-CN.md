# Smart Agent Ledger

从**本仓库目录**即可运行。首次体验推荐先用 demo mode，它不会读取本机真实 Agent 日志、订阅文件或团队节点配置。

## 0. Demo 快速体验

```bash
git clone https://github.com/ChuluuMGL/Smart-Agent-Ledger.git
cd Smart-Agent-Ledger
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
SMART_AGENT_LEDGER_DEMO_MODE=1 uvicorn gateway:app --host 127.0.0.1 --port 8001 --no-access-log
open http://127.0.0.1:8001/ui
```

## 1. 准备环境（首次）

```bash
# 进入项目目录
git clone https://github.com/ChuluuMGL/Smart-Agent-Ledger.git
cd Smart-Agent-Ledger

# 创建虚拟环境并安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 2. 设置 env（密钥）

真实模型代理需要 `keys.env`。如果只是看 demo dashboard，可以跳过本节。

```bash
# 复制模板
cp keys.env.example keys.env

# 用编辑器打开 keys.env，填入 DeepSeek / GLM / Qwen 的真实 key，保存
open -e keys.env

# 限制权限（建议）
chmod 600 keys.env
```

**说明**：`keys.env` 已在 `.gitignore` 中，不会被提交。不要往 `keys.env.example` 里填真实 key。

## 3. 启动服务

**方式 A：用脚本（推荐，自动加载 keys.env）**

```bash
chmod +x run.sh
./run.sh
```

**方式 B：手动加载 env 再启动**

```bash
source venv/bin/activate
# 加载 keys.env（跳过注释行）
set -a
source <(grep -v '^#' keys.env | grep -v '^[[:space:]]*$' | sed 's/^/export /')
set +a
uvicorn gateway:app --host 0.0.0.0 --port 8001
```

**方式 C：一行 export（keys.env 无空格、无 # 时可用）**

```bash
source venv/bin/activate
export $(grep -v '^#' keys.env | xargs)
uvicorn gateway:app --host 0.0.0.0 --port 8001
```

## 4. 验证

- 健康检查：`curl http://localhost:8001/health`
- 客户端 base_url：`http://<本机IP>:8001/v1`

更多说明见英文 README 和 `OPEN_SOURCE_READINESS.md`。

---

## 4.1 可视与调节（Web + CLI）

- **Web 仪表盘**：浏览器打开 **http://localhost:8001/ui**，可看状态、按 provider 请求数、词表与 provider 列表（只读，每 30 秒刷新）
- **Agent 工作台**：同一页面可看 Agent / 项目 / 任务 / 会话 / token / 已知金额；接口为 `GET /agent-ledger`
- **订阅额度**：同一页面可看模型订阅、续费提醒、额度重置和路由避让建议；接口为 `GET /subscription-ledger`
- **CLI**：`python3 cli.py status` | `stats` | `config` | `ledger` | `subscriptions` | `logs`
- **HTTP**：`GET /health`、`GET /stats`、`GET /config`、`GET /agent-ledger`、`GET /subscription-ledger`
- **调词表/权重**：编辑 `data/routing-keywords.json` 或相关 provider 配置后重启服务。
- **Agent 标注**：请求网关时可带 `X-Agent-Name`、`X-Project`、`X-Task`、`X-Session-Id`，或在请求体里放 `metadata`。

---

## 5. 后台运行

公开版推荐用 Docker 或你自己的进程管理工具运行，避免绑定某一台机器的本机路径。

```bash
docker build -t smart-agent-ledger .
docker run -p 8001:8001 -v "$PWD/data:/app/data" smart-agent-ledger
```

也可以用 `nohup ./run.sh >> gateway.log 2>&1 &` 在本机后台运行。应用结构化日志看 `tail -f data/gateway-app.log`，启动失败再看 `gateway.log`。要停掉：`kill $(lsof -t -i:8001)`。
