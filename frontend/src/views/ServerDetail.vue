<template>
  <div class="server-detail">
    <div class="header">
      <button @click="goBack" class="btn-secondary">返回列表</button>
      <h2>{{ serverName }} - 服务详情</h2>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <div v-else class="detail-content">
      <div class="section">
        <h3>服务信息</h3>
        <div class="info-grid">
          <div class="info-item">
            <label>名称</label>
            <span>{{ serverName }}</span>
          </div>
          <div class="info-item">
            <label>状态</label>
            <span :class="['status', serverInfo.active ? 'active' : 'inactive']">
              {{ serverInfo.active ? '运行中' : '已停止' }}
            </span>
          </div>
          <div class="info-item">
            <label>配置文件</label>
            <span>{{ serverInfo.path }}</span>
          </div>
          <div class="info-item">
            <label>监听端口</label>
            <span>{{ serverInfo.config?.Interface?.ListenPort || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <label>服务端地址</label>
            <span>{{ serverInfo.config?.Interface?.Address || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <label>DNS</label>
            <span>{{ serverInfo.config?.Interface?.DNS || 'N/A' }}</span>
          </div>
          <div class="info-item full-width">
            <label>服务端公钥</label>
            <code>{{ serverInfo.config?.Interface?.PublicKey || 'N/A' }}</code>
          </div>
        </div>
        
        <div class="actions">
          <button v-if="!serverInfo.active" @click="startServer" class="btn-success">启动服务</button>
          <button v-else @click="stopServer" class="btn-warning">停止服务</button>
          <button @click="restartServer" class="btn-info">重启服务</button>
        </div>
      </div>

      <div class="section">
        <div class="section-header">
          <h3>客户端列表</h3>
          <button @click="showAddClientModal = true" class="btn-primary">
            添加客户端
          </button>
        </div>

        <div v-if="clients.length === 0" class="empty">
          暂无客户端
        </div>

        <table v-else class="clients-table">
          <thead>
            <tr>
              <th>公钥</th>
              <th>允许的IP</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(client, index) in clients" :key="index">
              <td class="key-cell">{{ client.PublicKey }}</td>
              <td>{{ client.AllowedIPs }}</td>
              <td>
                <button @click="exportConfig(client)" class="btn-info">导出配置</button>
                <button @click="removeClient(client)" class="btn-danger">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="showAddClientModal" class="modal-overlay" @click.self="showAddClientModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>添加新客户端</h3>
          <button @click="showAddClientModal = false" class="close-btn">&times;</button>
        </div>
        
        <form @submit.prevent="addClient">
          <div class="form-group">
            <label>客户端名称</label>
            <input v-model="newClient.client_name" required placeholder="例如: client1" />
          </div>
          
          <div class="form-group">
            <label>客户端地址 (CIDR)</label>
            <input v-model="newClient.client_address" required placeholder="例如: 10.0.0.2/32" />
          </div>
          
          <div class="form-group">
            <label>允许的IP段</label>
            <input v-model="newClient.allowed_ips" placeholder="例如: 0.0.0.0/0, ::/0" />
          </div>

          <div class="form-actions">
            <button type="button" @click="showAddClientModal = false" class="btn-secondary">
              取消
            </button>
            <button type="submit" class="btn-primary" :disabled="adding">
              {{ adding ? '添加中...' : '添加' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showClientConfigModal" class="modal-overlay" @click.self="closeConfigModal">
      <div class="modal">
        <div class="modal-header">
          <h3>客户端配置</h3>
          <button @click="closeConfigModal" class="close-btn">&times;</button>
        </div>
        
        <div class="config-content">
          <p><strong>客户端私钥:</strong></p>
          <code class="config-key">{{ clientConfig.private_key }}</code>
          
          <p><strong>客户端公钥:</strong></p>
          <code class="config-key">{{ clientConfig.public_key }}</code>
          
          <p v-if="clientConfig.preshared_key"><strong>预共享密钥:</strong></p>
          <code v-if="clientConfig.preshared_key" class="config-key">{{ clientConfig.preshared_key }}</code>
          
          <p><strong>配置文件内容:</strong></p>
          <pre class="config-pre">{{ clientConfig.client_config }}</pre>
          
          <p class="warning">⚠️ 请妥善保管密钥，特别是私钥！</p>
          
          <div class="form-actions">
            <button @click="copyConfig" class="btn-primary">复制配置</button>
            <button @click="downloadConfig" class="btn-success">下载配置文件</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const route = useRoute()

const serverName = route.params.name
const serverInfo = ref({})
const clients = ref([])
const loading = ref(true)
const error = ref('')
const showAddClientModal = ref(false)
const showClientConfigModal = ref(false)
const adding = ref(false)

const newClient = ref({
  client_name: '',
  client_address: '',
  allowed_ips: ''
})

const clientConfig = ref({
  private_key: '',
  public_key: '',
  preshared_key: '',
  client_config: ''
})

async function loadServerInfo() {
  try {
    serverInfo.value = await api.getServer(serverName)
    clients.value = await api.listClients(serverName)
  } catch (err) {
    error.value = '加载失败: ' + err.message
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/')
}

async function startServer() {
  try {
    await api.startServer(serverName)
    alert('服务已启动')
    loadServerInfo()
  } catch (err) {
    alert('启动失败: ' + err.message)
  }
}

async function stopServer() {
  try {
    await api.stopServer(serverName)
    alert('服务已停止')
    loadServerInfo()
  } catch (err) {
    alert('停止失败: ' + err.message)
  }
}

async function restartServer() {
  try {
    await api.restartServer(serverName)
    alert('服务已重启')
    loadServerInfo()
  } catch (err) {
    alert('重启失败: ' + err.message)
  }
}

async function addClient() {
  adding.value = true
  try {
    const result = await api.addClient(serverName, newClient.value)
    clientConfig.value = result
    showAddClientModal.value = false
    showClientConfigModal.value = true
    clients.value.push({
      PublicKey: result.public_key,
      AllowedIPs: newClient.value.client_address
    })
    newClient.value = { client_name: '', client_address: '', allowed_ips: '' }
  } catch (err) {
    alert('添加失败: ' + err.message)
  } finally {
    adding.value = false
  }
}

async function exportConfig(client) {
  const address = client.AllowedIPs || ''
  const firstClient = clients.value[0]
  if (firstClient) {
    try {
      const result = await api.getClientConfig(serverName, client.PublicKey, '', address)
      clientConfig.value = {
        ...result,
        private_key: '',
        public_key: client.PublicKey
      }
      showClientConfigModal.value = true
    } catch (err) {
      alert('导出失败: ' + err.message)
    }
  }
}

async function removeClient(client) {
  if (confirm('确定要删除此客户端吗？')) {
    try {
      await api.removeClient(serverName, client.PublicKey)
      clients.value = clients.value.filter(c => c.PublicKey !== client.PublicKey)
      alert('客户端已删除')
    } catch (err) {
      alert('删除失败: ' + err.message)
    }
  }
}

function closeConfigModal() {
  showClientConfigModal.value = false
  clientConfig.value = {
    private_key: '',
    public_key: '',
    preshared_key: '',
    client_config: ''
  }
}

function copyConfig() {
  navigator.clipboard.writeText(clientConfig.value.client_config)
    .then(() => alert('配置已复制到剪贴板'))
    .catch(() => alert('复制失败'))
}

async function downloadConfig() {
  try {
    await api.downloadConfig(
      serverName,
      clientConfig.value.public_key,
      clientConfig.value.private_key,
      clients.value.find(c => c.PublicKey === clientConfig.value.public_key)?.AllowedIPs || ''
    )
  } catch (err) {
    alert('下载失败: ' + err.message)
  }
}

onMounted(loadServerInfo)
</script>

<style scoped>
.header {
  margin-bottom: 2rem;
}

.header h2 {
  margin-top: 1rem;
  color: #2c3e50;
}

.loading, .error, .empty {
  text-align: center;
  padding: 3rem;
}

.error {
  color: #e74c3c;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.section h3 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-item label {
  font-weight: 500;
  color: #666;
  font-size: 0.9rem;
}

.info-item span {
  color: #333;
}

.status {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
  width: fit-content;
}

.status.active {
  background: #d4edda;
  color: #155724;
}

.status.inactive {
  background: #f8d7da;
  color: #721c24;
}

code {
  background: #f8f9fa;
  padding: 0.5rem;
  border-radius: 4px;
  font-family: monospace;
  word-break: break-all;
  font-size: 0.85rem;
}

.actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.clients-table {
  width: 100%;
  border-collapse: collapse;
}

.clients-table th,
.clients-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.clients-table th {
  background: #f8f9fa;
  font-weight: 600;
}

.key-cell {
  font-family: monospace;
  font-size: 0.85rem;
  word-break: break-all;
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
  border-radius: 8px;
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

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #666;
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
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.config-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.config-content p {
  margin: 0;
  font-weight: 500;
}

.config-key {
  background: #f8f9fa;
  padding: 0.75rem;
  border-radius: 4px;
  font-family: monospace;
  word-break: break-all;
  font-size: 0.85rem;
}

.config-pre {
  background: #2c3e50;
  color: #ecf0f1;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
  font-family: monospace;
  font-size: 0.85rem;
  white-space: pre-wrap;
  word-break: break-all;
}

.warning {
  color: #e74c3c;
  font-weight: 500;
}

.btn-primary, .btn-secondary, .btn-success, .btn-warning, .btn-danger, .btn-info {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
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
</style>
