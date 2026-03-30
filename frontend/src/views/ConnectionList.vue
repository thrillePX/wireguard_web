<template>
  <div class="connection-list">
    <Loading :show="loading" text="加载中..." />
    
    <div class="header">
      <h2>WireGuard 连接列表</h2>
      <div class="header-actions">
        <button @click="showImportModal = true" class="btn-secondary">
          导入配置
        </button>
        <button @click="showAddModal = true" class="btn-primary">
          添加连接
        </button>
      </div>
    </div>

    <div class="filter-bar">
      <div class="filter-left">
        <label class="filter-toggle">
          <input type="checkbox" v-model="filterOnlyConnected" />
          <span class="toggle-slider"></span>
          <span class="toggle-label">仅显示已连接</span>
        </label>
        <span class="filter-count">
          {{ filteredConnections.length }} / {{ connections.length }}
        </span>
        <label class="batch-toggle" v-if="filteredConnections.length > 0">
          <input type="checkbox" v-model="batchMode" />
          <span class="toggle-slider small"></span>
          <span class="toggle-label">批量选择</span>
        </label>
      </div>
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="搜索名称或服务端..."
          class="search-input"
          ref="searchInput"
        />
        <button v-if="searchQuery" @click="searchQuery = ''" class="search-clear">&times;</button>
      </div>
    </div>

    <div v-if="selectedConnections.length > 0" class="batch-actions">
      <span>已选择 {{ selectedConnections.length }} 个</span>
      <button @click="batchConnect" class="btn-connect">批量连接</button>
      <button @click="batchDisconnect" class="btn-disconnect">批量断开</button>
      <button @click="selectedConnections = []" class="btn-secondary">取消</button>
    </div>

    <div v-else-if="loading" class="loading">
      <div class="spinner"></div>
      加载中...
    </div>
    
    <div v-else-if="filteredConnections.length === 0" class="empty">
      <div class="empty-icon">🔌</div>
      <p v-if="filterOnlyConnected">暂无已连接的 VPN</p>
      <p v-else>暂无连接</p>
      <button v-if="!filterOnlyConnected" @click="showImportModal = true" class="btn-primary">
        导入第一个配置文件
      </button>
      <button v-else @click="filterOnlyConnected = false" class="btn-secondary">
        显示全部
      </button>
    </div>

    <div v-else class="connection-grid" ref="connectionGrid">
      <div 
        v-for="(conn, index) in filteredConnections" 
        :key="conn.name" 
        :class="[
          'connection-card', 
          conn.connected ? 'connected' : 'disconnected',
          { 'selected': selectedConnections.includes(conn.name) },
          { 'focused': focusedIndex === index }
        ]"
        @click="handleCardClick(conn.name, $event)"
      >
        <div class="card-header">
          <div class="connection-name">
            <input 
              v-if="batchMode" 
              type="checkbox" 
              :checked="selectedConnections.includes(conn.name)"
              @click.stop
              @change="toggleSelect(conn.name)"
              class="batch-checkbox"
            />
            <span :class="['status-dot', conn.connected ? 'active' : '']"></span>
            <h3>{{ conn.name }}</h3>
          </div>
          <div class="header-actions">
            <button 
              @click="handleTogglePin(conn.name)" 
              class="pin-btn"
              :title="getConnectionInfo(conn.name).pinned ? '取消固定' : '固定到顶部'"
            >
              {{ getConnectionInfo(conn.name).pinned ? '📌' : '📍' }}
            </button>
            <span :class="['status-badge', conn.connected ? 'connected' : 'disconnected']">
              {{ conn.connected ? '已连接' : '未连接' }}
            </span>
          </div>
        </div>
        
        <div class="card-info">
          <div v-if="conn.interface" class="info-row">
            <span class="label">本地 IP:</span>
            <span class="value">{{ conn.interface.Address }}</span>
            <button @click="copyToClipboard(conn.interface.Address)" class="copy-btn">复制</button>
          </div>
          <div v-if="conn.peer" class="info-row">
            <span class="label">服务端:</span>
            <span class="value endpoint">{{ conn.peer.Endpoint || 'N/A' }}</span>
            <button v-if="conn.peer.Endpoint" @click="copyToClipboard(conn.peer.Endpoint)" class="copy-btn">复制</button>
          </div>
          <div v-if="conn.interface_name" class="info-row">
            <span class="label">接口:</span>
            <span class="value">{{ conn.interface_name }}</span>
          </div>
          <div v-if="conn.connected && conn.uptime" class="info-row uptime">
            <span class="label">运行时长:</span>
            <span class="value">{{ conn.uptime }}</span>
          </div>
        </div>

        <div class="card-actions">
          <button 
            v-if="!conn.connected" 
            @click="handleConnect(conn.name)" 
            class="btn-connect"
          >
            连接
          </button>
          <button 
            v-else 
            @click="handleDisconnect(conn.name)" 
            class="btn-disconnect"
          >
            断开
          </button>
          <button @click="viewDetail(conn.name)" class="btn-info">
            详情
          </button>
          <button @click="handleExport(conn.name)" class="btn-secondary">
            导出
          </button>
          <button @click="confirmDelete(conn.name)" class="btn-danger">
            删除
          </button>
        </div>
      </div>
    </div>

    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>导入 WireGuard 配置</h3>
          <button @click="showImportModal = false" class="close-btn">&times;</button>
        </div>
        
        <div class="modal-body">
          <p>选择 WireGuard 配置文件 (.conf)</p>
          <input 
            type="file" 
            accept=".conf" 
            @change="handleFileSelect" 
            ref="fileInput"
          />
        </div>
        
        <div class="modal-footer">
          <button @click="showImportModal = false" class="btn-secondary">
            取消
          </button>
          <button @click="importFile" class="btn-primary" :disabled="!selectedFile">
            导入
          </button>
        </div>
      </div>
    </div>

    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal modal-large">
        <div class="modal-header">
          <h3>添加新连接</h3>
          <button @click="showAddModal = false" class="close-btn">&times;</button>
        </div>
        
        <div class="modal-tabs">
          <button 
            :class="['tab-btn', { active: addMode === 'form' }]"
            @click="addMode = 'form'"
          >
            📝 表单创建
          </button>
          <button 
            :class="['tab-btn', { active: addMode === 'import' }]"
            @click="addMode = 'import'"
          >
            📄 导入配置
          </button>
        </div>
        
        <div v-if="addMode === 'form'" class="modal-body">
          <form @submit.prevent="addConnection">
            <div class="form-section">
              <h4>基本信息</h4>
              <div class="form-group">
                <label>连接名称</label>
                <input v-model="newConnection.name" required placeholder="例如: my-vpn" />
              </div>
            </div>
            
            <div class="form-section">
              <h4>🔐 本地接口 (Interface)</h4>
              
              <div class="form-group">
                <label>私钥 (PrivateKey)</label>
                <div class="input-with-btn">
                  <input 
                    v-model="newConnection.privateKey" 
                    required 
                    placeholder="点击生成获取私钥"
                    readonly
                  />
                  <button type="button" @click="generateInterfaceKeys" class="btn-generate" :disabled="generatingKeys">
                    {{ generatingKeys ? '生成中...' : '🔑 生成' }}
                  </button>
                </div>
                <small class="form-hint">⚠️ 私钥将保存在配置文件中</small>
              </div>
              
              <div v-if="newConnection.generatedPublicKey" class="form-group public-key-display">
                <label>📤 对应公钥 (分享给对端)</label>
                <div class="public-key-box">
                  <code>{{ newConnection.generatedPublicKey }}</code>
                  <button type="button" @click="copyToClipboard(newConnection.generatedPublicKey)" class="btn-copy">
                    📋 复制
                  </button>
                </div>
                <small class="form-hint success">✅ 将此公钥配置到对端设备的 Peer 中</small>
              </div>
              
              <div class="form-group">
                <label>本地地址 (Address)</label>
                <input 
                  v-model="newConnection.address" 
                  required 
                  placeholder="例如: 10.0.0.2/24"
                />
                <small class="form-hint">WireGuard 隧道内的 IP 地址</small>
              </div>
              
              <div class="form-row">
                <div class="form-group">
                  <label>监听端口 (ListenPort - 可选)</label>
                  <input 
                    v-model="newConnection.listenPort" 
                    placeholder="随机端口"
                    type="number"
                    min="1"
                    max="65535"
                  />
                  <small class="form-hint">本机监听 UDP 端口，默认随机</small>
                </div>
                <div class="form-group">
                  <label>DNS (可选)</label>
                  <input 
                    v-model="newConnection.dns" 
                    placeholder="例如: 223.5.5.5"
                  />
                </div>
              </div>
              
              <div class="form-group">
                <label>MTU (可选)</label>
                <input 
                  v-model="newConnection.mtu" 
                  placeholder="默认: 1360"
                  type="number"
                />
                <small class="form-hint">最大传输单元，通常保持默认即可</small>
              </div>
            </div>
            
            <div class="form-section">
              <h4>🌐 对端节点 (Peer)</h4>
              
              <div class="form-group">
                <label>对端公钥 (PublicKey)</label>
                <input 
                  v-model="newConnection.peerPublicKey" 
                  required 
                  placeholder="服务器提供的公钥"
                />
              </div>
              
              <div class="form-group">
                <label>预共享密钥 (PresharedKey - 可选)</label>
                <div class="input-with-btn">
                  <input 
                    v-model="newConnection.presharedKey" 
                    placeholder="额外的安全密钥 (可选)"
                    readonly
                  />
                  <button type="button" @click="generatePresharedKey" class="btn-generate" :disabled="generatingKeys">
                    {{ generatingKeys ? '生成中...' : '🔑 生成' }}
                  </button>
                </div>
                <small class="form-hint">用于抗量子攻击的可选密钥</small>
              </div>
              
              <div class="form-group">
                <label>服务端地址 (Endpoint)</label>
                <input 
                  v-model="newConnection.endpoint" 
                  required 
                  placeholder="例如: vpn.example.com:51820"
                />
              </div>
              
              <div class="form-group">
                <label>允许的 IP (AllowedIPs)</label>
                <input 
                  v-model="newConnection.allowedIPs" 
                  required 
                  placeholder="例如: 0.0.0.0/0, ::/0"
                />
                <small class="form-hint">
                  0.0.0.0/0 = 全部流量走 VPN<br/>
                  10.0.0.0/24 = 仅特定网段走 VPN
                </small>
              </div>
              
              <div class="form-group">
                <label>保活间隔 (PersistentKeepalive - 可选)</label>
                <input 
                  v-model="newConnection.persistentKeepalive" 
                  placeholder="默认: 25 秒"
                  type="number"
                  min="0"
                  max="65535"
                />
                <small class="form-hint">保持连接活跃的间隔 (秒)，NAT 环境建议 25</small>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" @click="showAddModal = false" class="btn-secondary">
                取消
              </button>
              <button type="submit" class="btn-primary" :disabled="adding || !isFormValid">
                {{ adding ? '添加中...' : '添加连接' }}
              </button>
            </div>
          </form>
        </div>
        
        <div v-else class="modal-body">
          <form @submit.prevent="addConnection">
            <div class="form-group">
              <label>连接名称</label>
              <input v-model="newConnection.name" required placeholder="例如: my-vpn" />
            </div>
            
            <div class="form-group">
              <label>配置文件内容</label>
              <textarea 
                v-model="newConnection.config" 
                required 
                placeholder="粘贴 WireGuard 配置内容..."
                rows="10"
              ></textarea>
            </div>

            <div class="modal-footer">
              <button type="button" @click="showAddModal = false" class="btn-secondary">
                取消
              </button>
              <button type="submit" class="btn-primary" :disabled="adding">
                {{ adding ? '添加中...' : '导入' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useConnectionHistory } from '../composables/useConnectionHistory'
import { useToast } from '../composables/useToast'
import Loading from '../components/Loading.vue'

const router = useRouter()
const connections = ref([])
const loading = ref(true)
const showImportModal = ref(false)
const showAddModal = ref(false)
const adding = ref(false)
const generatingKeys = ref(false)
const addMode = ref('form')
const selectedFile = ref(null)
const fileInput = ref(null)
const filterOnlyConnected = ref(true)
const searchQuery = ref('')
const batchMode = ref(false)
const selectedConnections = ref([])
const focusedIndex = ref(-1)
const searchInput = ref(null)
const connectionGrid = ref(null)
const connectingIds = ref(new Set())
let refreshInterval = null

const { getSortScore, recordUsage, togglePin, getConnectionInfo } = useConnectionHistory()
const toast = useToast()

const filteredConnections = computed(() => {
  let result = connections.value
  
  if (filterOnlyConnected.value) {
    result = result.filter(conn => conn.connected)
  }
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(conn => 
      conn.name.toLowerCase().includes(query) ||
      (conn.peer?.Endpoint || '').toLowerCase().includes(query) ||
      (conn.interface?.Address || '').toLowerCase().includes(query)
    )
  }
  
  return result
})

