<script setup lang="ts">
import { Delete, Edit, ElementPlus, FolderAdd, Avatar } from '@element-plus/icons-vue';
import { onMounted, reactive, ref } from 'vue';
import SideBar from '../../components/SideBar.vue';
import type { repo } from '../../api/repo';
import { router } from '../../router';
import { useUserStore } from '../../utils/state';
import { useCurrentRepoStore } from '../../utils/state';
import { addRepo as addRepoApi, getRepo, updateRepoName, updateRepoDesc, deleteRepo as deleteRepoApi } from '../../api/repo';
import { ElMessageBox, ElMessage } from 'element-plus';
import 'element-plus/theme-chalk/el-message-box.css'
import { checkAuth } from '../../utils/directives';

const userStore = useUserStore();
const currentRepoStore = useCurrentRepoStore();

const repos = ref([] as repo[]);//暂存的Repo数据

const searchInput = ref('');
const repoAdderVisible = ref(false);
const repoAdderForm = reactive({
  name: '',
  desc: '',
});

const repoEditorVisible = ref(false);
const repoEditorForm = reactive({
  name: '',
  desc: '',
  id: '',
});

onMounted(() => {
  userStore.localStorageUserData();
  currentRepoStore.localStorageCurrentRepoData();
  
  if (!checkAuth()) {
    ElMessage.warning('请先登录后再访问此页面');
    router.push({
      path: '/login',
      query: { redirect: '/dashboard' }
    });
    return;
  }
  
  for (let repoId of userStore.repos) {
    getRepo(repoId).then(response => {
      if (response.status === 200) {
        console.log(response);
        repos.value.push(response.data);
      }
    }).catch(error => {
      console.log(error);
    });
  }
})

function openRepoAdder() {
  repoAdderForm.name = '';
  repoAdderForm.desc = '';
  repoAdderVisible.value = true;
}

function openRepoEditor(name: string, desc: string, id: string) {
  repoEditorForm.name = name;
  repoEditorForm.desc = desc;
  repoEditorForm.id = id;
  repoEditorVisible.value = true;
}

function addRepo() {
  addRepoApi(userStore.id, {
    name: repoAdderForm.name,
    desc: repoAdderForm.desc,
  }).then(response => {
    console.log(response);
    if (response.status === 200) {
      userStore.updateRepos(userStore.repos.concat(response.data.id));
      repos.value.push(response.data);
    }
  }).catch(error => {
    console.log(error);
  });
  repoAdderVisible.value = false;
}

function editRepo() {
  const repo = repos.value.find(repo => repo.id === repoEditorForm.id);
  if (repo) {
    if (repoEditorForm.name !== repo.name) {
      updateRepoName(repoEditorForm.id, {
        new_name: repoEditorForm.name,
        new_desc: repoEditorForm.desc,
      }).catch(error => {
        console.log(error);
      });
    }
    if (repoEditorForm.desc !== repo.desc) {
      updateRepoDesc(repoEditorForm.id, {
        new_name: repoEditorForm.name,
        new_desc: repoEditorForm.desc,
      }).catch(error => {
        console.log(error);
      });
    }
    repo.name = repoEditorForm.name;
    repo.desc = repoEditorForm.desc;
  }
  repoEditorVisible.value = false;
}

function deleteRepo(id: string) {
  ElMessageBox.confirm(
    'Delete this repo ?',
    'Warning',
    {
      confirmButtonText: 'Confirm',
      cancelButtonText: 'Cancel',
      type: 'warning',
    }
  ).then(() => {

    const repo = repos.value.find(repo => repo.id === id);
    if (repo) {
      deleteRepoApi(repo.id).then(response => {
        if (response.status === 200) {
          userStore.updateRepos(userStore.repos.filter(repoId => repoId !== id));
          repos.value = repos.value.filter(repo => repo.id !== id);
        }
      }).catch(error => {
        console.log(error);
      });
    }

  });
}

const selectRepo = (repo: repo) => {
  if (!checkAuth()) {
    ElMessage.warning('请先登录后再访问此页面');
    router.push({
      path: '/login',
      query: { redirect: '/repo' }
    });
    return;
  }
  
  currentRepoStore.setCurrentRepoInfo(repo);
  router.push('/repo');
};
</script>

