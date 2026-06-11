import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

export function scanUrl(url) {
  return api.post('/scan', { url })
}

export function getScan(scanId) {
  return api.get(`/scan/${scanId}`)
}

export function getScanHtml(scanId) {
  return api.get(`/scan/${scanId}/html`)
}

export function listScans(limit = 20, offset = 0) {
  return api.get('/scans', { params: { limit, offset } })
}

export default api
