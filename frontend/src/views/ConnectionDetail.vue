<template>
  <div class="connection-detail">
    <div class="header">
      <button @click="goBack" class="btn-back">← 返回列表</button>
      <h2>{{ connectionName }} - 连接详情</h2>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      加载中...
    </div>
    
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <div v-else class="detail-content">
      <div class="section status-section">
        <div class="status-header">
          <div class="connection-status">
            <span :class="['status-indicator', connection.connected ? 'connected' : 'disconnected']"></span>
            <h3>{{ connection.connected ? '已连接' : '未连接' }}</h3>
          </div>
          <div class="status-actions">
            <button 
              v-if="!connection.connected" 
              @click="handleConnect" 
              class="btn-connect"
            >
              连接
            </button>
            <button 
              v-else 
              @click="handleDisconnect" 
              class="btn-disconnect"
            >
              断开
            </button>
          </div>
        </div>

        <div v-if="connection.connected && connection.status" class="connection-stats">
          <div class="stat-card">
            <div class="stat-label">网络接口</div>
            <div class="stat-value">{{ connection.status.interface }}</div>
          </div>
          <div v-if="connection.status.peers && connection.status.peers.length > 0" class="stat-card">
            <div class="stat-label">服务端点</div>
            <div class="stat-value">{{ connection.status.peers[0].endpoint || 'N/A' }}</div>
          </div>
          <div v-if="connection.status.peers && connection.status.peers.length > 0" class="stat-card">
            <div class="stat-label">最后握手</div>
            <div class="stat-value">{{ formatTimeAgo(connection.status.peers[0].latest_handshake) }}</div>
          </div>
        </div>

        <div v-if="connection.connected && connection.status && connection.status.peers && connection.status.peers.length > 0" class="traffic-section">
          <h4>📊 实时流速</h4>
          <div class="speed-display">
            <div class="speed-item download">
              <div class="speed-icon">↓</div>
              <div class="speed-info">
                <div class="speed-label">下载速度</div>
                <div class="speed-value">{{ formatSpeed(currentSpeed.rx) }}</div>
              </div>
            </div>
            <div class="speed-item upload">
              <div class="speed-icon">↑</div>
              <div class="speed-info">
                <div class="speed-label">上传速度</div>
                <div class="speed-value">{{ formatSpeed(currentSpeed.tx) }}</div>
              </div>
            </div>
          </div>
          
          <div class="speed-chart">
            <div class="chart-title">📈 流速趋势 (最近 {{ speedHistory.length }} 秒)</div>
            <svg class="line-chart" viewBox="0 0 400 150" preserveAspectRatio="none" @mousemove="handleChartHover" @mouseleave="hideTooltip">
              <defs>
                <linearGradient id="downloadGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" style="stop-color:#27ae60;stop-opacity:0.3" />
                  <stop offset="100%" style="stop-color:#27ae60;stop-opacity:0" />
                </linearGradient>
                <linearGradient id="uploadGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" style="stop-color:#3498db;stop-opacity:0.3" />
                  <stop offset="100%" style="stop-color:#3498db;stop-opacity:0" />
                </linearGradient>
              </defs>
              
              <path 
                v-if="downloadAreaPath" 
                :d="downloadAreaPath" 
                fill="url(#downloadGradient)"
              />
              <path 
                v-if="uploadAreaPath" 
                :d="uploadAreaPath" 
                fill="url(#uploadGradient)"
              />
              
              <path 
                v-if="downloadLinePath" 
                :d="downloadLinePath" 
                fill="none" 
                stroke="#27ae60" 
                stroke-width="2"
                class="chart-line"
              />
              <path 
                v-if="uploadLinePath" 
                :d="uploadLinePath" 
                fill="none" 
                stroke="#3498db" 
                stroke-width="2"
                class="chart-line"
              />
              
              <g v-if="hoveredPoint" class="hover-indicator">
                <line :x1="hoveredPoint.x" y1="0" :x2="hoveredPoint.x" y2="150" stroke="#667eea" stroke-width="1.5"/>
                <line x1="0" :y1="hoveredPoint.y" x2="400" :y2="hoveredPoint.y" stroke="#667eea" stroke-width="1" stroke-dasharray="3"/>
              </g>
              
              <line x1="0" y1="0" x2="0" y2="150" stroke="#ddd" stroke-width="1"/>
              <line x1="0" y1="150" x2="400" y2="150" stroke="#ddd" stroke-width="1"/>
            </svg>
            
            <div v-if="hoveredPoint" class="chart-tooltip" :style="{ left: tooltipPosition.left, top: tooltipPosition.top }">
              <div class="tooltip-title">{{ formatTime(hoveredPoint.time) }}</div>
              <div class="tooltip-row download">
                <span class="dot"></span>
                <span class="label">下载:</span>
                <span class="value">{{ formatSpeed(hoveredPoint.rx) }}</span>
              </div>
              <div class="tooltip-row upload">
                <span class="dot"></span>
                <span class="label">上传:</span>
                <span class="value">{{ formatSpeed(hoveredPoint.tx) }}</span>
              </div>
            </div>
            
            <div class="chart-legend">
              <span class="legend-item"><span class="dot download"></span> 下载</span>
              <span class="legend-item"><span class="dot upload"></span> 上传</span>
            </div>
          </div>
          
          <div class="total-traffic">
            <div class="total-item">
              <span class="total-label">总接收:</span>
              <span class="total-value">{{ formatBytes(connection.status.peers[0].transfer.rx) }}</span>
            </div>
            <div class="total-item">
              <span class="total-label">总发送:</span>
              <span class="total-value">{{ formatBytes(connection.status.peers[0].transfer.tx) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="section">
        <h3>配置信息</h3>
        <div class="config-section">
          <div v-if="connection.interface" class="config-block">
            <h4>[Interface]</h4>
            <div class="config-item">
              <span class="key">Address</span>
              <span class="value">{{ connection.interface.Address || 'N/A' }}</span>
            </div>
            <div v-if="connection.interface.DNS" class="config-item">
              <span class="key">DNS</span>
              <span class="value">{{ connection.interface.DNS }}</span>
            </div>
            <div v-if="connection.interface.MTU" class="config-item">
              <span class="key">MTU</span>
              <span class="value">{{ connection.interface.MTU }}</span>
            </div>
          </div>

          <div v-if="connection.peer" class="config-block">
            <h4>[Peer]</h4>
            <div class="config-item">
              <span class="key">Endpoint</span>
              <span class="value">{{ connection.peer.Endpoint || 'N/A' }}</span>
            </div>
            <div class="config-item">
              <span class="key">AllowedIPs</span>
              <span class="value allowed-ips">{{ connection.peer.AllowedIPs || 'N/A' }}</span>
            </div>
            <div v-if="connection.peer.PersistentKeepalive" class="config-item">
              <span class="key">PersistentKeepalive</span>
              <span class="value">{{ connection.peer.PersistentKeepalive }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="section actions-section">
        <h3>操作</h3>
        <div class="action-buttons">
          <button @click="handleExport" class="btn-secondary">
            导出配置
          </button>
          <button @click="openEditModal" class="btn-info">
            编辑配置
          </button>
          <button @click="confirmDelete" class="btn-danger">
            删除连接
          </button>
        </div>
      </div>
    </div>

    <div v-if="showEditModal" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal modal-large">
        <div class="modal-header">
          <h3>编辑配置</h3>
          <button @click="closeEditModal" class="close-btn">&times;</button>
        </div>
        
        <div class="modal-tabs">
          <button 
            :class="['tab-btn', { active: editMode === 'form' }]"
            @click="editMode = 'form'"
          >
            📝 表单编辑
          </button>
          <button 
            :class="['tab-btn', { active: editMode === 'raw' }]"
            @click="editMode = 'raw'"
          >
            📄 原始文本
          </button>
        </div>
        
        <div v-if="editMode === 'form'" class="modal-body">
          <form @submit.prevent="saveConfig">
            <div class="form-section">
              <h4>🔐 本地接口 (Interface)</h4>
              
              <div class="form-group">
                <label>私钥 (PrivateKey)</label>
                <div class="input-with-btn">
                  <input 
                    v-model="editForm.privateKey" 
                    required 
                    placeholder="点击生成获取私钥"
                    readonly
                  />
                  <button type="button" @click="generateEditKeys" class="btn-generate" :disabled="generatingKeys">
                    {{ generatingKeys ? '生成中...' : '🔑 生成' }}
                  </button>
                </div>
              </div>
              
              <div v-if="editForm.generatedPublicKey" class="form-group public-key-display">
                <label>📤 对应公钥</label>
                <div class="public-key-box">
                  <code>{{ editForm.generatedPublicKey }}</code>
                  <button type="button" @click="copyToClipboard(editForm.generatedPublicKey)" class="btn-copy">
                    📋 复制
                  </button>
                </div>
              </div>
              
              <div class="form-group">
                <label>本地地址 (Address)</label>
                <input v-model="editForm.address" required placeholder="例如: 10.0.0.2/24" />
              </div>
              
              <div class="form-row">
                <div class="form-group">
                  <label>监听端口 (ListenPort - 可选)</label>
                  <input 
                    v-model="editForm.listenPort" 
                    placeholder="随机端口"
                    type="number"
                    min="1"
                    max="65535"
                  />
                </div>
                <div class="form-group">
                  <label>DNS (可选)</label>
                  <input v-model="editForm.dns" placeholder="例如: 223.5.5.5" />
                </div>
              </div>
              
              <div class="form-group">
                <label>MTU (可选)</label>
                <input v-model="editForm.mtu" placeholder="默认: 1360" type="number" />
              </div>
            </div>
            
            <div class="form-section">
              <h4>🌐 对端节点 (Peer)</h4>
              
              <div class="form-group">
                <label>对端公钥 (PublicKey)</label>
                <input v-model="editForm.peerPublicKey" required placeholder="服务器提供的公钥" />
              </div>
              
              <div class="form-group">
                <label>预共享密钥 (PresharedKey - 可选)</label>
                <div class="input-with-btn">
                  <input 
                    v-model="editForm.presharedKey" 
                    placeholder="额外的安全密钥 (可选)"
                    readonly
                  />
                  <button type="button" @click="generateEditPresharedKey" class="btn-generate" :disabled="generatingKeys">
                    {{ generatingKeys ? '生成中...' : '🔑 生成' }}
                  </button>
                </div>
              </div>
              
              <div class="form-group">
                <label>服务端地址 (Endpoint)</label>
                <input v-model="editForm.endpoint" required placeholder="例如: vpn.example.com:51820" />
              </div>
              
              <div class="form-group">
                <label>允许的 IP (AllowedIPs)</label>
                <input v-model="editForm.allowedIPs" required placeholder="例如: 0.0.0.0/0, ::/0" />
              </div>
              
              <div class="form-group">
                <label>保活间隔 (PersistentKeepalive - 可选)</label>
                <input 
                  v-model="editForm.persistentKeepalive" 
                  placeholder="默认: 25 秒"
                  type="number"
                  min="0"
                  max="65535"
                />
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" @click="closeEditModal" class="btn-secondary">
                取消
              </button>
              <button type="submit" class="btn-primary" :disabled="saving">
                {{ saving ? '保存中...' : '保存' }}
              </button>
            </div>
          </form>
        </div>
        
        <div v-else class="modal-body">
          <form @submit.prevent="saveConfig">
            <div class="form-group">
              <label>配置文件内容</label>
              <textarea 
                v-model="editConfig" 
                required 
                rows="15"
              ></textarea>
            </div>

            <div class="modal-footer">
              <button type="button" @click="closeEditModal" class="btn-secondary">
                取消
              </button>
              <button type="submit" class="btn-primary" :disabled="saving">
                {{ saving ? '保存中...' : '保存' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from '../composables/useToast'
import { api } from '../api'

const router = useRouter()
const route = useRoute()
const toast = useToast()

const connectionName = route.params.name
const connection = ref({})
const loading = ref(true)
const error = ref('')
const showEditModal = ref(false)
const saving = ref(false)
const generatingKeys = ref(false)
const editMode = ref('form')
const editConfig = ref('')
const editForm = ref({
  privateKey: '',
  generatedPublicKey: '',
  address: '',
  listenPort: '',
  dns: '',
  mtu: '',
  peerPublicKey: '',
  presharedKey: '',
  endpoint: '',
  allowedIPs: '',
  persistentKeepalive: '25'
})
let refreshInterval = null
let speedInterval = null
let lastRx = 0
let lastTx = 0
let lastTime = 0

const currentSpeed = ref({ rx: 0, tx: 0 })
const speedHistory = ref([])
const MAX_HISTORY = 30

const downloadLinePath = ref('')
const uploadLinePath = ref('')
const downloadAreaPath = ref('')
const uploadAreaPath = ref('')
const hoveredPoint = ref(null)
const tooltipPosition = ref({ left: '0px', top: '0px' })

async function loadConnection() {
  try {
    const data = await api.getConnection(connectionName)
    connection.value = data.connection || data
    if (!connection.value) {
      error.value = '连接不存在'
    }
    
    if (connection.value.connected && connection.value.status) {
      updateSpeed()
    }
  } catch (err) {
    error.value = '加载失败: ' + err.message
  } finally {
    loading.value = false
  }
}

function updateSpeed() {
  if (!connection.value.connected || !connection.value.status || !connection.value.status.peers || !connection.value.status.peers[0]) {
    return
  }
  
  const peer = connection.value.status.peers[0]
  const now = Date.now()
  const rx = peer.transfer.rx
  const tx = peer.transfer.tx
  
  if (lastTime > 0) {
    const timeDiff = (now - lastTime) / 1000
    if (timeDiff > 0) {
      currentSpeed.value.rx = Math.max(0, (rx - lastRx) / timeDiff) * 8
      currentSpeed.value.tx = Math.max(0, (tx - lastTx) / timeDiff) * 8
      
      speedHistory.value.push({
        rx: currentSpeed.value.rx,
        tx: currentSpeed.value.tx,
        time: now
      })
      
      if (speedHistory.value.length > MAX_HISTORY) {
        speedHistory.value.shift()
      }
      
      updateChartPaths()
    }
  }
  
  lastRx = rx
  lastTx = tx
  lastTime = now
}

function formatSpeed(bitsPerSecond) {
  if (bitsPerSecond === 0) return '0 bps'
  const k = 1000
  const sizes = ['bps', 'Kbps', 'Mbps', 'Gbps']
  const i = Math.floor(Math.log(bitsPerSecond) / Math.log(k))
  return parseFloat((bitsPerSecond / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function handleChartHover(event) {
  if (speedHistory.value.length === 0) return
  
  const svg = event.currentTarget
  const rect = svg.getBoundingClientRect()
  const x = event.clientX - rect.left
  const relativeX = (x / rect.width) * 400
  
  const width = 400
  const padding = 10
  const chartWidth = width - padding * 2
  
  const index = Math.round((relativeX - padding) / chartWidth * (speedHistory.value.length - 1))
  const clampedIndex = Math.max(0, Math.min(speedHistory.value.length - 1, index))
  
  const point = speedHistory.value[clampedIndex]
  if (point) {
    const maxSpeed = Math.max(...speedHistory.value.flatMap(p => [p.rx, p.tx]), 1)
    const chartHeight = 130
    
    hoveredPoint.value = {
      x: padding + (clampedIndex / Math.max(speedHistory.value.length - 1, 1)) * chartWidth,
      y: 150 - padding - (point.rx / maxSpeed) * chartHeight,
      rx: point.rx,
      tx: point.tx,
      time: point.time
    }
    
    tooltipPosition.value = {
      left: (x > 200 ? x - 150 : x + 10) + 'px',
      top: '-10px'
    }
  }
}

function hideTooltip() {
  hoveredPoint.value = null
}

function updateChartPaths() {
  const width = 400
  const height = 150
  const padding = 10
  
  if (speedHistory.value.length === 0) {
    downloadLinePath.value = ''
    uploadLinePath.value = ''
    downloadAreaPath.value = ''
    uploadAreaPath.value = ''
    return
  }
  
  const maxSpeed = Math.max(...speedHistory.value.flatMap(p => [p.rx, p.tx]), 1)
  const chartWidth = width - padding * 2
  const chartHeight = height - padding * 2
  
  const downloadPoints = speedHistory.value.map((point, index) => {
    const x = padding + (index / Math.max(speedHistory.value.length - 1, 1)) * chartWidth
    const y = height - padding - (point.rx / maxSpeed) * chartHeight
    return { x, y }
  })
  
  const uploadPoints = speedHistory.value.map((point, index) => {
    const x = padding + (index / Math.max(speedHistory.value.length - 1, 1)) * chartWidth
    const y = height - padding - (point.tx / maxSpeed) * chartHeight
    return { x, y }
  })
  
  if (downloadPoints.length === 1) {
    downloadLinePath.value = `M ${downloadPoints[0].x} ${downloadPoints[0].y} L ${downloadPoints[0].x + 1} ${downloadPoints[0].y}`
    uploadLinePath.value = `M ${uploadPoints[0].x} ${uploadPoints[0].y} L ${uploadPoints[0].x + 1} ${uploadPoints[0].y}`
  } else {
    downloadLinePath.value = downloadPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
    uploadLinePath.value = uploadPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  }
  
  downloadAreaPath.value = downloadLinePath.value + 
    ` L ${padding + chartWidth} ${height - padding} L ${padding} ${height - padding} Z`
  
  uploadAreaPath.value = uploadLinePath.value + 
    ` L ${padding + chartWidth} ${height - padding} L ${padding} ${height - padding} Z`
}

function startSpeedMonitoring() {
  if (speedInterval) return
  
  speedInterval = setInterval(() => {
    if (connection.value.connected) {
      api.getConnection(connectionName).then(data => {
        if (data.connected && data.status) {
          connection.value.status = data.status
          updateSpeed()
        }
      }).catch(err => {
        console.error('获取速度失败:', err)
      })
    }
  }, 1000)
}

function stopSpeedMonitoring() {
  if (speedInterval) {
    clearInterval(speedInterval)
    speedInterval = null
  }
  currentSpeed.value = { rx: 0, tx: 0 }
  speedHistory.value = []
  lastRx = 0
  lastTx = 0
  lastTime = 0
  downloadLinePath.value = ''
  uploadLinePath.value = ''
  downloadAreaPath.value = ''
  uploadAreaPath.value = ''
  hoveredPoint.value = null
}

function goBack() {
  router.push('/')
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    toast.success('已复制到剪贴板')
  }).catch(() => {
    toast.error('复制失败')
  })
}

function formatTimeAgo(text) {
  if (!text) return 'N/A'
  if (typeof text !== 'string') return text
  return text
    .replace('week', '周')
    .replace('day', '天')
    .replace('hour', '小时')
    .replace('minute', '分钟')
    .replace('second', '秒')
    .replace('ago', '前')
}

async function handleConnect() {
  try {
    const result = await api.connect(connectionName)
    toast.success(result.message || '连接成功')
    loadConnection()
  } catch (err) {
    toast.error('连接失败: ' + err.message)
  }
}

async function handleDisconnect() {
  try {
    const result = await api.disconnect(connectionName)
    toast.success(result.message || '已断开')
    loadConnection()
  } catch (err) {
    toast.error('断开失败: ' + err.message)
  }
}

async function handleExport() {
  try {
    await api.exportConfig(connectionName)
    toast.success('配置文件已导出')
  } catch (err) {
    toast.error('导出失败: ' + err.message)
  }
}

async function confirmDelete() {
  if (confirm(`确定要删除连接 "${connectionName}" 吗？`)) {
    try {
      await api.deleteConnection(connectionName)
      toast.success('连接已删除')
      router.push('/')
    } catch (err) {
      toast.error('删除失败: ' + err.message)
    }
  }
}

function generateConfigText() {
  let config = ''
  
  if (connection.value.interface) {
    config += '[Interface]\n'
    if (connection.value.interface.PrivateKey) {
      config += `PrivateKey = ${connection.value.interface.PrivateKey}\n`
    }
    if (connection.value.interface.Address) {
      config += `Address = ${connection.value.interface.Address}\n`
    }
    if (connection.value.interface.DNS) {
      config += `DNS = ${connection.value.interface.DNS}\n`
    }
    if (connection.value.interface.MTU) {
      config += `MTU = ${connection.value.interface.MTU}\n`
    }
  }
  
  if (connection.value.peer) {
    config += '\n[Peer]\n'
    if (connection.value.peer.PublicKey) {
      config += `PublicKey = ${connection.value.peer.PublicKey}\n`
    }
    if (connection.value.peer.PresharedKey) {
      config += `PresharedKey = ${connection.value.peer.PresharedKey}\n`
    }
    if (connection.value.peer.Endpoint) {
      config += `Endpoint = ${connection.value.peer.Endpoint}\n`
    }
    if (connection.value.peer.AllowedIPs) {
      config += `AllowedIPs = ${connection.value.peer.AllowedIPs}\n`
    }
    if (connection.value.peer.PersistentKeepalive) {
      config += `PersistentKeepalive = ${connection.value.peer.PersistentKeepalive}\n`
    }
  }
  
  return config
}

async function saveConfig() {
  saving.value = true
  try {
    let config
    if (editMode.value === 'form') {
      config = generateConfigFromFormEdit()
    } else {
      config = editConfig.value
    }
    await api.updateConnection(connectionName, config)
    toast.success('配置已保存')
    showEditModal.value = false
    loadConnection()
  } catch (err) {
    toast.error('保存失败: ' + err.message)
  } finally {
    saving.value = false
  }
}

function openEditModal() {
  showEditModal.value = true
  editMode.value = 'form'
  parseConfigToForm()
}

function closeEditModal() {
  showEditModal.value = false
}

function parseConfigToForm() {
  const iface = connection.value.interface || {}
  const peer = connection.value.peer || {}
  
  editForm.value = {
    privateKey: iface.PrivateKey || '',
    generatedPublicKey: '',
    address: iface.Address || '',
    listenPort: iface.ListenPort || '',
    dns: iface.DNS || '',
    mtu: iface.MTU || '',
    peerPublicKey: peer.PublicKey || '',
    presharedKey: peer.PresharedKey || '',
    endpoint: peer.Endpoint || '',
    allowedIPs: peer.AllowedIPs || '',
    persistentKeepalive: peer.PersistentKeepalive || '25'
  }
  
  editConfig.value = generateConfigText()
  
  if (iface.PrivateKey) {
    derivePublicKeyForEdit(iface.PrivateKey)
  }
}

async function derivePublicKeyForEdit(privateKey) {
  try {
    const result = await api.derivePublicKey(privateKey)
    editForm.value.generatedPublicKey = result.publicKey
  } catch (error) {
    console.error('派生公钥失败:', error)
  }
}

function generateConfigFromFormEdit() {
  const form = editForm.value
  
  let config = `[Interface]\n`
  config += `PrivateKey = ${form.privateKey}\n`
  config += `Address = ${form.address}\n`
  
  if (form.listenPort) {
    config += `ListenPort = ${form.listenPort}\n`
  }
  
  if (form.dns) {
    config += `DNS = ${form.dns}\n`
  }
  
  if (form.mtu) {
    config += `MTU = ${form.mtu}\n`
  }
  
  config += `\n[Peer]\n`
  config += `PublicKey = ${form.peerPublicKey}\n`
  
  if (form.presharedKey) {
    config += `PresharedKey = ${form.presharedKey}\n`
  }
  
  config += `Endpoint = ${form.endpoint}\n`
  config += `AllowedIPs = ${form.allowedIPs}\n`
  
  if (form.persistentKeepalive) {
    config += `PersistentKeepalive = ${form.persistentKeepalive}\n`
  }
  
  return config
}

async function generateEditKeys() {
  try {
    generatingKeys.value = true
    const keys = await api.generateKeys()
    editForm.value.privateKey = keys.privateKey
    editForm.value.generatedPublicKey = keys.publicKey
  } catch (error) {
    toast.error('生成密钥失败: ' + error.message)
  } finally {
    generatingKeys.value = false
  }
}

async function generateEditPresharedKey() {
  try {
    generatingKeys.value = true
    const result = await api.generatePresharedKey()
    editForm.value.presharedKey = result.presharedKey
  } catch (error) {
    toast.error('生成预共享密钥失败: ' + error.message)
  } finally {
    generatingKeys.value = false
  }
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

onMounted(() => {
  loadConnection()
  refreshInterval = setInterval(loadConnection, 3000)
  startSpeedMonitoring()
  
  setTimeout(() => {
    editConfig.value = generateConfigText()
  }, 500)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  stopSpeedMonitoring()
})
</script>

<style scoped>
.header {
  margin-bottom: 2rem;
}

.btn-back {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  font-size: 1rem;
  margin-bottom: 0.5rem;
  padding: 0;
}

.btn-back:hover {
  text-decoration: underline;
}

.header h2 {
  color: #2c3e50;
}

.loading, .error {
  text-align: center;
  padding: 3rem;
}

.spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error {
  color: #e74c3c;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.section {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.section h3 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.status-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.status-section h3,
.status-section h4 {
  color: white;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.status-indicator {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: rgba(255,255,255,0.3);
}

.status-indicator.connected {
  background: #27ae60;
  box-shadow: 0 0 12px rgba(39, 174, 96, 0.8);
}

.status-indicator.disconnected {
  background: rgba(255,255,255,0.3);
}

.connection-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: rgba(255,255,255,0.1);
  padding: 1rem;
  border-radius: 8px;
}

.stat-label {
  font-size: 0.85rem;
  opacity: 0.8;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1rem;
  font-weight: 600;
  font-family: monospace;
}

.traffic-stats h4 {
  margin-bottom: 1rem;
  font-size: 1rem;
}

.traffic-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.traffic-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: rgba(255,255,255,0.1);
  padding: 1rem;
  border-radius: 8px;
}

.traffic-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: bold;
}

.traffic-label {
  font-size: 0.85rem;
  opacity: 0.8;
}

.traffic-value {
  font-size: 1.1rem;
  font-weight: 600;
  font-family: monospace;
}

.traffic-section {
  margin-top: 1.5rem;
}

.speed-display {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.speed-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(255,255,255,0.1);
  border-radius: 8px;
}

.speed-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
}

.speed-item.download .speed-icon {
  background: rgba(39, 174, 96, 0.3);
}

.speed-item.upload .speed-icon {
  background: rgba(52, 152, 219, 0.3);
}

.speed-info {
  flex: 1;
}

.speed-label {
  font-size: 0.9rem;
  opacity: 0.8;
  margin-bottom: 0.25rem;
}

.speed-value {
  font-size: 1.3rem;
  font-weight: 600;
  font-family: monospace;
}

.speed-item.download .speed-value {
  color: #27ae60;
}

.speed-item.upload .speed-value {
  color: #3498db;
}

.speed-chart {
  background: rgba(255,255,255,0.1);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  position: relative;
}

.speed-chart .chart-title {
  font-size: 0.9rem;
  margin-bottom: 1rem;
  opacity: 0.9;
}

.line-chart {
  width: 100%;
  height: 150px;
  background: rgba(255,255,255,0.05);
  border-radius: 8px;
}

.chart-line {
  stroke-linecap: round;
  stroke-linejoin: round;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-top: 1rem;
  font-size: 0.85rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  opacity: 0.9;
}

.legend-item .dot {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-item .dot.download {
  background: #27ae60;
}

.legend-item .dot.upload {
  background: #3498db;
}

.chart-tooltip {
  position: absolute;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.6rem 0.8rem;
  border-radius: 6px;
  font-size: 0.8rem;
  pointer-events: none;
  z-index: 100;
  min-width: 140px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.tooltip-title {
  font-weight: 600;
  margin-bottom: 0.4rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  font-size: 0.75rem;
}

.tooltip-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0.2rem 0;
}

.tooltip-row .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.tooltip-row.download .dot {
  background: #a8e6cf;
}

.tooltip-row.upload .dot {
  background: #88d3f5;
}

.tooltip-row .label {
  flex: 1;
  opacity: 0.9;
}

.tooltip-row .value {
  font-family: 'SF Mono', 'Monaco', monospace;
  font-weight: 600;
  font-weight: 600;
}

.hover-indicator {
  pointer-events: none;
}

.total-traffic {
  display: flex;
  justify-content: space-around;
  padding: 1rem;
  background: rgba(255,255,255,0.1);
  border-radius: 8px;
}

.total-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.total-label {
  font-size: 0.85rem;
  opacity: 0.8;
}

.total-value {
  font-size: 1rem;
  font-weight: 600;
  font-family: monospace;
}

.config-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.config-block {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 8px;
}

.config-block h4 {
  color: #667eea;
  margin-bottom: 0.75rem;
  font-size: 1rem;
}

.config-item {
  display: flex;
  padding: 0.5rem 0;
  border-bottom: 1px solid #e9ecef;
}

.config-item:last-child {
  border-bottom: none;
}

.config-item .key {
  width: 180px;
  color: #666;
  font-weight: 500;
}

.config-item .value {
  flex: 1;
  font-family: monospace;
  color: #333;
  word-break: break-all;
}

.config-item .value.allowed-ips {
  font-size: 0.85rem;
  line-height: 1.4;
}

.actions-section .action-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 2rem;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.modal-header h3 {
  color: #2c3e50;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #666;
  line-height: 1;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 0.9rem;
  font-family: monospace;
  resize: vertical;
}

.modal-footer {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.btn-primary, .btn-secondary, .btn-info, .btn-danger, .btn-connect, .btn-disconnect {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-secondary {
  background: #f8f9fa;
  color: #333;
  border: 1px solid #ddd;
}

.btn-info {
  background: #3498db;
  color: white;
}

.btn-danger {
  background: #e74c3c;
  color: white;
}

.btn-connect {
  background: #27ae60;
  color: white;
  font-weight: 500;
  padding: 0.75rem 1.5rem;
}

.btn-disconnect {
  background: var(--bg-card);
  color: #e74c3c;
  font-weight: 500;
  padding: 0.75rem 1.5rem;
}

.modal-large {
  max-width: 700px;
}

.modal-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid #eee;
}

.tab-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  background: transparent;
  color: #666;
  font-size: 1rem;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.3s;
}

.tab-btn:hover {
  color: #667eea;
}

.tab-btn.active {
  color: #667eea;
  border-bottom-color: #667eea;
  font-weight: 500;
}

.modal-body {
  max-height: 70vh;
  overflow-y: auto;
}

.form-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #eee;
}

.form-section:last-of-type {
  border-bottom: none;
}

.form-section h4 {
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.input-with-btn {
  display: flex;
  gap: 0.5rem;
}

.input-with-btn input {
  flex: 1;
}

.btn-generate {
  padding: 0.75rem 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.3s;
}

.btn-generate:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}

.btn-generate:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-hint {
  display: block;
  margin-top: 0.5rem;
  color: #666;
  font-size: 0.85rem;
  line-height: 1.4;
}

.form-hint.success {
  color: #27ae60;
}

.public-key-display {
  background: rgba(39, 174, 96, 0.1);
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid rgba(39, 174, 96, 0.3);
}

.public-key-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--bg-card);
  padding: 0.75rem;
  border-radius: 6px;
  border: 1px solid #ddd;
}

.public-key-box code {
  flex: 1;
  font-family: monospace;
  font-size: 0.9rem;
  word-break: break-all;
  color: #2c3e50;
}

.btn-copy {
  padding: 0.5rem 1rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.3s;
}

.btn-copy:hover {
  background: #2980b9;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  font-family: monospace;
}

.form-group textarea {
  resize: vertical;
}
</style>
