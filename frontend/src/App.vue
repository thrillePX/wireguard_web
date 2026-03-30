<template>
  <div id="app" :class="{ 'dark-mode': isDarkMode }">
    <nav class="navbar">
      <div class="nav-container">
        <div class="nav-brand">
          <h1>WireGuard 连接管理器</h1>
        </div>
        <div class="nav-links">
          <router-link to="/">连接列表</router-link>
          <router-link to="/topology">网络拓扑</router-link>
          <router-link to="/settings">设置</router-link>
        </div>
        <button class="theme-toggle" @click="toggleTheme" :title="isDarkMode ? '切换到亮色' : '切换到暗色'">
          {{ isDarkMode ? '☀️' : '🌙' }}
        </button>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
    
    <Toast 
      v-for="toast in toasts" 
      :key="toast.id" 
      :message="toast.message" 
      :type="toast.type"
      :duration="toast.duration"
      @close="removeToast(toast.id)"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Toast from './components/Toast.vue'
import { useToast } from './composables/useToast'

const { toasts, remove: removeToast } = useToast()
const isDarkMode = ref(false)

function toggleTheme() {
  isDarkMode.value = !isDarkMode.value
  localStorage.setItem('darkMode', isDarkMode.value)
}

onMounted(() => {
  const saved = localStorage.getItem('darkMode')
  if (saved !== null) {
    isDarkMode.value = saved === 'true'
  } else {
    isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }
})
</script>

<style>
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-card: #ffffff;
  --bg-input: #ffffff;
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --border-color: #e5e7eb;
  --accent-color: #667eea;
  --success-color: #10b981;
  --danger-color: #ef4444;
  --shadow: rgba(0,0,0,0.1);
}

.dark-mode {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-card: #1e293b;
  --bg-input: #334155;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --border-color: #334155;
  --accent-color: #818cf8;
  --success-color: #34d399;
  --danger-color: #f87171;
  --shadow: rgba(0,0,0,0.3);
}

.dark-mode body,
.dark-mode {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.dark-mode .connection-list,
.dark-mode .connection-detail,
.dark-mode .topology,
.dark-mode .settings,
.dark-mode .server-list,
.dark-mode .server-detail,
.dark-mode .modal,
.dark-mode .form-group {
  background: var(--bg-card);
  color: var(--text-primary);
}

.dark-mode .header h2,
.dark-mode h3,
.dark-mode h4,
.dark-mode .stat-label,
.dark-mode .config-item .key,
.dark-mode .value {
  color: var(--text-primary);
}

.dark-mode .info-row,
.dark-mode .modal-header,
.dark-mode .modal-footer,
.dark-mode .config-block,
.dark-mode .tab-content {
  border-color: var(--border-color);
}

.dark-mode input,
.dark-mode textarea,
.dark-mode select {
  background: var(--bg-input);
  border-color: var(--border-color);
  color: var(--text-primary);
}

.dark-mode .btn-secondary {
  background: var(--bg-input);
  color: var(--text-primary);
  border-color: var(--border-color);
}

.dark-mode .status-badge.disconnected {
  background: var(--bg-input);
}

.dark-mode .empty {
  background: var(--bg-card);
}

.dark-mode .loading {
  color: var(--text-secondary);
}

.dark-mode .error {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger-color);
}

.dark-mode .spinner {
  border-color: var(--border-color);
  border-top-color: var(--accent-color);
}

.dark-mode .toggle-slider {
  background: var(--border-color);
}

.dark-mode .toggle-slider:before {
  background: white;
}

.dark-mode input:checked + .toggle-slider {
  background: var(--accent-color);
}

.dark-mode .traffic-section,
.dark-mode .speed-display,
.dark-mode .speed-chart,
.dark-mode .config-section {
  background: var(--bg-input);
}

.dark-mode .line-chart {
  background: var(--bg-input);
}

.dark-mode .chart-title,
.dark-mode .chart-legend {
  color: var(--text-secondary);
}

.dark-mode .chart-tooltip {
  background: var(--bg-card);
  color: var(--text-primary);
  border-color: var(--border-color);
}

.dark-mode .node circle,
.dark-mode .node rect {
  stroke: var(--accent-color);
}

.dark-mode .link {
  stroke: var(--border-color);
}

.dark-mode .connection-grid {
  background: transparent;
}

.dark-mode .connection-card {
  background: var(--bg-card);
  border-color: var(--border-color);
  box-shadow: 0 2px 8px var(--shadow);
}

.dark-mode .connection-card:hover {
  box-shadow: 0 4px 12px var(--shadow);
}

.dark-mode .empty-icon {
  opacity: 0.8;
}

.dark-mode .tab-btn {
  background: var(--bg-input);
  color: var(--text-secondary);
  border-color: var(--border-color);
}

.dark-mode .tab-btn.active {
  background: var(--accent-color);
  color: white;
}

.dark-mode .form-group label {
  color: var(--text-primary);
}

.dark-mode .generated-key {
  background: var(--bg-input);
  border-color: var(--border-color);
}

.dark-mode .stat-card {
  background: var(--bg-input);
}

.dark-mode .stat-value {
  color: var(--accent-color);
}

.dark-mode .btn-back {
  background: var(--bg-input);
  color: var(--text-primary);
  border-color: var(--border-color);
}

.dark-mode .btn-back:hover {
  background: var(--border-color);
}

.dark-mode .config-block {
  background: var(--bg-input);
}

.dark-mode .config-block h4 {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.dark-mode .section {
  background: var(--bg-card);
}

.dark-mode .total-traffic {
  background: var(--bg-input);
}

.dark-mode .legend-item {
  color: var(--text-secondary);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background: var(--bg-secondary);
  color: var(--text-primary);
  transition: background 0.3s, color 0.3s;
}

#app {
  min-height: 100vh;
}

.navbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-brand h1 {
  font-size: 1.5rem;
  font-weight: 600;
}

.nav-links {
  display: flex;
  gap: 2rem;
}

.nav-links a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background 0.3s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  background: rgba(255,255,255,0.2);
}

.theme-toggle {
  background: rgba(255,255,255,0.2);
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.3s;
}

.theme-toggle:hover {
  background: rgba(255,255,255,0.3);
  transform: rotate(15deg);
}

.main-content {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 2rem;
}

button {
  cursor: pointer;
  font-family: inherit;
}

.connection-list, .connection-detail, .topology, .settings {
  background: var(--bg-primary);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.dark-mode .connection-list,
.dark-mode .connection-detail,
.dark-mode .topology,
.dark-mode .settings {
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.header h2 {
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-primary, .btn-secondary, .btn-connect, .btn-disconnect, .btn-danger, .btn-info {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-connect {
  background: var(--success-color);
  color: white;
}

.btn-disconnect {
  background: var(--danger-color);
  color: white;
}

.btn-danger {
  background: var(--danger-color);
  color: white;
}

.btn-info {
  background: #3b82f6;
  color: white;
}

.connection-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1rem;
  transition: all 0.2s;
}

.connection-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.connection-card.connected {
  border-left: 4px solid var(--success-color);
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-badge.connected {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success-color);
}

.status-badge.disconnected {
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border-color);
}

.info-row .label {
  color: var(--text-secondary);
}

.info-row .value {
  color: var(--text-primary);
  font-weight: 500;
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
  z-index: 100;
}

.modal {
  background: var(--bg-card);
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-secondary);
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-color);
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: 8px;
  margin-bottom: 1rem;
}

.filter-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  color: var(--text-primary);
}

.copy-btn {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
}

.copy-btn:hover {
  background: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
}
</style>
