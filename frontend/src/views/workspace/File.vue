<script setup lang="ts">
import { Document, Download } from '@element-plus/icons-vue';
import { onMounted } from 'vue';
import { useCurrentFileStore } from '../../utils/state';
import { downloadFile } from '../../api/file';
import { ElMessage } from 'element-plus';

const currentFile = useCurrentFileStore();

onMounted(() => {
  currentFile.localStorageCurrentFileInfo();
});

function downloadResult() {
  downloadFile( currentFile.file_id).then(res => {
    const url = window.URL.createObjectURL(res.data);
    const a = document.createElement('a');
    a.href = url;
    a.download = currentFile.filename; // 设置下载的文件名
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }).catch(err => {
    console.log(err);
    ElMessage.error(`Failed to download ${currentFile.filename}`);
  });
}

</script>

<template>
  <el-main class="main-frame">
    <el-card class="main-card">
      <template #header>
        <div class="header">
          <el-space :size="16">
            <el-icon :size="50" color="#42a5f5"><Document /></el-icon>
            <span class="header-title">{{ currentFile.filename }}</span>
          </el-space>

          <el-button type="primary" :icon="Download" @click="downloadResult">Download</el-button>
        </div>
      </template>

      <el-descriptions title="Overview" border>
        <el-descriptions-item label="Name">
          {{ currentFile.file_id }}
        </el-descriptions-item>
        <el-descriptions-item label="Size">
          {{ currentFile.size }}
        </el-descriptions-item>
        <el-descriptions-item label="Upload Time">
          {{ currentFile.uploaded_at }}
        </el-descriptions-item>
        <el-descriptions-item label="Status">
          <el-tag type="success">
            {{ currentFile.status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Fraud Posibility">
          {{ currentFile.status }}
        </el-descriptions-item>
      </el-descriptions>

      <el-collapse>
        <el-collapse-item title="Current Transactions" name="ct">
          <el-descriptions :column="1" border>
            <el-descriptions-item 
              v-for="pair in currentFile.resultData.content.current_transaction"
              :label="pair.key"
            >
              {{ pair.value }}
            </el-descriptions-item>
          </el-descriptions>
        </el-collapse-item>

        <el-collapse-item title="Related Transactions" name="rt">
          <el-descriptions :column="3" border>
            <el-descriptions-item 
              v-for="pair in currentFile.resultData.content.related_transactions"
              :label="pair.key"
            >
              {{ pair.value }}
            </el-descriptions-item>
          </el-descriptions>
        </el-collapse-item>

        <el-collapse-item title="Operation Information" name="oi">
          <el-descriptions :column="2" border>
            <el-descriptions-item 
              v-for="pair in currentFile.resultData.content.operation_information"
              :label="pair.key"
            >
              {{ pair.value }}
            </el-descriptions-item>
          </el-descriptions>
        </el-collapse-item>

        <el-collapse-item title="Initial Account" name="ia">
          <el-descriptions :column="4" border>
            <el-descriptions-item 
              v-for="pair in currentFile.resultData.content.initial_account"
              :label="pair.key"
            >
              {{ pair.value }}
            </el-descriptions-item>
          </el-descriptions>
        </el-collapse-item>

        <el-collapse-item title="Target Account" name="ta">
          <el-descriptions :column="3" border>
            <el-descriptions-item 
              v-for="pair in currentFile.resultData.content.target_account"
              :label="pair.key"
            >
              {{ pair.value }}
            </el-descriptions-item>
          </el-descriptions>
        </el-collapse-item>

        <el-collapse-item title="Fraud Dectection" name="fd">
          <el-descriptions :column="1" border>
            <el-descriptions-item 
              v-for="pair in currentFile.resultData.content.fraud_detection"
              :label="pair.key"
            >
              {{ pair.value }}
            </el-descriptions-item>
          </el-descriptions>
        </el-collapse-item>

      </el-collapse>
      
    </el-card>
  </el-main>
</template>

<style scoped>

.main-frame {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 30px 15px;
  gap: 5px;
  justify-content: center;
  align-items: center;
}

.main-card {
  width: 90%;
  height: auto;
  flex-grow: 1;
  overflow: hidden;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title {
  font-size: 20px;
  font-weight: bold;
  color: #2c2c2c;
}

</style>