const newConnection = ref({
  name: '',
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
  persistentKeepalive: '25',
  config: ''
})

const isFormValid = computed(() => {
  return newConnection.value.name && 
         newConnection.value.privateKey &&
         newConnection.value.address &&
         newConnection.value.peerPublicKey &&
         newConnection.value.endpoint &&
         newConnection.value.allowedIPs
})

async function generateInterfaceKeys() {
  try {
    generatingKeys.value = true
    const keys = await api.generateKeys()
    newConnection.value.privateKey = keys.privateKey
    newConnection.value.generatedPublicKey = keys.publicKey
  } catch (error) {
    toast.error('生成密钥失败: ' + error.message)
  } finally {
    generatingKeys.value = false
  }
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    toast.success('已复制到剪贴板')
  }).catch(() => {
    toast.error('复制失败')
  })
}

async function generatePresharedKey() {
  try {
    generatingKeys.value = true
    const result = await api.generatePresharedKey()
    newConnection.value.presharedKey = result.presharedKey
  } catch (error) {
    toast.error('生成预共享密钥失败: ' + error.message)
  } finally {
    generatingKeys.value = false
  }
}

function resetNewConnectionForm() {
  newConnection.value = {
    name: '',
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
    persistentKeepalive: '25',
    config: ''
  }
  addMode.value = 'form'
}

