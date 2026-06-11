<template>
  <el-card class="dashboard-card">
    <div class="dashboard-grid">
      <!-- Score Gauge -->
      <div class="gauge-section">
        <v-chart :option="gaugeOption" autoresize style="height: 200px" />
        <div class="score-label">合规评分</div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-section">
        <div class="stat-item critical">
          <div class="stat-value">{{ result.summary.by_severity.critical || 0 }}</div>
          <div class="stat-label">严重</div>
        </div>
        <div class="stat-item serious">
          <div class="stat-value">{{ result.summary.by_severity.serious || 0 }}</div>
          <div class="stat-label">重要</div>
        </div>
        <div class="stat-item moderate">
          <div class="stat-value">{{ result.summary.by_severity.moderate || 0 }}</div>
          <div class="stat-label">中等</div>
        </div>
        <div class="stat-item minor">
          <div class="stat-value">{{ result.summary.by_severity.minor || 0 }}</div>
          <div class="stat-label">轻微</div>
        </div>
      </div>

      <!-- Impact Groups Chart -->
      <div class="chart-section">
        <v-chart :option="impactChartOption" autoresize style="height: 200px" />
      </div>

      <!-- Rule Distribution -->
      <div class="chart-section">
        <v-chart :option="ruleChartOption" autoresize style="height: 200px" />
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { GaugeChart, BarChart, PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, GaugeChart, BarChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const props = defineProps({
  result: { type: Object, required: true }
})

const impactGroupLabels = {
  blind: '视障用户',
  low_vision: '低视力',
  color_blind: '色盲/色弱',
  motor: '键盘用户',
  cognitive: '认知障碍',
}

const gaugeOption = computed(() => {
  const score = props.result.score
  let color = '#f56c6c'
  if (score >= 80) color = '#67c23a'
  else if (score >= 60) color = '#e6a23c'

  return {
    series: [{
      type: 'gauge',
      startAngle: 200,
      endAngle: -20,
      min: 0,
      max: 100,
      progress: { show: true, width: 14 },
      pointer: { show: false },
      axisLine: { lineStyle: { width: 14, color: [[1, '#e0e0e0']] } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      detail: {
        valueAnimation: true,
        fontSize: 32,
        fontWeight: 'bold',
        formatter: '{value}',
        color,
        offsetCenter: [0, '0%'],
      },
      data: [{ value: score, itemStyle: { color } }],
    }]
  }
})

const impactChartOption = computed(() => {
  const groups = props.result.summary.by_impact_group || {}
  const data = Object.entries(groups).map(([key, value]) => ({
    name: impactGroupLabels[key] || key,
    value
  }))

  return {
    title: { text: '受影响人群', left: 'center', textStyle: { fontSize: 13 } },
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],
      data,
      label: { fontSize: 11 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.2)' } },
    }]
  }
})

const ruleChartOption = computed(() => {
  const rules = props.result.summary.by_rule || {}
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

  const entries = Object.entries(rules).sort((a, b) => b[1] - a[1]).slice(0, 8)

  return {
    title: { text: '问题类型分布', left: 'center', textStyle: { fontSize: 13 } },
    tooltip: {},
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: entries.map(([k]) => ruleLabels[k] || k),
      axisLabel: { rotate: 30, fontSize: 10 },
    },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      data: entries.map(([, v]) => v),
      itemStyle: {
        color: (params) => {
          const colors = ['#f56c6c', '#e6a23c', '#409eff', '#67c23a', '#909399', '#b37feb', '#f759ab', '#36cfc9']
          return colors[params.dataIndex % colors.length]
        }
      }
    }]
  }
})
</script>

<style scoped>
.dashboard-card {
  margin-bottom: 20px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 200px 1fr 1fr 1fr;
  gap: 20px;
  align-items: center;
}

.gauge-section {
  text-align: center;
}

.score-label {
  font-size: 13px;
  color: #909399;
  margin-top: -10px;
}

.stats-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 6px;
  background: #f5f7fa;
}

.stat-item.critical { border-left: 3px solid #f56c6c; }
.stat-item.serious { border-left: 3px solid #e6a23c; }
.stat-item.moderate { border-left: 3px solid #409eff; }
.stat-item.minor { border-left: 3px solid #67c23a; }

.stat-value {
  font-size: 20px;
  font-weight: bold;
  min-width: 30px;
}

.stat-label {
  font-size: 13px;
  color: #606266;
}

.chart-section {
  min-height: 200px;
}
</style>
