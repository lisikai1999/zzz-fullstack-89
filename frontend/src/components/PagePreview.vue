<template>
  <el-card class="preview-card">
    <template #header>
      <div class="panel-header">
        <el-icon><Monitor /></el-icon>
        <span>页面预览</span>
        <el-tag v-if="issues.length" size="small" type="warning">
          {{ issues.length }} 个问题标注
        </el-tag>
      </div>
    </template>

    <div class="preview-container" ref="previewContainer">
      <iframe
        ref="previewFrame"
        class="preview-frame"
        sandbox="allow-same-origin"
        :srcdoc="annotatedHtml"
        @load="onFrameLoad"
      ></iframe>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { Monitor } from '@element-plus/icons-vue'
import { getScanHtml } from '../api'

const props = defineProps({
  scanId: { type: Number, required: true },
  issues: { type: Array, default: () => [] },
  selectedIssue: { type: Object, default: null },
})

const previewFrame = ref(null)
const previewContainer = ref(null)
const htmlContent = ref('')

watch(() => props.scanId, async (newId) => {
  if (newId) {
    try {
      const { data } = await getScanHtml(newId)
      htmlContent.value = data.html || ''
    } catch (e) {
      htmlContent.value = '<p>无法加载页面预览</p>'
    }
  }
}, { immediate: true })

const annotatedHtml = computed(() => {
  if (!htmlContent.value) return ''

  const highlightStyle = `
    <style>
      [data-wcag-issue] {
        outline: 2px solid #f56c6c !important;
        outline-offset: 2px;
        position: relative;
      }
      [data-wcag-issue]::after {
        content: attr(data-wcag-label);
        position: absolute;
        top: -18px;
        left: 0;
        background: #f56c6c;
        color: #fff;
        font-size: 10px;
        padding: 1px 4px;
        border-radius: 2px;
        white-space: nowrap;
        z-index: 99999;
        pointer-events: none;
      }
      [data-wcag-issue-selected] {
        outline-color: #409eff !important;
        outline-width: 3px !important;
        animation: wcag-pulse 1s infinite;
      }
      [data-wcag-issue-selected]::after {
        background: #409eff !important;
      }
      @keyframes wcag-pulse {
        0%, 100% { outline-offset: 2px; }
        50% { outline-offset: 4px; }
      }
      body { transform: scale(0.6); transform-origin: top left; width: 166.67%; }
    </style>
  `

  let html = htmlContent.value
  // Inject highlight styles into the head
  if (html.includes('</head>')) {
    html = html.replace('</head>', highlightStyle + '</head>')
  } else {
    html = highlightStyle + html
  }

  return html
})

function onFrameLoad() {
  highlightIssues()
}

watch(() => props.selectedIssue, () => {
  highlightIssues()
})

function highlightIssues() {
  const iframe = previewFrame.value
  if (!iframe || !iframe.contentDocument) return

  const doc = iframe.contentDocument
  // Clear previous highlights
  doc.querySelectorAll('[data-wcag-issue]').forEach(el => {
    el.removeAttribute('data-wcag-issue')
    el.removeAttribute('data-wcag-label')
    el.removeAttribute('data-wcag-issue-selected')
  })

  // Apply highlights
  for (const issue of props.issues) {
    try {
      const selector = issue.element_selector
      if (!selector) continue
      const el = doc.querySelector(selector)
      if (el) {
        el.setAttribute('data-wcag-issue', 'true')
        el.setAttribute('data-wcag-label', issue.rule_name)

        if (props.selectedIssue && props.selectedIssue.id === issue.id) {
          el.setAttribute('data-wcag-issue-selected', 'true')
          el.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      }
    } catch (e) {
      // Selector might not be valid in the preview context
    }
  }
}
</script>

<style scoped>
.preview-card {
  margin-top: 16px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.panel-header .el-tag {
  margin-left: auto;
}

.preview-container {
  height: 350px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
  background: #fff;
}

.preview-frame {
  width: 100%;
  height: 100%;
  border: none;
}
</style>