<template>
  <el-container>
    <SideBar />
    <el-main class="main-frame">
      <el-card class="main-card">
        <template #header>
          <el-space :size="16">
            <el-icon :size="50" color="#42a5f5">
              <ElementPlus />
            </el-icon>
            <span class="header-title">Welcome back, {{ userStore.username }}</span>
          </el-space>
        </template>

        <el-table :data="repos" style="width: 100%" max-height="500">
          <el-table-column prop="name" label="Repository" width="180" sortable show-overflow-tooltip>
            <template #default="scope">
              <el-button type="primary" link @click.prevent="selectRepo(scope.row)">{{ scope.row.name }}</el-button>
            </template>
          </el-table-column>
          <el-table-column prop="owner_id" label="Owner" width="180" sortable>
            <template #default="scope">
              <el-space>
                <el-avatar v-if="scope.row.avatar" :src="scope.row.avatar" size="small" />
                <el-icon v-else size="small">
                  <Avatar />
                </el-icon>
                <el-tag type="primary">{{ scope.row.owner_id }}</el-tag>
              </el-space>
            </template>
          </el-table-column>
          <el-table-column prop="desc" label="Description" show-overflow-tooltip />
          <el-table-column fixed="right" align="right">
            <template #header>
              <el-row :gutter="10" style="width: 100%;">
                <el-col :span="20">
                  <el-input v-model="searchInput" placeholder="Search repository" />
                </el-col>
                <el-col :span="4">
                  <el-button type="primary" :icon="FolderAdd" @click.prevent="openRepoAdder">New</el-button>
                </el-col>
              </el-row>
            </template>
            <template #default="scope">
              <el-button type="primary" :icon="Edit" link size="small"
                @click.prevent="openRepoEditor(scope.row.name, scope.row.desc, scope.row.id)">Edit</el-button>
              <el-button type="danger" :icon="Delete" link size="small"
                @click.prevent="deleteRepo(scope.row.id)">Delete</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-dialog v-model="repoAdderVisible" width="500">
          <template #header="{ titleId, titleClass }">
            <div class="dialog-header">
              <el-icon :size="30" color="#42a5f5">
                <FolderAdd />
              </el-icon>
              <span :id="titleId" :class="titleClass">New Repository</span>
            </div>
          </template>

          <el-form :model="repoAdderForm" label-width="auto" label-position="left">
            <el-form-item label="Name">
              <el-input v-model="repoAdderForm.name"></el-input>
            </el-form-item>
            <el-form-item label="Description">
              <el-input v-model="repoAdderForm.desc"></el-input>
            </el-form-item>
          </el-form>

          <template #footer>
            <div class="dialog-footer">
              <el-button @click.prevent="repoAdderVisible = false">Cancel</el-button>
              <el-button type="primary" @click.prevent="addRepo">Confirm</el-button>
            </div>
          </template>
        </el-dialog>

        <el-dialog v-model="repoEditorVisible" width="500">
          <template #header="{ titleId, titleClass }">
            <div class="dialog-header">
              <el-icon :size="30" color="#42a5f5">
                <Edit />
              </el-icon>
              <span :id="titleId" :class="titleClass">Edit Repository</span>
            </div>
          </template>

          <el-form :model="repoEditorForm" label-width="auto" label-position="left">
            <el-form-item label="Name">
              <el-input v-model="repoEditorForm.name"></el-input>
            </el-form-item>
            <el-form-item label="Description">
              <el-input v-model="repoEditorForm.desc"></el-input>
            </el-form-item>
          </el-form>

          <template #footer>
            <div class="dialog-footer">
              <el-button @click.prevent="repoEditorVisible = false">Cancel</el-button>
              <el-button type="primary" @click.prevent="editRepo">Confirm</el-button>
            </div>
          </template>
        </el-dialog>

      </el-card>
    </el-main>
  </el-container>
</template>

<style scoped>
.main-frame {
  width: 100%;
  height: calc(100vh - 30px);
  display: flex;
  padding: 15px;
  gap: 5px;
  justify-content: center;
  align-items: center;
}

.main-card {
  width: 90%;
  height: 90%;
}

.header-title {
  font-size: 20px;
  font-weight: bold;
  color: #2c2c2c;
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