async function loadConnections() {
  try {
    const data = await api.listConnections()
    const connList = Array.isArray(data) ? data : (data.connections || [])
    connections.value = connList.sort((a, b) => {
      const scoreA = getSortScore(a)
      const scoreB = getSortScore(b)
      return scoreB - scoreA
    })
  } catch (error) {
    console.error('加载连接失败:', error)
  } finally {
    loading.value = false
  }
}

function toggleSelect(name) {
  const index = selectedConnections.value.indexOf(name)
  if (index === -1) {
    selectedConnections.value.push(name)
  } else {
    selectedConnections.value.splice(index, 1)
  }
}

function handleCardClick(name, event) {
  if (batchMode.value) {
    toggleSelect(name)
  }
}

async function batchConnect() {
  for (const name of selectedConnections.value) {
    const conn = connections.value.find(c => c.name === name)
    if (conn && !conn.connected) {
      connectingIds.value.add(name)
      try {
        await api.connect(name)
      } catch (e) {
        toast.error(`${name} 连接失败`)
      }
      connectingIds.value.delete(name)
    }
  }
  selectedConnections.value = []
  batchMode.value = false
  loadConnections()
}

async function batchDisconnect() {
  for (const name of selectedConnections.value) {
    const conn = connections.value.find(c => c.name === name)
    if (conn && conn.connected) {
      connectingIds.value.add(name)
      try {
        await api.disconnect(name)
      } catch (e) {
        toast.error(`${name} 断开失败`)
      }
      connectingIds.value.delete(name)
    }
  }
  selectedConnections.value = []
  batchMode.value = false
  loadConnections()
}

