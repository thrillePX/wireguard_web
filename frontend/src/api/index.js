const API_BASE = '/api'

async function request(url, options = {}) {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: '请求失败' }))
    throw new Error(error.error || '请求失败')
  }
  
  return response.json()
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
    method: 'POST'
  }),
  
  disconnect: (name) => request(`/connections/${encodeURIComponent(name)}/disconnect`, {
    method: 'POST'
  }),
  
  getConnectionStatus: (name) => request(`/connections/${encodeURIComponent(name)}/status`),
  
  importConfig: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await fetch(`${API_BASE}/connections/import`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: '导入失败' }))
      throw new Error(error.error || '导入失败')
    }
    
    return response.json()
  },
  
  exportConfig: async (name) => {
    const response = await fetch(`${API_BASE}/connections/${encodeURIComponent(name)}/export`)
    
    if (!response.ok) {
      throw new Error('导出失败')
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
