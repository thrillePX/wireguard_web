<template>
  <div class="topology-view">
    <div class="header">
      <h2>📊 WireGuard 网络拓扑图</h2>
      <button @click="refreshTopology" class="btn-refresh">
        🔄 刷新
      </button>
    </div>

    <div class="filter-bar">
      <label class="filter-toggle">
        <input type="checkbox" v-model="filterOnlyConnected" />
        <span class="toggle-slider"></span>
        <span class="toggle-label">仅显示已连接</span>
      </label>
      
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input 
          v-model="searchQuery" 
          placeholder="搜索网段..."
          class="search-input"
        />
        <button v-if="searchQuery" @click="searchQuery = ''" class="clear-btn">✕</button>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      加载中...
    </div>

    <div v-else class="topology-content">
      <div class="local-node">
        <div class="node-icon">💻</div>
        <div class="node-info">
          <h3>本机</h3>
          <p class="node-detail">网络入口</p>
        </div>
        <div class="connection-count">
          <span class="count-badge connected">{{ connectedCount }} 个活跃连接</span>
        </div>
      </div>

      <div v-for="(conn, index) in filteredConnections" :key="index" class="vpn-branch">
        <div class="branch-connector">
          <div class="connector-line"></div>
          <div class="connector-dot"></div>
        </div>

        <div :class="['vpn-node', conn.connected ? 'connected' : 'disconnected']">
          <div class="vpn-icon">{{ conn.connected ? '🌐' : '⚪' }}</div>
          <div class="vpn-info">
            <h4>{{ conn.name }}</h4>
            <p class="vpn-detail">
              <span class="endpoint">{{ conn.peer?.Endpoint || 'N/A' }}</span>
              <span class="status-badge" :class="conn.connected ? 'connected' : ''">
                {{ conn.connected ? '已连接' : '未连接' }}
              </span>
            </p>
          </div>
          <div v-if="conn.connected && conn.status" class="vpn-traffic">
            <span class="traffic rx">↓ {{ formatBytes(conn.status.peers?.[0]?.transfer?.rx || 0) }}</span>
            <span class="traffic tx">↑ {{ formatBytes(conn.status.peers?.[0]?.transfer?.tx || 0) }}</span>
          </div>
        </div>

        <div v-if="conn.peer?.AllowedIPs && filteredAllowedIPs(conn).length > 0" class="routes-branch">
          <div class="routes-connector">
            <div class="connector-line horizontal"></div>
          </div>
          
          <div class="routes-container">
            <div class="route-node" v-for="(ip, ipIndex) in filteredAllowedIPs(conn).slice(0, maxRoutesPerConn)" :key="ipIndex">
              <div class="route-icon">📍</div>
              <div class="route-info">
                <span class="route-ip">{{ ip }}</span>
                <span class="route-label">可通过 {{ conn.name }} 访问</span>
              </div>
            </div>
            
            <div v-if="filteredAllowedIPs(conn).length > maxRoutesPerConn" class="more-routes">
              <button @click="showAllRoutes(conn, filteredAllowedIPs(conn))" class="show-more-btn">
                📋 查看全部 {{ filteredAllowedIPs(conn).length }} 个匹配网段
              </button>
            </div>
            
            <div v-if="searchQuery && filteredAllowedIPs(conn).length === 0" class="no-matches">
              <span>无匹配网段</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="filteredConnections.length === 0" class="empty-state">
        <div class="empty-icon">🔌</div>
        <p v-if="filterOnlyConnected">暂无已连接的 VPN</p>
        <p v-else>暂无 WireGuard 连接</p>
        <p class="empty-hint">导入配置文件开始管理你的 VPN 连接</p>
      </div>
    </div>

    <div v-if="showAllRoutesModal" class="modal-overlay" @click.self="showAllRoutesModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ selectedConn?.name }} - {{ searchQuery ? '匹配' : '' }}路由网段</h3>
          <button @click="showAllRoutesModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="search-box in-modal">
            <span class="search-icon">🔍</span>
            <input 
              v-model="modalSearchQuery" 
              placeholder="搜索网段..."
              class="search-input"
            />
          </div>
          <div class="all-routes-list">
            <div v-for="(ip, ipIndex) in filteredModalIPs" :key="ipIndex" class="route-item-full">
              <span class="route-icon">📍</span>
              <span class="route-ip-full">{{ ip }}</span>
            </div>
            <div v-if="filteredModalIPs.length === 0" class="no-matches">
              <span>无匹配网段</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { api } from '../api'

const connections = ref([])
const loading = ref(true)
const showAllRoutesModal = ref(false)
const selectedConn = ref(null)
const filterOnlyConnected = ref(true)
const searchQuery = ref('')
const modalSearchQuery = ref('')
const maxRoutesPerConn = ref(8)
let refreshInterval = null

const connectedCount = computed(() => {
  return connections.value.filter(c => c.connected).length
})

const filteredConnections = computed(() => {
  let result = connections.value
  if (filterOnlyConnected.value) {
    result = result.filter(c => c.connected)
  }
  return result
})

const filteredModalIPs = computed(() => {
  if (!selectedConn.value?.allIPs) return []
  if (!modalSearchQuery.value) return selectedConn.value.allIPs
  const query = modalSearchQuery.value.toLowerCase()
  return selectedConn.value.allIPs.filter(ip => 
    ip.toLowerCase().includes(query)
  )
})