function handleKeydown(event) {
  if (event.target.tagName === 'INPUT') return
  
  const list = filteredConnections.value
  if (list.length === 0) return
  
  switch (event.key) {
    case 'j':
    case 'ArrowDown':
      event.preventDefault()
      focusedIndex.value = Math.min(focusedIndex.value + 1, list.length - 1)
      scrollToFocused()
      break
    case 'k':
    case 'ArrowUp':
      event.preventDefault()
      focusedIndex.value = Math.max(focusedIndex.value - 1, 0)
      scrollToFocused()
      break
    case 'Enter':
      if (focusedIndex.value >= 0) {
        event.preventDefault()
        const conn = list[focusedIndex.value]
        if (conn.connected) {
          handleDisconnect(conn.name)
        } else {
          handleConnect(conn.name)
        }
      }
      break
    case '/':
      event.preventDefault()
      searchInput.value?.focus()
      break
    case 'Escape':
      batchMode.value = false
      selectedConnections.value = []
      focusedIndex.value = -1
      break
  }
}

function scrollToFocused() {
  const grid = connectionGrid.value
  if (!grid) return
  const cards = grid.querySelectorAll('.connection-card')
  if (cards[focusedIndex.value]) {
    cards[focusedIndex.value].scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }
}

onMounted(() => {
  loadConnections()
  refreshInterval = setInterval(loadConnections, 30000)
  window.addEventListener('keydown', handleKeydown)
})

