import { ref } from 'vue'

const STORAGE_KEY = 'wireguard_connection_history'

export function useConnectionHistory() {
  const history = ref(loadHistory())

  function loadHistory() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      return stored ? JSON.parse(stored) : {}
    } catch (error) {
      console.error('加载连接历史失败:', error)
      return {}
    }
  }

  function saveHistory() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history.value))
    } catch (error) {
      console.error('保存连接历史失败:', error)
    }
  }

  function recordUsage(connectionName) {
    const now = Date.now()
    if (!history.value[connectionName]) {
      history.value[connectionName] = {
        lastUsed: now,
        count: 0,
        pinned: false
      }
    }
    history.value[connectionName].lastUsed = now
    history.value[connectionName].count++
    saveHistory()
  }

  function togglePin(connectionName) {
    if (!history.value[connectionName]) {
      history.value[connectionName] = {
        lastUsed: 0,
        count: 0,
        pinned: true
      }
    } else {
      history.value[connectionName].pinned = !history.value[connectionName].pinned
    }
    saveHistory()
  }

  function getSortScore(connection) {
    const info = history.value[connection.name] || { lastUsed: 0, count: 0, pinned: false }
    
    let score = 0
    
    if (connection.connected) {
      score += 100000
    }
    
    if (info.pinned) {
      score += 50000
    }
    
    score += info.count * 100
    
    score += info.lastUsed / 1000000
    
    return score
  }

  function getConnectionInfo(connectionName) {
    return history.value[connectionName] || { lastUsed: 0, count: 0, pinned: false }
  }

  function clearHistory() {
    history.value = {}
    saveHistory()
  }

  return {
    history,
    recordUsage,
    togglePin,
    getSortScore,
    getConnectionInfo,
    clearHistory
  }
}
