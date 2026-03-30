<template>
  <div class="settings">
    <h2>系统设置</h2>

    <div class="section">
      <h3>配置文件路径</h3>
      <p class="description">
        WireGuard 配置文件的存放目录。默认路径为 <code>/etc/wireguard/</code>
      </p>
      
      <div class="form-group">
        <label>配置路径</label>
        <input v-model="configPath" placeholder="/etc/wireguard/" />
      </div>

      <button @click="saveConfigPath" class="btn-primary" :disabled="saving">
        {{ saving ? '保存中...' : '保存设置' }}
      </button>

      <p v-if="message" :class="['message', messageType]">{{ message }}</p>
    </div>

    <div class="section">
      <h3>连接统计</h3>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">📋</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total || 0 }}</div>
            <div class="stat-label">总连接数</div>
          </div>
        </div>
        <div class="stat-card connected">
          <div class="stat-icon">✅</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.connected || 0 }}</div>
            <div class="stat-label">已连接</div>
          </div>
        </div>
        <div class="stat-card disconnected">
          <div class="stat-icon">⚪</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.disconnected || 0 }}</div>
            <div class="stat-label">未连接</div>
          </div>
        </div>
      </div>
      <button @click="refreshStats" class="btn-secondary">
        刷新统计
      </button>
    </div>

    <div class="section" v-if="historyStats.length > 0">
      <h3>历史记录统计</h3>
      <div class="history-stats">
        <div v-for="item in historyStats" :key="item.connection" class="history-item">
          <div class="history-name">{{ item.connection }}</div>
          <div class="history-details">
            <span>连接 {{ item.total_connects }} 次</span>
            <span>累计 {{ item.total_duration_formatted }}</span>
            <span>平均 {{ item.avg_duration_formatted }}/次</span>
          </div>
        </div>
      </div>
      <button @click="loadHistoryStats" class="btn-secondary" :disabled="loadingHistory">
        {{ loadingHistory ? '加载中...' : '刷新历史' }}
      </button>
    </div>

    <div class="section">
      <h3>快捷键</h3>
      <div class="shortcuts-grid">
        <div class="shortcut-item">
          <kbd>J</kbd> / <kbd>↓</kbd>
          <span>下一个连接</span>
        </div>
        <div class="shortcut-item">
          <kbd>K</kbd> / <kbd>↑</kbd>
          <span>上一个连接</span>
        </div>
        <div class="shortcut-item">
          <kbd>Enter</kbd>
          <span>连接/断开选中项</span>
        </div>
        <div class="shortcut-item">
          <kbd>/</kbd>
          <span>聚焦搜索框</span>
        </div>
        <div class="shortcut-item">
          <kbd>Esc</kbd>
          <span>取消批量选择</span>
        </div>
      </div>
    </div>

    <div class="section">
      <h3>使用说明</h3>
      <div class="instructions">
        <h4>1. 导入配置</h4>
        <p>点击"导入配置"按钮，选择 WireGuard 配置文件（.conf 文件）来添加新连接。</p>
        
        <h4>2. 连接 VPN</h4>
        <p>在连接列表中，点击"连接"按钮来启动 WireGuard 连接。需要系统授权。</p>
        
        <h4>3. 断开连接</h4>
        <p>点击"断开"按钮来关闭当前连接。</p>
        
        <h4>4. 查看详情</h4>
        <p>点击"详情"按钮可以查看连接的详细信息，包括流量统计和配置内容。</p>
        
        <h4>5. 导出配置</h4>
        <p>可以将配置导出为 .conf 文件，用于备份或在其他设备上使用。</p>
        
        <h4>注意事项</h4>
        <ul>
          <li>连接和断开操作可能需要管理员权限</li>
          <li>在 macOS 上，WireGuard 会创建 utun 接口</li>
          <li>多个连接不能同时使用相同的本地 IP 地址</li>
          <li>配置文件路径需要有读取权限</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const configPath = ref('')
const saving = ref(false)
const message = ref('')
const messageType = ref('success')
const stats = ref({})
const historyStats = ref([])
const loadingHistory = ref(false)

async function loadConfigPath() {
  try {
    const result = await api.getConfigPath()
    configPath.value = result.path
  } catch (error) {
    message.value = '加载配置路径失败: ' + error.message
    messageType.value = 'error'
  }
}

async function loadStats() {
  try {
    stats.value = await api.getAllStatus()
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

async function saveConfigPath() {
  saving.value = true
  message.value = ''
  try {
    await api.setConfigPath(configPath.value)
    message.value = '配置路径已保存'
    messageType.value = 'success'
    loadStats()
  } catch (error) {
    message.value = '保存失败: ' + error.message
    messageType.value = 'error'
  } finally {
    saving.value = false
  }
}

function refreshStats() {
  loadStats()
}

async function loadHistoryStats() {
  loadingHistory.value = true
  try {
    const result = await api.getAllStats()
    historyStats.value = result.stats || []
  } catch (error) {
    console.error('加载历史统计失败:', error)
  } finally {
    loadingHistory.value = false
  }
}

onMounted(() => {
  loadConfigPath()
  loadStats()
  loadHistoryStats()
})
</script>

<style scoped>
h2 {
  color: #2c3e50;
  margin-bottom: 2rem;
}

.section {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 1.5rem;
}

.section h3 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.description {
  color: #666;
  margin-bottom: 1.5rem;
}

.description code {
  background: #f8f9fa;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #ddd;
}

.stat-card.connected {
  border-left-color: #27ae60;
}

.stat-card.disconnected {
  border-left-color: #95a5a6;
}

.stat-icon {
  font-size: 2rem;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 1.8rem;
  font-weight: bold;
  color: #2c3e50;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  max-width: 400px;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
}

.message {
  margin-top: 1rem;
  padding: 0.75rem;
  border-radius: 8px;
  font-weight: 500;
}

.message.success {
  background: #d4edda;
  color: #155724;
}

.message.error {
  background: #f8d7da;
  color: #721c24;
}

.instructions {
  color: #666;
  line-height: 1.6;
}

.instructions h4 {
  color: #2c3e50;
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
}

.instructions h4:first-child {
  margin-top: 0;
}

.instructions ul {
  margin-left: 1.5rem;
  margin-top: 0.5rem;
}

.instructions li {
  margin: 0.5rem 0;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s;
}

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: #f8f9fa;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s;
}

.btn-secondary:hover {
  background: #e9ecef;
}

.history-stats {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.history-item {
  padding: 0.75rem 1rem;
  background: var(--bg-input);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.history-name {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.history-details {
  display: flex;
  gap: 1.5rem;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.shortcuts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.shortcut-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--bg-input);
  border-radius: 8px;
}

.shortcut-item kbd {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  font-family: monospace;
  font-size: 0.85rem;
  color: var(--accent-color);
}

.shortcut-item span {
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .history-details {
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .shortcuts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