async function handleConnect(name) {
  try {
    recordUsage(name)
    const result = await api.connect(name)
    toast.success(result.message || '连接成功')
    loadConnections()
  } catch (error) {
    toast.error('连接失败: ' + error.message)
  }
}

async function handleDisconnect(name) {
  try {
    recordUsage(name)
    const result = await api.disconnect(name)
    toast.success(result.message || '已断开')
    loadConnections()
  } catch (error) {
    toast.error('断开失败: ' + error.message)
  }
}

function viewDetail(name) {
  router.push(`/connection/${name}`)
}

function handleTogglePin(name) {
  togglePin(name)
  loadConnections()
}

async function handleExport(name) {
  try {
    await api.exportConfig(name)
    toast.success('配置文件已导出')
  } catch (error) {
    toast.error('导出失败: ' + error.message)
  }
}

async function confirmDelete(name) {
  if (confirm(`确定要删除连接 "${name}" 吗？`)) {
    try {
      await api.deleteConnection(name)
      toast.success('连接已删除')
      loadConnections()
    } catch (error) {
      toast.error('删除失败: ' + error.message)
    }
  }
}

function handleFileSelect(event) {
  selectedFile.value = event.target.files[0]
}

async function importFile() {
  if (!selectedFile.value) return
  
  try {
    const result = await api.importConfig(selectedFile.value)
    toast.success(result.message || '导入成功')
    showImportModal.value = false
    selectedFile.value = null
    if (fileInput.value) {
      fileInput.value.value = ''
    }
    loadConnections()
  } catch (error) {
    toast.error('导入失败: ' + error.message)
  }
}

async function addConnection() {
  adding.value = true
  try {
    let config
    
    if (addMode.value === 'form') {
      config = generateConfigFromForm()
    } else {
      config = newConnection.value.config
    }
    
    await api.addConnection(newConnection.value.name, config)
    toast.success('连接已添加')
    showAddModal.value = false
    resetNewConnectionForm()
    loadConnections()
  } catch (error) {
    toast.error('添加失败: ' + error.message)
  } finally {
    adding.value = false
  }
}

