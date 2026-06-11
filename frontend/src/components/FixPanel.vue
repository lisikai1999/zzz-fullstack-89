<template>
  <el-card v-if="issue" class="fix-panel-card">
    <template #header>
      <div class="panel-header">
        <el-icon><MagicStick /></el-icon>
        <span>修复建议</span>
      </div>
    </template>

    <div class="fix-content">
      <div class="fix-section">
        <h4>问题描述</h4>
        <p>{{ issue.description }}</p>
      </div>

      <div class="fix-section">
        <h4>WCAG 标准</h4>
        <div class="criterion-info">
          <el-tag size="small" effect="plain">WCAG {{ issue.wcag_criterion }}</el-tag>
          <el-tag size="small" :type="issue.wcag_level === 'A' ? 'danger' : 'warning'" effect="dark">
            Level {{ issue.wcag_level }}
          </el-tag>
        </div>
      </div>

      <div class="fix-section">
        <h4>影响人群</h4>
        <div class="impact-tags">
          <el-tag
            v-for="group in impactGroups"
            :key="group"
            size="small"
            :type="impactTagType(group)"
            effect="light"
          >
            {{ impactLabels[group] || group }}
          </el-tag>
        </div>
      </div>

      <div class="fix-section">
        <h4>修复方案</h4>
        <p class="fix-suggestion">{{ issue.fix_suggestion }}</p>
      </div>

      <div v-if="issue.fix_code" class="fix-section">
        <h4>修复代码</h4>
        <div class="code-block">
          <pre><code>{{ issue.fix_code }}</code></pre>
          <el-button size="small" @click="copyCode" :icon="CopyDocument" class="copy-btn">
            复制
          </el-button>
        </div>
      </div>

      <div v-if="issue.contrast_actual" class="fix-section">
        <h4>对比度详情</h4>
        <div class="contrast-info">
          <div class="contrast-row">
            <span>当前对比度:</span>
            <span class="contrast-value bad">{{ issue.contrast_actual }}:1</span>
          </div>
          <div class="contrast-row">
            <span>要求对比度:</span>
            <span class="contrast-value required">≥ {{ issue.contrast_required }}:1</span>
          </div>
          <div v-if="issue.suggested_color" class="contrast-row">
            <span>建议颜色:</span>
            <span class="contrast-value good">
              <span class="color-swatch" :style="{ background: issue.suggested_color }"></span>
              {{ issue.suggested_color }}
            </span>
          </div>
        </div>
      </div>

      <div class="fix-section">
        <h4>问题元素</h4>
        <div class="element-preview">
          <code>{{ issue.element_html }}</code>
        </div>
      </div>
    </div>
  </el-card>

  <el-card v-else class="fix-panel-card empty">
    <el-empty description="点击左侧问题查看修复建议" :image-size="60" />
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { MagicStick, CopyDocument } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  issue: { type: Object, default: null }
})

const impactLabels = {
  blind: '视障用户',
  low_vision: '低视力用户',
  color_blind: '色盲/色弱用户',
  motor: '键盘用户',
  cognitive: '认知障碍用户',
}

const impactGroups = computed(() => {
  if (!props.issue) return []
  return props.issue.impact_group.split(',').map(g => g.trim())
})

function impactTagType(group) {
  const map = { blind: 'danger', low_vision: 'warning', color_blind: 'warning', motor: '', cognitive: 'info' }
  return map[group] || 'info'
}

function copyCode() {
  if (props.issue?.fix_code) {
    navigator.clipboard.writeText(props.issue.fix_code)
    ElMessage.success('已复制到剪贴板')
  }
}
</script>

<style scoped>
.fix-panel-card {
  margin-bottom: 16px;
}

.fix-panel-card.empty {
  min-height: 150px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.fix-content {
  max-height: 400px;
  overflow-y: auto;
}

.fix-section {
  margin-bottom: 16px;
}

.fix-section h4 {
  font-size: 13px;
  color: #303133;
  margin-bottom: 6px;
  font-weight: 600;
}

.fix-section p {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.criterion-info {
  display: flex;
  gap: 6px;
}

.impact-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.fix-suggestion {
  background: #f0f9eb;
  padding: 10px;
  border-radius: 4px;
  border-left: 3px solid #67c23a;
}

.code-block {
  position: relative;
  background: #1a1a2e;
  border-radius: 6px;
  padding: 12px;
  overflow-x: auto;
}

.code-block pre {
  margin: 0;
}

.code-block code {
  color: #e0e0e0;
  font-size: 12px;
  font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
  white-space: pre-wrap;
  word-break: break-all;
}

.copy-btn {
  position: absolute;
  top: 6px;
  right: 6px;
}

.contrast-info {
  background: #fafafa;
  padding: 10px;
  border-radius: 4px;
}

.contrast-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 13px;
}

.contrast-value {
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}

.contrast-value.bad { color: #f56c6c; }
.contrast-value.required { color: #909399; }
.contrast-value.good { color: #67c23a; }

.color-swatch {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  border: 1px solid #ddd;
  display: inline-block;
}

.element-preview {
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}

.element-preview code {
  font-size: 11px;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
