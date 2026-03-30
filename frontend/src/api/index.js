const API_BASE = '/api/v1'

const DEFAULT_TIMEOUT = 10000
const MAX_RETRIES = 3
const RETRY_DELAY = 1000

class APIError extends Error {
  constructor(message, status, data) {
    super(message)
    this.name = 'APIError'
    this.status = status
    this.data = data
  }
}

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function request(url, options = {}) {
  const {
    timeout = DEFAULT_TIMEOUT,
    retries = MAX_RETRIES,
    retryDelay = RETRY_DELAY,
    ...fetchOptions
  } = options

  let lastError

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), timeout)

      const response = await fetch(`${API_BASE}${url}`, {
        ...fetchOptions,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...fetchOptions.headers
        }
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        let errorData = { error: '请求失败' }
        try {
          errorData = await response.json()
        } catch (e) {
          errorData = { error: `服务器错误 (${response.status})` }
        }
        throw new APIError(
          errorData.error || '请求失败',
          response.status,
          errorData
        )
      }

      const data = await response.json()
      return data

    } catch (error) {
      lastError = error

      if (error.name === 'AbortError') {
        lastError = new APIError('请求超时，请稍后重试', 408, null)
      }

      if (attempt < retries && !(error instanceof APIError && error.status >= 400 && error.status < 500)) {
        await delay(retryDelay * (attempt + 1))
        continue
      }

      throw lastError
    }
  }

  throw lastError
}

export const api = {
  getConfigPath: () => request('/config/path'),
  
  setConfigPath: (path) => request('/config/path', {
    method: 'POST',
    body: JSON.stringify({ path })
  }),
  
  listConnections: () => request('/connections'),
  
  generateKeys: () => request('/keys/generate', { method: 'POST' }),
  
  generatePresharedKey: () => request('/keys/preshared', { method: 'POST' }),
  
  derivePublicKey: (privateKey) => request('/keys/derive', {
    method: 'POST',
    body: JSON.stringify({ privateKey })
  }),
  
  getAllStatus: () => request('/connections/all-status'),
  
  getConnection: (name) => request(`/connections/${encodeURIComponent(name)}`),
  
  addConnection: (name, config) => request('/connections', {
    method: 'POST',
    body: JSON.stringify({ name, config })
  }),
  
  updateConnection: (name, config) => request(`/connections/${encodeURIComponent(name)}`, {
    method: 'PUT',
    body: JSON.stringify({ config })
  }),
  
  deleteConnection: (name) => request(`/connections/${encodeURIComponent(name)}`, {
    method: 'DELETE'
  }),
  
  connect: (name) => request(`/connections/${encodeURIComponent(name)}/connect`, {
    method: 'POST',
    timeout: 15000
  }),
  
  disconnect: (name) => request(`/connections/${encodeURIComponent(name)}/disconnect`, {
    method: 'POST',
    timeout: 15000
  }),
  
  getConnectionStatus: (name) => request(`/connections/${encodeURIComponent(name)}/status`),
  
  getConnectionStats: (connectionName) => request(`/stats/connections/${encodeURIComponent(connectionName)}`),
  
  getAllStats: () => request('/stats/connections'),
  
  getHistory: (limit = 50) => request(`/stats/history?limit=${limit}`),
  
  clearHistory: (connectionName) => request(`/stats/history?connection=${connectionName}`, {
    method: 'DELETE'
  }),
  
  listBackups: (connectionName) => {
    const url = connectionName 
      ? `/backups?connection=${encodeURIComponent(connectionName)}`
      : '/backups'
    return request(url)
  },
  
  restoreBackup: (connectionName, timestamp) => request(`/backups/${encodeURIComponent(connectionName)}/restore`, {
    method: 'POST',
    body: JSON.stringify({ timestamp })
  }),
  
  importConfig: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await fetch(`${API_BASE}/connections/import`, {
      method: 'POST',
      body: formData,
      timeout: 30000
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: '导入失败' }))
      throw new APIError(error.error || '导入失败', response.status, error)
    }
    
    return response.json()
  },
  
  exportConfig: async (name) => {
    const response = await fetch(`${API_BASE}/connections/${encodeURIComponent(name)}/export`)
    
    if (!response.ok) {
      throw new APIError('导出失败', response.status, null)
    }
    
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${name}.conf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  },
  
  healthCheck: () => request('/health')
}

export { APIError }
