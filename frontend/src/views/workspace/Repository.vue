<script setup lang="ts">
import {
  ElementPlus,
  Avatar,
  Edit,
  Delete,
  Upload,
  Download,
  VideoPlay,
  User,
  ChatSquare,
} from "@element-plus/icons-vue";
import { onMounted, reactive, ref, onUnmounted } from "vue";
import {
  useUserStore,
  useCurrentRepoStore,
  useCurrentFileStore,
} from "../../utils/state";
import {
  updateRepoName,
  updateRepoDesc,
  deleteRepo as deleteRepoApi,
  updateRepoCollaborators,
  getRepo,
} from "../../api/repo";
import { router } from "../../router";
import { ElMessage, ElMessageBox, type UploadFile } from "element-plus";
import "element-plus/theme-chalk/el-message.css";
import "element-plus/theme-chalk/el-message-box.css";
import {
  downloadFile,
  uploadFile,
  type file,
  deleteFile,
  getFileMetadata,
  getFileJsonResult,
} from "../../api/file";
import { processFile } from "../../api/process";
import { checkAuth } from "../../utils/directives";
import { wsService } from "../../utils/socket";

const userStore = useUserStore();
const currentRepo = useCurrentRepoStore();
const currentFile = useCurrentFileStore();

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

const searchInput = ref("");

const repoEditorVisible = ref(false);
const repoEditorForm = reactive({
  name: "",
  desc: "",
});

const collaboratorVisible = ref(false);
const collaboratorInput = ref("");

const uploadVisible = ref(false);
const uploadFiles = ref<UploadFile[]>([]);

onMounted(() => {
  userStore.localStorageUserData();
  currentRepo.localStorageCurrentRepoData();

  if (!checkAuth()) {
    ElMessage.warning("请先登录后再访问此页面");
    router.push({
      path: "/login",
      query: { redirect: router.currentRoute.value.fullPath },
    });
    return;
  }

  if (!currentRepo.id) {
    ElMessage.warning("Please select a repository first");
    router.push("/dashboard");
    return;
  }

  // 建立WebSocket连接
  wsService.connect(currentRepo.id);
});

onUnmounted(() => {
  wsService.disconnect();
});

function openRepoEditor() {
  repoEditorForm.name = currentRepo.name;
  repoEditorForm.desc = currentRepo.desc;
  repoEditorVisible.value = true;
}

function editRepo() {
  if (repoEditorForm.name !== currentRepo.name) {
    updateRepoName(currentRepo.id, {
      new_name: repoEditorForm.name,
      new_desc: currentRepo.desc,
    }).catch((error) => {
      console.error(error);
    });
  }
  if (repoEditorForm.desc !== currentRepo.desc) {
    updateRepoDesc(currentRepo.id, {
      new_name: repoEditorForm.name,
      new_desc: repoEditorForm.desc,
    }).catch((error) => {
      console.error(error);
    });
  }
  currentRepo.updateCurrentRepoNameAndDesc(
    repoEditorForm.name,
    repoEditorForm.desc
  );
  repoEditorVisible.value = false;
}

function deleteRepo() {
  ElMessageBox.confirm("Delete this repo ?", "Warning", {
    confirmButtonText: "Confirm",
    cancelButtonText: "Cancel",
    type: "warning",
  }).then(() => {
    deleteRepoApi(currentRepo.id)
      .catch((error) => {
        console.error(error);
      })
      .then(() => {
        userStore.updateRepos(
          userStore.repos.filter((repo) => repo !== currentRepo.id)
        );
        currentRepo.clearCurrentRepoInfo();
        router.push("/dashboard").then(() => {
          router.go(0);
        });
      });
  });
}

function openCollaboratorAdder() {
  collaboratorInput.value = "";
  collaboratorVisible.value = true;
}

function addCollaborator() {
  updateRepoCollaborators(currentRepo.id, {
    collaborator_id: collaboratorInput.value,
  })
    .then((response) => {
      if (response.status === 200) {
        currentRepo.collaborators.push(collaboratorInput.value);
        currentRepo.updateCurrentRepoCollaborators(currentRepo.collaborators);
      }
    })
    .catch((error) => {
      console.error(error);
      ElMessage.error("Invalid User ID or User Already Exist");
    });
  collaboratorVisible.value = false;
}

