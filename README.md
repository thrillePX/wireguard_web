# WireGuard 连接管理器

> 一个运行在 macOS 本地的 WireGuard VPN 客户端管理器

[English](./README_EN.md) | 简体中文

## 📖 项目概述

### 核心定位
本项目是一个 **WireGuard 客户端管理器**，用于管理本机上的多个 WireGuard 连接配置，实现一键连接/断开、流量监控和智能排序。

### 适用场景
```
┌─────────────────────────────────────────┐
│   你的 Mac (客户端管理器)                │
└─────────────────────────────────────────┘
        │
        ├──→ home_px    → 家庭网络
        ├──→ work_px    → 工作网络
        ├──→ vps        → VPS 服务器
        └──→ ...        → 其他 VPN
```

## ✨ 功能特性

### 连接管理
- ✅ 一键连接/断开 WireGuard VPN
- ✅ 可视化表单创建连接（自动生成密钥）
- ✅ 导入/导出配置文件
- ✅ 智能排序（已连接 → 固定 → 使用频率）
- ✅ 固定常用连接置顶

### 实时监控
- 📊 实时流速监控（bit/s）
- 📈 折线图趋势展示
- 🖱 鼠标悬停查看历史数据
- ⏱ 显示连接运行时长

### 网络拓扑
- 🌐 可视化网络拓扑图
- 🔍 网段搜索过滤
- 📋 查看全部路由网段

### 表单创建
- 🔑 自动生成公私钥对
- 📤 从私钥派生公钥显示
- 📝 表单式编辑配置
- 📄 保留原始文本编辑

## 🏗 技术架构

### 技术栈
```
前端: Vue 3 + Vite + Vue Router
后端: Python Flask
通信: RESTful API
平台: macOS / Linux
```

### 架构图
```
┌──────────────────────────────────────────────┐
│                  前端 (Vue 3)                │
│  ┌────────────┬────────────┬──────────────┐  │
│  │ 连接列表   │ 网络拓扑   │  连接详情     │  │
│  └────────────┴────────────┴──────────────┘  │
└──────────────────────────────────────────────┘
                      │ HTTP API
                      ▼
┌──────────────────────────────────────────────┐
│                  后端 (Flask)                 │
│  ┌────────────────────────────────────────┐ │
│  │         WireGuardManager              │ │
│  │  • 连接/断开 WireGuard                │ │
│  │  • 解析配置文件                        │ │
│  │  • 获取流量统计                       │ │
│  └────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│              系统命令                          │
│  • wg-quick up/down    (需要 sudo)          │
│  • wg show             (获取状态)           │
│  • ifconfig            (macOS 检测接口)      │
└──────────────────────────────────────────────┘
```

## 📁 文件结构

```
wireguardweb/
├── backend/
│   ├── app.py                 # Flask 主应用 (API 路由)
│   ├── wireguard_manager.py   # WireGuard 核心管理类
│   ├── config.py              # 配置 (端口、路径)
│   └── requirements.txt       # Python 依赖
│
├── frontend/
│   ├── src/
│   │   ├── App.vue                    # 根组件 (导航栏)
│   │   ├── main.js                    # Vue 入口
│   │   ├── router/
│   │   │   └── index.js              # 路由配置
│   │   ├── api/
│   │   │   └── index.js              # API 调用封装
│   │   ├── composables/
│   │   │   └── useConnectionHistory.js # 连接历史追踪
│   │   └── views/
│   │       ├── ConnectionList.vue    # 连接列表页
│   │       ├── ConnectionDetail.vue  # 连接详情页
│   │       ├── Topology.vue          # 网络拓扑图
│   │       └── Settings.vue          # 设置页
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
│
├── start.sh                  # 一键启动脚本
└── README.md
```

## 🚀 快速开始

### 环境要求
- macOS / Linux
- Python 3.8+
- Node.js 16+
- WireGuard 已安装

### 安装 WireGuard

**macOS (使用 Homebrew):**
```bash
brew install wireguard-tools
```

**Ubuntu/Debian:**
```bash
sudo apt install wireguard
```

### 启动应用

```bash
cd wireguardweb

# 一键启动（推荐）
chmod +x start.sh
./start.sh

# 或者手动启动
# 终端 1: 后端 (需要 sudo)
cd backend
sudo pip install -r requirements.txt
sudo python3 app.py

# 终端 2: 前端
cd frontend
npm install
npm run dev
```

### 访问地址
- 前端: http://localhost:3000
- 后端: http://localhost:5001

## 🔌 API 设计

