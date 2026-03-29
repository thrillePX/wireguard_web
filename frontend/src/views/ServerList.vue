<template>
  <div class="server-list">
    <div class="header">
      <h2>WireGuard 服务列表</h2>
      <button @click="showCreateModal = true" class="btn-primary">
        新建服务
      </button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    
    <div v-else-if="servers.length === 0" class="empty">
      <p>暂无服务</p>
      <button @click="showCreateModal = true" class="btn-secondary">
        创建第一个服务
      </button>
    </div>

    <div v-else class="server-grid">
      <div v-for="server in servers" :key="server.name" class="server-card">
        <div class="server-header">
          <h3>{{ server.name }}</h3>
          <span :class="['status', server.active ? 'active' : 'inactive']">
            {{ server.active ? '运行中' : '已停止' }}
          </span>
        </div>
        
        <div class="server-info">
          <p><strong>配置文件:</strong> {{ server.path }}</p>
          <p v-if="server.config.Interface">
            <strong>地址:</strong> {{ server.config.Interface.Address }}
          </p>
          <p v-if="server.config.Interface">
            <strong>端口:</strong> {{ server.config.Interface.ListenPort }}
          </p>
        </div>

        <div class="server-actions">
          <button @click="viewServer(server.name)" class="btn-info">
            查看详情
          </button>
          <button 
            v-if="!server.active" 
            @click="startServer(server.name)" 
            class="btn-success"
          >
            启动
          </button>
          <button 
            v-else 
            @click="stopServer(server.name)" 
            class="btn-warning"
          >
            停止
          </button>
          <button @click="confirmDelete(server.name)" class="btn-danger">
            删除
          </button>
        </div>
      </div>
    </div>

    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>创建新服务</h3>
          <button @click="showCreateModal = false" class="close-btn">&times;</button>
        </div>
        
        <form @submit.prevent="createServer">
          <div class="form-group">
            <label>服务名称</label>
            <input v-model="newServer.name" required placeholder="例如: wg0" />
          </div>
          
          <div class="form-group">
            <label>服务端地址 (CIDR)</label>
            <input v-model="newServer.address" required placeholder="例如: 10.0.0.1/24" />
          </div>
          
          <div class="form-group">
            <label>监听端口</label>
            <input v-model.number="newServer.listen_port" type="number" required placeholder="默认: 51820" />
          </div>
          
          <div class="form-group">
            <label>DNS服务器</label>
            <input v-model="newServer.dns" placeholder="例如: 8.8.8.8" />
          </div>
          
          <div class="form-group">
            <label>MTU</label>
            <input v-model.number="newServer.mtu" type="number" placeholder="默认: 1420" />
          </div>

          <div class="form-actions">
            <button type="button" @click="showCreateModal = false" class="btn-secondary">
              取消
            </button>
            <button type="submit" class="btn-primary" :disabled="creating">
              {{ creating ? '创建中...' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const servers = ref([])
const loading = ref(true)
const showCreateModal = ref(false)
const creating = ref(false)

const newServer = ref({
  name: '',
  address: '10.0.0.1/24',
  listen_port: 51820,
  dns: '8.8.8.8',
  mtu: 1420
})

async function loadServers() {
  try {
    servers.value = await api.listServers()
  } catch (error) {
    alert('加载服务列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

async function createServer() {
  creating.value = true
  try {
    const result = await api.createServer(newServer.value)
    alert(`服务创建成功！\n公钥: ${result.public_key}\n私钥: ${result.private_key}\n\n请妥善保管密钥！`)
    showCreateModal.value = false
    loadServers()
  } catch (error) {
    alert('创建失败: ' + error.message)
  } finally {
    creating.value = false
  }
}

function viewServer(name) {
  router.push(`/server/${name}`)
}

async function startServer(name) {
  try {
    await api.startServer(name)
    alert('服务已启动')
    loadServers()
  } catch (error) {
    alert('启动失败: ' + error.message)
  }
}

async function stopServer(name) {
  try {
    await api.stopServer(name)
    alert('服务已停止')
    loadServers()
  } catch (error) {
    alert('停止失败: ' + error.message)
  }
}

async function confirmDelete(name) {
  if (confirm(`确定要删除服务 "${name}" 吗？`)) {
    try {
      await api.deleteServer(name)
      alert('服务已删除')
      loadServers()
    } catch (error) {
      alert('删除失败: ' + error.message)
    }
  }
}

onMounted(loadServers)
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

.loading, .empty {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.server-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.server-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.server-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.server-header h3 {
  color: #2c3e50;
}

.status {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
}

.status.active {
  background: #d4edda;
  color: #155724;
}

.status.inactive {
  background: #f8d7da;
  color: #721c24;
}

.server-info {
  margin: 1rem 0;
  color: #666;
}

.server-info p {
  margin: 0.5rem 0;
  font-size: 0.9rem;
}

.server-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
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
  color: #333;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.btn-primary, .btn-secondary, .btn-success, .btn-warning, .btn-danger, .btn-info {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover {
  background: #2980b9;
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