function openUploader() {
  uploadVisible.value = true;
}

async function uploadAllFiles() {
  try {
    // 等待所有文件上传完成
    await Promise.all(
      uploadFiles.value.map(async (file) => {
        const response = await uploadFile(
          currentRepo.id,
          file.raw as File,
          true
        );
        // 发送WebSocket消息通知上传完成
        wsService.sendMessage("FILE_UPLOADED", {
          repo_id: currentRepo.id,
          file_id: response.file_id
        });
        return response;
      })
    );

    uploadFiles.value = [];
    uploadVisible.value = false;
    ElMessage.success("文件上传成功");
  } catch (err) {
    console.error(err);
    ElMessage.error("上传文件失败，请重试");
  }
}

async function analyseFile(file: file) {
  try {
    await processFile(currentRepo.id, file.file_id);
    file.status = "processing";

    // 发送WebSocket消息通知开始处理
    wsService.sendMessage("FILE_STATUS_CHANGED", {
      repo_id: currentRepo.id,
      file_id: file.file_id,
      status: "processing"
    });

    console.log("开始分析文件");
  } catch (err) {
    console.error(err);
    file.status = "error";
    ElMessage.error("处理文件失败");
  }
}

function removeFile(file: file) {
  ElMessageBox.confirm("Delete this file ?", "Warning", {
    confirmButtonText: "Confirm",
    cancelButtonText: "Cancel",
    type: "warning",
  }).then(() => {
    deleteFile(file.file_id)
      .then(() => {
        getRepo(currentRepo.id)
          .then((res) => {
            if (res.status == 200) {
              currentRepo.setCurrentRepoInfo(res.data);
            }
          })
          .catch((err) => {
            console.log(err);
            ElMessage.error(`Fail to update info, please refresh manually`);
          });
      })
      .catch((err) => {
        console.log(err);
        ElMessage.error(`Fail to delete file`);
      });
  });
}

function downloadResult(file: file) {
  downloadFile(file.file_id)
    .then((res) => {
      const url = window.URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = file.filename; // 设置下载的文件名
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    })
    .catch((err) => {
      console.log(err);
      ElMessage.error(`Failed to download ${file.filename}`);
    });
}

function removeResult(file: file) {
  ElMessageBox.confirm("Delete this result ?", "Warning", {
    confirmButtonText: "Confirm",
    cancelButtonText: "Cancel",
    type: "warning",
  }).then(() => {
    deleteFile(file.file_id)
      .then(() => {
        getRepo(currentRepo.id)
          .then((res) => {
            if (res.status == 200) {
              currentRepo.setCurrentRepoInfo(res.data);
            }
          })
          .catch((err) => {
            console.log(err);
            ElMessage.error(`Fail to update info, please refresh manually`);
          });
      })
      .catch((err) => {
        console.log(err);
        ElMessage.error(`Fail to delete file`);
      });
  });
}

function naviToFile(file: file) {
  getFileJsonResult(file.file_id)
    .then((res) => {
      currentFile.setCurrentFileInfo(file, res.data);
      router.push({ path: "/file" }).then(() => {
        router.go(0);
      });
    })
    .catch((err) => {
      console.log(err);
      ElMessage.error(`Fail to get file result`);
    });
}

function naviToChat() {
  router.push({ path: "/chat" }).then(() => {
    router.go(0);
  });
}
</script>

