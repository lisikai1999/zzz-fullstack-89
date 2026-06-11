<template>
  <div class="app-container">
    <el-container>
      <el-header class="app-header">
        <h1>WCAG 无障碍检测工具</h1>
        <span class="subtitle">Level A & AA 合规性检测</span>
      </el-header>
      <el-main>
        <ScanInput @scan-complete="handleScanComplete" @scanning="scanning = true" />

        <template v-if="scanResult">
          <ScoreDashboard :result="scanResult" />

          <el-row :gutter="20" class="content-row">
            <el-col :span="14">
              <IssueList
                :issues="scanResult.issues"
                :summary="scanResult.summary"
                @select-issue="handleSelectIssue"
              />
            </el-col>
            <el-col :span="10">
              <FixPanel :issue="selectedIssue" />
              <PagePreview
                :scan-id="scanResult.id"
                :issues="scanResult.issues"
                :selected-issue="selectedIssue"
              />
            </el-col>
          </el-row>
        </template>

        <el-empty v-else-if="!scanning" description="输入 URL 开始检测网页无障碍合规性" />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ScanInput from './components/ScanInput.vue'
import ScoreDashboard from './components/ScoreDashboard.vue'
import IssueList from './components/IssueList.vue'
import FixPanel from './components/FixPanel.vue'
import PagePreview from './components/PagePreview.vue'

const scanResult = ref(null)
const selectedIssue = ref(null)
const scanning = ref(false)

function handleScanComplete(result) {
  scanResult.value = result
  selectedIssue.value = null
  scanning.value = false
}

function handleSelectIssue(issue) {
  selectedIssue.value = issue
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background: #f5f7fa;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
}

.app-container {
  min-height: 100vh;
}

.app-header {
  background: #1a1a2e;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 24px;
}

.app-header h1 {
  font-size: 20px;
  font-weight: 600;
}

.app-header .subtitle {
  font-size: 13px;
  opacity: 0.7;
}

.el-main {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
}

.content-row {
  margin-top: 20px;
}
</style>
