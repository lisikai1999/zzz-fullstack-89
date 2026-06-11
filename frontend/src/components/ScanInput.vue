<template>
  <el-card class="scan-input-card">
    <el-form @submit.prevent="handleScan" inline>
      <el-form-item style="flex: 1">
        <el-input
          v-model="url"
          placeholder="输入要检测的网页 URL，如 https://example.com"
          size="large"
          :prefix-icon="Link"
          clearable
          :disabled="loading"
        />
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          @click="handleScan"
          :icon="Search"
        >
          {{ loading ? '检测中...' : '开始检测' }}
        </el-button>
      </el-form-item>
    </el-form>
    <div v-if="loading" class="progress-hint">
      <el-icon class="is-loading"><Loading /></el-icon>
      正在抓取页面并逐节点分析 DOM 树...
    </div>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import { Link, Search, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { scanUrl } from '../api'

const emit = defineEmits(['scan-complete', 'scanning'])
const url = ref('')
const loading = ref(false)

async function handleScan() {
  if (!url.value.trim()) {
    ElMessage.warning('请输入要检测的 URL')
    return
  }

  loading.value = true
  emit('scanning')

  try {
    const { data } = await scanUrl(url.value.trim())
    emit('scan-complete', data)
    ElMessage.success(`检测完成，发现 ${data.total_issues} 个问题`)
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || '检测失败'
    ElMessage.error(`检测失败: ${msg}`)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.scan-input-card {
  margin-bottom: 20px;
}

.scan-input-card .el-form {
  display: flex;
  width: 100%;
}

.scan-input-card .el-form-item:first-child {
  flex: 1;
  margin-right: 12px;
}

.progress-hint {
  margin-top: 12px;
  color: #909399;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