<template>
  <el-main class="main-frame">
    <el-card class="main-card">
      <template #header>
        <div class="header">
          <el-space :size="16">
            <el-icon :size="50" color="#42a5f5">
              <ElementPlus />
            </el-icon>
            <el-space direction="vertical" style="align-items: start">
              <span class="header-title">{{ currentRepo.name }}</span>
              <span class="header-text">{{ currentRepo.desc }}</span>
            </el-space>
          </el-space>

          <el-button-group>
            <el-button type="primary" :icon="Edit" @click="openRepoEditor"
              >Edit</el-button
            >
            <el-button type="success" :icon="ChatSquare" @click="naviToChat"
              >AI</el-button
            >
            <el-button type="danger" plain :icon="Delete" @click="deleteRepo"
              >Delete</el-button
            >
          </el-button-group>
        </div>
      </template>

      <el-dialog v-model="repoEditorVisible" width="500">
        <template #header="{ titleId, titleClass }">
          <div class="dialog-header">
            <el-icon :size="30" color="#42a5f5">
              <Edit />
            </el-icon>
            <span :id="titleId" :class="titleClass">Edit Repository</span>
          </div>
        </template>

        <el-form
          :model="repoEditorForm"
          label-width="auto"
          label-position="left"
        >
          <el-form-item label="Name">
            <el-input v-model="repoEditorForm.name"></el-input>
          </el-form-item>
          <el-form-item label="Description">
            <el-input v-model="repoEditorForm.desc"></el-input>
          </el-form-item>
        </el-form>

        <template #footer>
          <div class="dialog-footer">
            <el-button @click="repoEditorVisible = false">Cancel</el-button>
            <el-button type="primary" @click="editRepo">Confirm</el-button>
          </div>
        </template>
      </el-dialog>

      <el-descriptions title="Overview" border>
        <template #extra>
          <el-button type="primary" :icon="Edit" @click="openCollaboratorAdder"
            >Add Collaborator</el-button
          >
        </template>

        <el-descriptions-item label="File Number">
          {{ currentRepo.files.length }}
        </el-descriptions-item>
        <el-descriptions-item label="Result Number">
          {{ currentRepo.results.length }}
        </el-descriptions-item>
        <el-descriptions-item label="Owner">
          <el-space>
            <el-avatar
              v-if="userStore.profile_picture"
              :src="userStore.profile_picture"
              :size="20"
            />
            <el-icon v-else :size="20">
              <Avatar />
            </el-icon>
            <el-tag type="primary" disable-transitions>{{
              userStore.username
            }}</el-tag>
          </el-space>
        </el-descriptions-item>
        <el-descriptions-item label="Collaborators">
          <el-space>
            <el-space v-for="col in currentRepo.collaborators">
              <!-- TODO: get collaboratiors -->
              <el-avatar
                v-if="userStore.profile_picture"
                :src="userStore.profile_picture"
                :size="20"
              />
              <el-icon v-else :size="20">
                <Avatar />
              </el-icon>
              <el-tag type="success" closable disable-transitions>{{
                col
              }}</el-tag>
            </el-space>
          </el-space>
        </el-descriptions-item>
      </el-descriptions>

      <el-dialog v-model="collaboratorVisible" width="500">
        <template #header="{ titleId, titleClass }">
          <div class="dialog-header">
            <el-icon :size="30" color="#42a5f5">
              <User />
            </el-icon>
            <span :id="titleId" :class="titleClass">Add collaborator</span>
          </div>
        </template>

        <el-input v-model="collaboratorInput" placeholder="Add by ID" />

        <template #footer>
          <div class="dialog-footer">
            <el-button @click="collaboratorVisible = false">Cancel</el-button>
            <el-button type="primary" @click="addCollaborator"
              >Confirm</el-button
            >
          </div>
        </template>
      </el-dialog>

      <el-divider></el-divider>

      <el-space direction="vertical" fill style="width: 100%">
        <el-card shadow="never">
          <template #header>
            <span style="font-weight: bold">File</span>
          </template>

          <el-table
            :data="currentRepo.files"
            style="width: 100%"
            max-height="200"
          >
            <el-table-column
              prop="filename"
              label="Name"
              width="180"
              sortable
              show-overflow-tooltip
            >
              <!-- <template #default="scope">
                <el-button type="primary" link @click="naviToFile(scope.row)">{{ scope.row.filename }}</el-button>
              </template> -->
            </el-table-column>
            <el-table-column 
              prop="size" 
              label="Size" 
              width="180" 
              sortable
              #default="scope"
            >
              {{ formatFileSize(scope.row.size) }}
            </el-table-column>
            <el-table-column
              prop="status"
              label="Status"
              width="180"
              sortable
              #default="scope"
            >
              <el-tag v-if="scope.row.status === 'uploaded'" type="primary"
                >uploaded</el-tag
              >
              <el-tag
                v-else-if="scope.row.status === 'processing'"
                type="warning"
                >analysing</el-tag
              >
              <el-tag v-else-if="scope.row.status === 'error'" type="danger"
                >error</el-tag
              >
              <el-tag v-else-if="typeof scope.row.status === 'number' || !isNaN(Number(scope.row.status))" type="warning">
                {{ Math.round(Number(scope.row.status) * 100) }}%
              </el-tag>
              <el-tag v-else type="success">{{ scope.row.status }}</el-tag>
            </el-table-column>
            <el-table-column fixed="right" align="right">
              <template #header>
                <el-row :gutter="10" style="width: 100%">
                  <el-col :span="20">
                    <el-input v-model="searchInput" placeholder="Search file" />
                  </el-col>
                  <el-col :span="4">
                    <el-button
                      type="primary"
                      :icon="Upload"
                      @click="openUploader"
                      >Upload</el-button
                    >
                  </el-col>
                </el-row>
              </template>
              <template #default="scope">
                <el-button
                  type="primary"
                  :icon="VideoPlay"
                  link
                  size="small"
                  @click="analyseFile(scope.row)"
                  :loading="scope.row.status == 'processing'"
                  >Analyse</el-button
                >
                <el-button
                  type="danger"
                  :icon="Delete"
                  link
                  size="small"
                  @click="removeFile(scope.row)"
                  >Delete</el-button
                >
              </template>
            </el-table-column>
          </el-table>

          <el-dialog v-model="uploadVisible" width="500">
            <template #header="{ titleId, titleClass }">
              <div class="dialog-header">
                <el-icon :size="30" color="#42a5f5">
                  <Upload />
                </el-icon>
                <span :id="titleId" :class="titleClass">Upload</span>
              </div>
            </template>

            <el-upload
              v-model:file-list="uploadFiles"
              multiple
              :auto-upload="false"
            >
              <el-button type="success" :icon="Upload">Select</el-button>
            </el-upload>

            <template #footer>
              <div class="dialog-footer">
                <el-button @click="uploadVisible = false">Cancel</el-button>
                <el-button type="primary" @click="uploadAllFiles"
                  >Submit</el-button
                >
              </div>
            </template>
          </el-dialog>
        </el-card>

        <el-card shadow="never">
          <template #header>
            <span style="font-weight: bold">Result</span>
          </template>

          <el-table
            :data="currentRepo.results"
            style="width: 100%"
            max-height="200"
          >
            <el-table-column
              prop="filename"
              label="Name"
              width="180"
              sortable
              show-overflow-tooltip
            >
              <template #default="scope">
                <el-button type="primary" link @click="naviToFile(scope.row)">{{
                  scope.row.filename
                }}</el-button>
              </template>
            </el-table-column>
            <el-table-column 
              prop="size" 
              label="Size" 
              width="180" 
              sortable
              #default="scope"
            >
              {{ formatFileSize(scope.row.size) }}
            </el-table-column>
            <el-table-column
              prop="status"
              label="Status"
              width="180"
              sortable
              #default="scope"
            >
              <el-tag v-if="scope.row.status === 'uploaded'" type="primary">{{
                scope.row.status
              }}</el-tag>
              <el-tag
                v-else-if="scope.row.status == 'pending'"
                type="warning"
                >{{ scope.row.status }}</el-tag
              >
              <el-tag v-else type="success">{{ scope.row.status }}</el-tag>
            </el-table-column>
            <el-table-column fixed="right" align="right">
              <template #header>
                <el-input v-model="searchInput" placeholder="Search result" />
              </template>
              <template #default="scope">
                <el-button
                  type="primary"
                  :icon="Download"
                  link
                  size="small"
                  @click="downloadResult(scope.row)"
                  >Download</el-button
                >
                <el-button
                  type="danger"
                  :icon="Delete"
                  link
                  size="small"
                  @click="removeResult(scope.row)"
                  >Delete</el-button
                >
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-space>
    </el-card>
  </el-main>
</template>

<style scoped>
.main-frame {
  width: 100%;
  height: 100%;
  display: flex;
  padding: 15px;
  gap: 5px;
  justify-content: center;
  align-items: center;
}

.main-card {
  width: 90%;
  height: 95%;
}

.header-title {
  font-size: 20px;
  font-weight: bold;
  color: #2c2c2c;
}

.header-text {
  font-size: 14px;
  color: #3a3a3a;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: start;
  gap: 20px;
}

.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
