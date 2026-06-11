<template>
  <el-card class="issue-list-card">
    <template #header>
      <div class="card-header">
        <span>问题列表 ({{ filteredIssues.length }})</span>
        <div class="filters">
          <el-select v-model="filterSeverity" placeholder="严重程度" clearable size="small" style="width: 110px">
            <el-option label="严重" value="critical" />
            <el-option label="重要" value="serious" />
            <el-option label="中等" value="moderate" />
            <el-option label="轻微" value="minor" />
          </el-select>
          <el-select v-model="filterRule" placeholder="规则类型" clearable size="small" style="width: 130px">
            <el-option v-for="rule in availableRules" :key="rule" :label="ruleLabels[rule] || rule" :value="rule" />
          </el-select>
          <el-select v-model="filterRegion" placeholder="页面区域" clearable size="small" style="width: 110px">
            <el-option v-for="region in availableRegions" :key="region" :label="regionLabels[region] || region" :value="region" />
          </el-select>
        </div>
      </div>
    </template>

    <div class="issue-list-scroll">
      <div
        v-for="issue in filteredIssues"
        :key="issue.id"
        class="issue-item"
        :class="{ selected: selectedId === issue.id }"
        @click="selectIssue(issue)"
      >
        <div class="issue-header">
          <el-tag :type="severityType(issue.severity)" size="small" effect="dark">
            {{ severityLabel(issue.severity) }}
          </el-tag>
          <el-tag size="small" effect="plain">
            WCAG {{ issue.wcag_criterion }}
          </el-tag>
          <el-tag size="small" type="info" effect="plain">
            {{ issue.wcag_level }}
          </el-tag>
          <span class="issue-region">{{ regionLabels[issue.page_region] || issue.page_region }}</span>
        </div>
        <div class="issue-title">{{ issue.rule_name }}</div>
        <div class="issue-desc">{{ issue.description }}</div>
        <div class="issue-impact">
          <el-icon><User /></el-icon>
          {{ formatImpactGroup(issue.impact_group) }}
        </div>
      </div>

      <el-empty v-if="filteredIssues.length === 0" description="没有匹配的问题" />
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { User } from '@element-plus/icons-vue'

const props = defineProps({
  issues: { type: Array, default: () => [] },
  summary: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['select-issue'])

const filterSeverity = ref('')
const filterRule = ref('')
const filterRegion = ref('')
const selectedId = ref(null)

const ruleLabels = {
  'img-alt-missing': '图片缺alt',
  'img-alt-empty': '空alt文本',
  'form-label-missing': '表单缺label',
  'link-text-empty': '空链接文本',
  'link-text-generic': '泛化链接文本',
  'heading-skip': '标题层级跳跃',
  'contrast-insufficient': '对比度不足',
  'keyboard-no-access': '键盘不可访问',
  'keyboard-tabindex-positive': 'tabindex滥用',
  'aria-invalid-role': 'ARIA角色无效',
  'aria-missing-property': 'ARIA属性缺失',
  'aria-hidden-focusable': 'aria-hidden冲突',
  'html-lang-missing': '缺少lang属性',
  'page-title-missing': '缺少页面标题',
}

const regionLabels = {
  header: '页头',
  nav: '导航',
  main: '主内容',
  footer: '页脚',
  aside: '侧边栏',
  form: '表单',
  body: '页面主体',
}

const impactLabels = {
  blind: '视障',
  low_vision: '低视力',
  color_blind: '色盲/色弱',
  motor: '键盘用户',
  cognitive: '认知障碍',
}

const availableRules = computed(() => {
  return [...new Set(props.issues.map(i => i.rule_id))]
})

const availableRegions = computed(() => {
  return [...new Set(props.issues.map(i => i.page_region))]
})

const filteredIssues = computed(() => {
  return props.issues.filter(i => {
    if (filterSeverity.value && i.severity !== filterSeverity.value) return false
    if (filterRule.value && i.rule_id !== filterRule.value) return false
    if (filterRegion.value && i.page_region !== filterRegion.value) return false
    return true
  })
})

function selectIssue(issue) {
  selectedId.value = issue.id
  emit('select-issue', issue)
}

function severityType(severity) {
  const map = { critical: 'danger', serious: 'warning', moderate: '', minor: 'success' }
  return map[severity] || 'info'
}

function severityLabel(severity) {
  const map = { critical: '严重', serious: '重要', moderate: '中等', minor: '轻微' }
  return map[severity] || severity
}

function formatImpactGroup(group) {
  return group.split(',').map(g => impactLabels[g.trim()] || g.trim()).join('、')
}
</script>

<style scoped>
.issue-list-card {
  height: calc(100vh - 400px);
  min-height: 400px;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.filters {
  display: flex;
  gap: 8px;
}

.issue-list-scroll {
  overflow-y: auto;
  flex: 1;
  max-height: calc(100vh - 500px);
}

.issue-item {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.2s;
  border-radius: 4px;
  margin-bottom: 4px;
}

.issue-item:hover {
  background: #f5f7fa;
}

.issue-item.selected {
  background: #ecf5ff;
  border-left: 3px solid #409eff;
}

.issue-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.issue-region {
  margin-left: auto;
  font-size: 12px;
  color: #909399;
}

.issue-title {
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 4px;
}

.issue-desc {
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.issue-impact {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