### 后端 API 端点

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | `/api/connections` | 列出所有连接 |
| GET | `/api/connections/:name` | 获取连接详情 |
| POST | `/api/connections/:name/connect` | 连接 |
| POST | `/api/connections/:name/disconnect` | 断开 |
| POST | `/api/connections/:name/status` | 获取状态 |
| POST | `/api/connections/import` | 导入配置 |
| GET | `/api/connections/:name/export` | 导出配置 |
| PUT | `/api/connections/:name` | 更新配置 |
| DELETE | `/api/connections/:name` | 删除连接 |
| GET | `/api/config/path` | 获取配置路径 |
| POST | `/api/config/path` | 设置配置路径 |
| POST | `/api/keys/generate` | 生成密钥对 |
| POST | `/api/keys/preshared` | 生成预共享密钥 |
| POST | `/api/keys/derive` | 从私钥派生公钥 |

## ⚙️ 配置文件格式

### 配置文件路径
- **默认**: `/etc/wireguard/`
- **可配置**: 可在设置页面修改

### 配置文件格式
```ini
[Interface]
PrivateKey = <your-private-key>
Address = 10.0.0.2/24
ListenPort = 51820
DNS = 223.5.5.5
MTU = 1360

[Peer]
PublicKey = <server-public-key>
PresharedKey = <optional-preshared-key>
Endpoint = vpn.example.com:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
```

### Interface 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| PrivateKey | ✅ | 本地私钥 |
| Address | ✅ | 本地隧道 IP |
| ListenPort | ❌ | 监听 UDP 端口（默认随机） |
| DNS | ❌ | DNS 服务器 |
| MTU | ❌ | 最大传输单元（默认 1360） |

### Peer 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| PublicKey | ✅ | 对端公钥 |
| PresharedKey | ❌ | 抗量子密钥 |
| Endpoint | ✅ | 对端地址:端口 |
| AllowedIPs | ✅ | 路由哪些流量走 VPN |
| PersistentKeepalive | ❌ | 保活间隔（NAT 环境建议 25） |

## 🎯 核心功能设计

### 1. 连接列表

#### 智能排序算法
```
排序优先级 (分数越高越靠前):
1. 已连接: +100000 分
2. 已固定 (📌): +50000 分
3. 使用频率: count × 100 分
4. 最后使用时间: timestamp / 1000000 分
```

### 2. 连接详情 - 实时流速监控

#### 流速计算
```javascript
speed_bps = (current_bytes - last_bytes) / time_diff × 8
// 单位: bit/s (不是 byte/s)

function formatSpeed(bitsPerSecond) {
  // bps → Kbps → Mbps → Gbps
  // 使用 1000 进制 (网络标准)
}
```

#### 折线图实现
- **SVG 绘制**: 响应式折线图
- **数据点**: 最多 30 个 (每秒更新)
- **交互**: 鼠标悬停显示详细数据
- **渐变填充**: 下载(绿)、上传(蓝)

### 3. 网络拓扑

#### 树形结构设计
```
💻 本机
└── 🌐 VPN_NAME (已连接)
      ├── 📍 10.0.0.0/24
      ├── 📍 192.168.1.0/24
      └── 📍 192.168.100.0/24
          └── [查看全部 N 个网段]
```

## 🔧 开发注意事项

### 1. macOS vs Linux 差异
```python
# 检测系统
import platform
if platform.system() == 'Darwin':
    # macOS: 使用 ifconfig, WireGuard 接口名是 utunX
    subprocess.run(['ifconfig'])
else:
    # Linux: 使用 ip, wg
    subprocess.run(['ip', 'link', 'show'])
```

### 2. 权限问题
- **后端必须用 sudo 运行**: 因为 wg-quick 需要 root 权限
- **配置文件权限**: 需要确保 Flask 进程能读取 /etc/wireguard/

### 3. 单位转换
```javascript
// 网络速率标准使用 bit/s
// 1 Byte = 8 bits
bytes_to_bits = bytes × 8

// 进制
// 存储单位: 1024 进制 (1 KB = 1024 B)
// 网络速率: 1000 进制 (1 Kbps = 1000 bps)
```

## 📝 维护记录

| 日期 | 版本 | 更新内容 |
|------|------|---------|
| 2024-03-29 | v1.0 | 初始版本，连接管理 |
| 2024-03-29 | v1.1 | 添加拓扑图 |
| 2024-03-29 | v1.2 | 添加流速监控、折线图 |
| 2024-03-29 | v1.3 | 添加智能排序、固定功能 |
| 2024-03-29 | v1.4 | 重新设计添加连接表单，支持表单创建和密钥生成 |
| 2024-03-29 | v1.5 | 添加 ListenPort；编辑配置支持表单式编辑 |
| 2024-03-29 | v1.6 | 从私钥派生公钥功能；首页默认显示已连接 |
| 2024-03-29 | v1.7 | 网络拓扑网段搜索过滤；优化流速图交互样式 |
| 2024-03-29 | v1.8 | 添加连接运行时长显示 |

## 🙏 致谢

- [WireGuard](https://www.wireguard.com/)
- [Vue.js](https://vuejs.org/)
- [Flask](https://flask.palletsprojects.com/)

## 📄 许可证

MIT License
