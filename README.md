# WireGuard 连接管理器

> 一个运行在 macOS 本地的 WireGuard VPN 客户端管理器

## 📖 项目概述

### 核心定位
本项目是一个 **WireGuard 客户端管理器**，而非服务端管理器。设计用于管理本机上的多个 WireGuard 连接配置，实现一键连接/断开、流量监控和智能排序。

### 适用场景
```
┌─────────────────────────────────────────┐
│   你的 Mac (客户端管理器)                │
└─────────────────────────────────────────┘
        │
        ├──→ home_px    → 家庭网络
        ├──→ work_px    → 工作网络
        ├──→ vps        → VPS 服务器
        └──→ D20        → 其他 VPN
```

### 与服务端管理器的区别

| 特性 | 服务端管理器 | 客户端管理器（我们的） |
|------|-------------|---------------------|
| **位置** | 服务器上运行 | 客户端设备上运行 |
| **功能** | 添加 Peer | 管理自己的连接 |
| **操作** | 启动接口、添加 peer | 连接/断开、查看流量 |
| **权限** | 需要 root | 需要 root（管理网络接口） |

## 🏗 技术架构

### 技术栈
```
前端: Vue 3 + Vite + Vue Router
后端: Python Flask
通信: RESTful API
平台: macOS (Darwin)
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
│   │       ├── ConnectionDetail.vue  # 连接详情页 (含流速监控)
│   │       ├── Topology.vue          # 网络拓扑图
│   │       └── Settings.vue          # 设置页
│   ├── package.json
│   ├── vite.config.js         # Vite 配置 (代理 API)
│   └── index.html
│
├── start.sh                  # 一键启动脚本 (需要 sudo)
└── README.md
```

## 🎯 核心功能设计

### 1. 连接列表 (ConnectionList.vue)

#### 智能排序算法
```javascript
排序优先级 (分数越高越靠前):
1. 已连接: +100000 分
2. 已固定 (📌): +50000 分
3. 使用频率: count × 100 分
4. 最后使用时间: timestamp / 1000000 分
```

#### 连接历史追踪
- **存储位置**: localStorage (`wireguard_connection_history`)
- **数据结构**:
  ```javascript
  {
    "home_px": {
      "lastUsed": 1699999999999,  // 时间戳
      "count": 5,                  // 使用次数
      "pinned": true               // 是否固定
    }
  }
  ```

#### 功能
- ✅ 显示所有 WireGuard 配置
- ✅ 实时连接状态 (已连接/未连接)
- ✅ 一键连接/断开
- ✅ 固定连接 (📌)
- ✅ 导入/导出配置
- ✅ 删除连接
- ✅ **默认仅显示已连接的 VPN**
- ✅ **支持筛选切换**

### 2. 连接详情 (ConnectionDetail.vue)

#### 实时流速监控
```javascript
// 流速计算
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

#### 关键实现
```javascript
// 1. 定时获取流量数据
speedInterval = setInterval(() => {
  api.getConnection(name).then(updateSpeed)
}, 1000)

// 2. 计算速度
currentSpeed.rx = (rx - lastRx) / timeDiff * 8
currentSpeed.tx = (tx - lastTx) / timeDiff * 8

// 3. 更新图表路径
updateChartPaths()  // 生成 SVG path
```

### 3. 网络拓扑图 (Topology.vue)

#### 树形结构设计
```
💻 本机
└── 🌐 home_px (已连接)
      ├── 📍 10.91.8.0/24
      ├── 📍 192.168.0.0/24
      └── 📍 192.168.100.0/24
          └── [查看全部 41 个网段]
```

#### 数据解析
```javascript
// 解析 AllowedIPs (可能很长)
function parseAllowedIPs(allowedIPs) {
  return allowedIPs.split(',').map(ip => ip.trim())
}

// 显示限制: 最多 8 个 + "查看全部" 按钮
```

#### 搜索过滤功能
```javascript
// 支持模糊匹配
searchQuery: "192"  // 匹配 192.168.x.x

// 实时过滤 VPN 列表和网段
filteredConnections = connections.filter(c => {
  if (filterOnlyConnected) return c.connected
  return true
})

// 网段搜索
filteredAllowedIPs = allIPs.filter(ip => 
  ip.toLowerCase().includes(query.toLowerCase())
)
```

### 4. macOS 特性处理

#### 接口检测
```python
# Linux: ip link show wg0
# macOS: ifconfig | grep utun

def get_interface_name(config_name):
    # 从配置文件读取 Address (如 10.91.8.2)
    # 在 ifconfig 输出中查找对应 IP
    # macOS 上 WireGuard 使用 utun 接口
```

#### 权限要求
```bash
# 需要 sudo 运行
sudo python3 app.py

# wg-quick 需要 root 权限管理网络接口
wg-quick up /etc/wireguard/home_px.conf
```

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

### 请求/响应示例

```javascript
// 连接
POST /api/connections/home_px/connect
Response: { "message": "连接成功" }