function generateConfigFromForm() {
  const form = newConnection.value
  
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

onMounted(() => {
  loadConnections()
  refreshInterval = setInterval(loadConnections, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.header h2 {
  font-size: 1.8rem;
  color: #2c3e50;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.loading, .empty {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
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

.connection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 1.5rem;
}

.connection-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px var(--shadow);
  border: 1px solid var(--border-color);
  transition: all 0.3s;
}

.connection-card.connected {
  border-left-color: #27ae60;
}

.connection-card.disconnected {
  border-left-color: #95a5a6;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.connection-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.pin-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.3s;
}

.pin-btn:hover {
  background: rgba(102, 126, 234, 0.1);
  transform: scale(1.2);
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #e0e0e0;
}

.status-dot.active {
  background: #27ae60;
  box-shadow: 0 0 8px rgba(39, 174, 96, 0.5);
}

.card-header h3 {
  color: #2c3e50;
  font-size: 1.2rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
}

.status-badge.connected {
  background: #d4edda;
  color: #155724;
}

.status-badge.disconnected {
  background: #f8f9fa;
  color: #6c757d;
}

.card-info {
  margin: 1rem 0;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-row:last-child {
  border-bottom: none;
}

.info-row.uptime {
  background: linear-gradient(135deg, rgba(39, 174, 96, 0.1) 0%, rgba(102, 126, 234, 0.1) 100%);
  padding: 0.5rem 0.75rem;
  margin: 0.5rem -0.75rem;
  border-radius: 6px;
  border-bottom: none;
}

.info-row.uptime .label {
  color: #27ae60;
  font-weight: 500;
}

.info-row.uptime .value {
  color: #2c3e50;
  font-weight: 600;
  font-family: 'SF Mono', 'Monaco', monospace;
}

.label {
  color: #666;
  font-size: 0.9rem;
}

.value {
  color: #333;
  font-weight: 500;
  font-family: monospace;
  font-size: 0.9rem;
}

.value.endpoint {
  font-size: 0.85rem;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
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
  max-width: 500px;
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

.modal-body {
  margin-bottom: 1.5rem;
}

.modal-body p {
  color: #666;
  margin-bottom: 1rem;
}

.modal-body input[type="file"] {
  width: 100%;
  padding: 0.75rem;
  border: 2px dashed #ddd;
  border-radius: 8px;
}

.modal-footer {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
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

.btn-primary, .btn-secondary, .btn-success, .btn-warning, .btn-danger, .btn-info, .btn-connect, .btn-disconnect {
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

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-secondary {
  background: #f8f9fa;
  color: #333;
  border: 1px solid #ddd;
}

.btn-success {
  background: #27ae60;
  color: white;
}

.btn-warning {
  background: #f39c12;
  color: white;
}

.btn-danger {
  background: #e74c3c;
  color: white;
}

.btn-info {
  background: #3498db;
  color: white;
}

.btn-connect {
  background: #27ae60;
  color: white;
  font-weight: 500;
}

.btn-disconnect {
  background: #e74c3c;
  color: white;
  font-weight: 500;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1.5rem;
  background: var(--bg-card);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 1.5rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.filter-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.filter-toggle {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
}

.filter-toggle input[type="checkbox"] {
  display: none;
}

.toggle-slider {
  position: relative;
  width: 48px;
  height: 26px;
  background: #ddd;
  border-radius: 13px;
  transition: all 0.3s;
}

.toggle-slider::before {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  background: var(--bg-card);
  border-radius: 50%;
  transition: all 0.3s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.filter-toggle input:checked + .toggle-slider {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.filter-toggle input:checked + .toggle-slider::before {
  transform: translateX(22px);
}

.toggle-label {
  font-size: 0.95rem;
  color: #2c3e50;
  font-weight: 500;
}

.filter-count {
  font-size: 0.9rem;
  color: #666;
  font-weight: 500;
}

.search-box {
  display: flex;
  align-items: center;
  background: #f8f9fa;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  gap: 0.5rem;
}

.search-icon {
  font-size: 1rem;
  opacity: 0.5;
}

.search-input {
  border: none;
  background: transparent;
  outline: none;
  font-size: 0.9rem;
  width: 200px;
  color: var(--text-primary);
}

.search-input::placeholder {
  color: var(--text-secondary);
}

.search-clear {
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #999;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.search-clear:hover {
  color: #666;
}

.dark-mode .search-box {
  background: #1e293b;
  border-color: #334155;
}

.dark-mode .search-input {
  color: #f1f5f9;
}

.info-row {
  position: relative;
}

.batch-toggle {
  margin-left: 1rem;
  display: flex;
  align-items: center;
}

.batch-toggle input[type="checkbox"] {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.batch-toggle .toggle-slider {
  position: relative;
  display: inline-block;
  width: 36px;
  height: 18px;
  background: var(--border-color);
  border-radius: 18px;
  cursor: pointer;
  transition: background 0.3s;
  margin-right: 0.5rem;
}

.batch-toggle input:checked + .toggle-slider {
  background: var(--accent-color);
}

.batch-toggle .toggle-slider::before {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
  background: white;
  border-radius: 50%;
  transition: transform 0.3s;
}

.batch-toggle input:checked + .toggle-slider::before {
  transform: translateX(18px);
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--accent-color);
  color: white;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.batch-actions span {
  flex: 1;
  font-weight: 500;
}

.connection-card.selected {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 2px var(--accent-color);
}

.connection-card.focused {
  box-shadow: 0 0 0 2px var(--accent-color);
  transform: translateY(-2px);
}

.batch-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--accent-color);
}

.toggle-slider.small {
  width: 36px;
  height: 18px;
}

.toggle-slider.small::before {
  width: 14px;
  height: 14px;
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }
  
  .filter-bar {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .filter-left {
    flex-wrap: wrap;
  }
  
  .search-box {
    width: 100%;
  }
  
  .search-input {
    width: 100%;
  }
  
  .connection-grid {
    grid-template-columns: 1fr;
  }
  
  .batch-actions {
    flex-wrap: wrap;
  }
  
  .nav-links {
    gap: 1rem;
    font-size: 0.9rem;
  }
}
</style>