function filteredAllowedIPs(conn) {
  const allIPs = parseAllowedIPs(conn.peer?.AllowedIPs || '')
  if (!searchQuery.value) return allIPs
  const query = searchQuery.value.toLowerCase()
  return allIPs.filter(ip => ip.toLowerCase().includes(query))
}

function parseAllowedIPs(allowedIPs) {
  if (!allowedIPs) return []
  return allowedIPs.split(',').map(ip => ip.trim()).filter(ip => ip)
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

async function loadConnections() {
  try {
    const data = await api.listConnections()
    const connList = Array.isArray(data) ? data : (data.connections || [])
    connections.value = connList.sort((a, b) => {
      if (a.connected && !b.connected) return -1
      if (!a.connected && b.connected) return 1
      return 0
    })
  } catch (error) {
    console.error('加载连接失败:', error)
  } finally {
    loading.value = false
  }
}

function showAllRoutes(conn, filteredIPs = null) {
  const allIPs = filteredIPs || parseAllowedIPs(conn.peer?.AllowedIPs || '')
  selectedConn.value = {
    ...conn,
    allIPs: allIPs
  }
  modalSearchQuery.value = ''
  showAllRoutesModal.value = true
}

function refreshTopology() {
  loading.value = true
  loadConnections()
}

onMounted(() => {
  loadConnections()
  refreshInterval = setInterval(loadConnections, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.topology-view {
  padding: 0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 1.5rem;
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
  background: white;
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

.search-box {
  display: flex;
  align-items: center;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  gap: 0.5rem;
  min-width: 200px;
}

.search-box.in-modal {
  margin-bottom: 1rem;
  min-width: auto;
}

.search-icon {
  font-size: 1rem;
  opacity: 0.6;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 0.95rem;
  outline: none;
}

.clear-btn {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  padding: 0;
  font-size: 0.9rem;
}

.clear-btn:hover {
  color: #666;
}

.no-matches {
  padding: 0.75rem;
  text-align: center;
  color: #999;
  font-size: 0.9rem;
}

.header h2 {
  color: #2c3e50;
}

.btn-refresh {
  padding: 0.5rem 1rem;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s;
}

.btn-refresh:hover {
  background: #e9ecef;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #666;
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

.topology-content {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.local-node {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  padding: 1.5rem 2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.local-node .node-icon {
  font-size: 3rem;
}

.local-node .node-info h3 {
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.local-node .node-detail {
  font-size: 0.9rem;
  opacity: 0.9;
}

.connection-count {
  margin-left: auto;
}

.count-badge {
  background: rgba(255,255,255,0.2);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
}

.vpn-branch {
  padding-left: 2rem;
  position: relative;
}

.branch-connector {
  position: absolute;
  left: 1rem;
  top: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.connector-line {
  width: 2px;
  height: 30px;
  background: #667eea;
}

.connector-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #667eea;
  border: 3px solid white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.vpn-node {
  background: white;
  border-radius: 12px;
  padding: 1rem 1.5rem;
  margin: 1rem 0;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  border-left: 4px solid #e0e0e0;
  transition: all 0.3s;
}

.vpn-node.connected {
  border-left-color: #27ae60;
}

.vpn-node.disconnected {
  border-left-color: #e0e0e0;
  opacity: 0.7;
}

.vpn-icon {
  font-size: 2.5rem;
}

.vpn-info {
  flex: 1;
}

.vpn-info h4 {
  font-size: 1.2rem;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.vpn-detail {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
}

.endpoint {
  color: #666;
  font-family: monospace;
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  background: #e0e0e0;
  color: #666;
}

.status-badge.connected {
  background: #d4edda;
  color: #155724;
}

.vpn-traffic {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.85rem;
  font-family: monospace;
}

.traffic.rx {
  color: #27ae60;
}

.traffic.tx {
  color: #3498db;
}

.routes-branch {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.routes-connector {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
}

.connector-line.horizontal {
  width: 30px;
  height: 2px;
  background: #e0e0e0;
}

.routes-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 0.75rem;
}

.route-node {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border-left: 3px solid #667eea;
  transition: all 0.3s;
}

.route-node:hover {
  background: #e9ecef;
  transform: translateX(4px);
}

.route-icon {
  font-size: 1.5rem;
}

.route-info {
  flex: 1;
}

.route-ip {
  font-family: monospace;
  font-weight: 600;
  color: #2c3e50;
  display: block;
  margin-bottom: 0.25rem;
}

.route-label {
  font-size: 0.8rem;
  color: #666;
}

.more-routes {
  grid-column: 1 / -1;
  display: flex;
  justify-content: center;
}

.show-more-btn {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.show-more-btn:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.empty-state {
  text-align: center;
  padding: 3rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-hint {
  color: #666;
  font-size: 0.9rem;
  margin-top: 0.5rem;
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
  background: white;
  border-radius: 12px;
  padding: 2rem;
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
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
  margin-bottom: 1rem;
}

.all-routes-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.route-item-full {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 3px solid #667eea;
}

.route-icon {
  font-size: 1.5rem;
}

.route-ip-full {
  font-family: monospace;
  font-weight: 600;
  color: #2c3e50;
  font-size: 1.1rem;
}
</style>