// 获取详情
GET /api/connections/home_px
Response: {
  "name": "home_px",
  "connected": true,
  "interface": {
    "Address": "10.91.8.2/24",
    "DNS": "223.5.5.5"
  },
  "peer": {
    "Endpoint": "home.pengxiaocloud.top:56562",
    "AllowedIPs": "10.91.8.0/24,192.168.0.0/24"
  },
  "status": {
    "interface": "utun5",
    "peers": [{
      "endpoint": "home.pengxiaocloud.top:56562",
      "transfer": { "rx": 123456, "tx": 78901 },
      "latest_handshake": "2 minutes, 23 seconds ago"
    }]
  }
}
```

### 密钥相关 API

```javascript
// 生成密钥对
POST /api/keys/generate
Response: {
  "privateKey": "yAnSxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx=",
  "publicKey": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx="
}

// 生成预共享密钥
POST /api/keys/preshared
Response: {
  "presharedKey": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx="
}

// 从私钥派生公钥
POST /api/keys/derive
Body: { "privateKey": "yAnSxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx=" }
Response: {
  "publicKey": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx="
}
```

## ⚙️ 配置文件管理

### 配置文件路径
- **默认**: `/etc/wireguard/`
- **可配置**: 可在设置页面修改

### 配置文件格式
```ini
[Interface]
PrivateKey = <your-private-key>
Address = 10.91.8.2/24
ListenPort = 51820
DNS = 223.5.5.5
MTU = 1360

[Peer]
PublicKey = <server-public-key>
PresharedKey = <optional-preshared-key>
Endpoint = home.pengxiaocloud.top:56562
AllowedIPs = 10.91.8.0/24,192.168.0.0/24
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

## 🚀 启动方式

### 方式一: 使用启动脚本
```bash
cd /Users/pengxiao/py/wireguardweb
chmod +x start.sh
./start.sh
# 会提示输入 sudo 密码
```

### 方式二: 手动启动
```bash
# 终端 1: 后端 (需要 sudo)
cd backend
sudo python3 app.py  # 端口 5001

# 终端 2: 前端
cd frontend
npm run dev  # 端口 3000
```

### 访问地址
- 前端: http://localhost:3000
- 后端: http://localhost:5001

## 📊 数据流

### 连接流程
```
用户点击"连接"
    ↓
前端: handleConnect(name)
    ↓
API: POST /api/connections/:name/connect
    ↓
后端: wm.connect(name)
    ↓
系统: wg-quick up /etc/wireguard/:name.conf
    ↓
返回结果给前端
    ↓
刷新连接列表
```

### 流量监控流程
```
页面加载
    ↓
启动 speedInterval (每秒)
    ↓
GET /api/connections/:name
    ↓
解析 wg show utunX 输出
    ↓
计算速度 = (当前 - 上次) / 间隔 × 8
    ↓
更新 speedHistory 数组
    ↓
重新渲染折线图
```

## 🎨 UI 设计

### 配色方案
```css
--primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--success: #27ae60;  /* 已连接/下载 */
--info: #3498db;      /* 上传 */
--danger: #e74c3c;   /* 断开/错误 */
```

### 组件状态
| 组件 | 状态 | 样式 |
|-----|------|------|
| 连接卡片 | 已连接 | 左边框绿色, 状态点亮 |
| 连接卡片 | 未连接 | 左边框灰色, 状态暗淡 |
| VPN 节点 | 已连接 | 边框绿色, 图标 🌐 |
| VPN 节点 | 未连接 | 边框灰色, 图标 ⚪ |

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

### 4. 性能优化
```javascript
// 限制历史数据量
MAX_HISTORY = 30  // 只保留 30 秒数据

// 节流更新
// 避免过于频繁的 API 调用
```

## 🔄 后续开发建议

### 可添加功能
1. **连接超时设置**: 自动断开空闲连接
2. **开机启动**: macOS LaunchAgent
3. **DNS 泄漏保护**: 切换 VPN 时自动管理 DNS
4. **延迟测试**: 测量到各 VPN 的延迟
5. **流量统计**: 每日/每月流量报告
6. **配置文件同步**: 支持云端同步
7. **快捷键**: 全局快捷键快速切换连接

### 潜在问题
1. **多个 VPN 同时连接**: 可能 IP 冲突
2. **DNS 污染**: 需要妥善处理 DNS 设置
3. **断线重连**: 添加自动重连机制

## 📝 维护记录

| 日期 | 版本 | 更新内容 |
|------|------|---------|
| 2024-03-29 | v1.0 | 初始版本，连接管理 |
| 2024-03-29 | v1.1 | 添加拓扑图 |
| 2024-03-29 | v1.2 | 添加流速监控、折线图 |
| 2024-03-29 | v1.3 | 添加智能排序、固定功能 |
| 2024-03-29 | v1.4 | 重新设计添加连接表单，支持表单创建和密钥生成，生成私钥时自动显示对应公钥 |
| 2024-03-29 | v1.5 | 添加 ListenPort 字段；编辑配置支持表单式编辑，保留原始文本编辑选项 |
| 2024-03-29 | v1.6 | 添加从私钥派生公钥功能（编辑时可自动显示）；首页默认显示已连接 VPN |
| 2024-03-29 | v1.7 | 网络拓扑添加网段搜索过滤功能；优化流速图交互样式（十字准心线指示器） |

## 🙏 致谢

- WireGuard: https://www.wireguard.com/
- Vue.js: https://vuejs.org/
- Flask: https://flask.palletsprojects.com/
