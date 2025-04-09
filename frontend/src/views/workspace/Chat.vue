<script setup lang="ts">
import { Promotion } from '@element-plus/icons-vue';
import { onMounted, ref } from 'vue';
import MarkdownIt from 'markdown-it';
import { getChatHistory, type chat, getChat, getChatWithMultipleFileID } from '../../api/chat';
import { useUserStore, useCurrentRepoStore, useChatHistoryStore } from '../../utils/state';

const userStore = useUserStore()
const currentRepo = useCurrentRepoStore()
const userChatHistory = useChatHistoryStore()

const chatMessages = ref<chat[]>([]);
const chatContainer = ref<HTMLElement | null>(null);
const inputDisabled = ref(false);

onMounted(() => {
  userStore.localStorageUserData();
  currentRepo.localStorageCurrentRepoData();
  userChatHistory.localStorageChatHistory();
  console.log(currentRepo.files);
  getChatHistory(userStore.id, currentRepo.id).then(response => { //转换聊天记录格式
    if (response.status === 200) {
      userChatHistory.setChatHistory(response.data);
      chatMessages.value = userChatHistory.texts.flatMap((text: {
        "question": chat,
        "answer": chat
      }) => [
          { text: text.question.text, sayer: text.question.sayer, timestamp: text.question.timestamp },
          { text: text.answer.text, sayer: text.answer.sayer, timestamp: text.answer.timestamp },
        ]);
    }
  })
});


const md = new MarkdownIt({
  html: true,
  breaks: true,
  linkify: true
});

const input = ref('');
const inputFile = ref<string[]>([]);

const renderMarkdown = (content: string) => {
  console.log(content);
  return md.render(content);
};

function scrollToBottom() {
  setTimeout(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }
  }, 100); // 给一个小延迟确保DOM已更新
}

function sendMessage() {
  inputDisabled.value = true;
  if (input.value === '') {
    inputDisabled.value = false;
    return;
  }
  const userMessage = { text: input.value, sayer: 'user', timestamp: new Date().toLocaleString() };
  const loadingMessage = {
    text: "让我思考一下..." + (inputFile.value.length > 0 ? "每个文件预计用时1分钟,请耐心等待..." : ""),
    sayer: 'assistant',
    timestamp: new Date().toLocaleString()
  };
  chatMessages.value.push(userMessage);
  chatMessages.value.push(loadingMessage);
  scrollToBottom();

  if (inputFile.value.length > 0) {
    console.log(inputFile.value);
    getChatWithMultipleFileID(userStore.id, currentRepo.id, input.value, inputFile.value).then(response => {
      if (response.status === 200) {
        chatMessages.value.pop();
        chatMessages.value.push(response.data);
      }
    }).catch(error => {
      chatMessages.value[chatMessages.value.length - 1].text = "超时了...请尝试重新发送";
      console.error(error);
    }).finally(() => {
      inputDisabled.value = false;
    })
  } else {
    getChat(userStore.id, currentRepo.id, input.value).then(response => {
      if (response.status === 200) {
        chatMessages.value.pop();
        chatMessages.value.push(response.data);
      }
    }).catch(error => {
      chatMessages.value[chatMessages.value.length - 1].text = "超时了...请尝试重新发送";
      console.error(error);
    }).finally(() => {
      inputDisabled.value = false;
    })
  }
  input.value = '';
  inputFile.value = [];
}

</script>

<template>
  <el-main class="main-frame">
    <!-- 聊天记录区域 -->
    <div class="chat-container" ref="chatContainer">
      <div class="chat-messages" v-if="chatMessages.length > 0">
        <div v-for="message in chatMessages" :key="message.timestamp"
          :class="['message-wrapper', { 'message-right': message.sayer === 'user' }]">
          <el-space :size="12" :alignment="message.sayer === 'assistant' ? 'start' : 'end'" direction="horizontal">
            <template v-if="message.sayer === 'user'">
              <el-card shadow="hover" class="message-card user-message">
                <div class="message-text markdown-body" v-html="renderMarkdown(message.text)"></div>
                <div class="message-time">{{ message.timestamp }}</div>
              </el-card>
            </template>
            <template v-else>
              <el-card shadow="hover" class="message-card ai-message">
                <div class="message-text markdown-body" v-html="renderMarkdown(message.text)"></div>
                <div class="message-time">{{ message.timestamp }}</div>
              </el-card>
            </template>
          </el-space>
        </div>
      </div>

      <span v-else class="prompt">
        What can I help you?
      </span>
    </div>

    <el-affix position="bottom" style="width: 80%;">
      <el-card>
        <template #header>
          <el-select v-model="inputFile" placeholder="Files to ask" multiple clearable tag-type="primary" placement="top-start"
            style="width: 96%;">
            <el-option v-for="file in currentRepo.results" :key="file.file_id" :label="file.filename"
              :value="file.file_id">
            </el-option>
          </el-select>
        </template>

        <div class="input-section">
          <el-input v-model="input" placeholder="Type to ask" :rows="4" type="textarea" resize="none">
          </el-input>
          <el-button type="primary" :icon="Promotion" circle @click.prevent="sendMessage" @keyup.enter="sendMessage"></el-button>
        </div>
      </el-card>
    </el-affix>

  </el-main>
</template>

<style scoped>
.main-frame {
  width: 100%;
  height: calc(100vh - 30px);
  display: flex;
  flex-direction: column;
  padding: 15px;
  gap: 15px;
  justify-content: start;
  align-items: center;
}

.chat-container {
  width: 80%;
  height: 80%;
  padding: 15px;
  position: relative;
  overflow-y: auto;
  overflow-x: hidden;
}

.chat-container::-webkit-scrollbar {
  width: 8px;
}

.chat-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.chat-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.chat-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.chat-messages {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 10px;
}

.prompt {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  color: #2c2c2c;
  font-size: x-large;
  font-weight: bold;
  white-space: nowrap;
}

.input-section {
  width: 100%;
  display: flex;
  gap: 20px;
  justify-content: space-between;
  align-items: flex-end;
}

/* 聊天记录样式 */
.message-wrapper {
  width: 100%;
  display: flex;
}

.message-right {
  justify-content: flex-end;
}

.message-card {
  width: 100%;
  padding: 20px;
  flex-grow: 1;
}

.message-card :deep(.el-card__body) {
  padding: 12px;
}

.ai-message {
  background-color: var(--el-color-primary-light-9);
}

.user-message {
  background-color: var(--el-color-success-light-9);
}

.message-text {
  color: var(--el-text-color-primary);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  text-align: right;
}

/* 输入框样式优化 */
:deep(.el-textarea__inner) {
  min-height: 60px !important;
  resize: none;
}

/* Markdown 样式 */
.markdown-body :deep(p) {
  margin: 0;
  line-height: 1.6;
}

.markdown-body :deep(pre) {
  background-color: var(--el-fill-color-darker);
  padding: 12px;
  border-radius: 4px;
  margin: 8px 0;
  overflow-x: auto;
}

.markdown-body :deep(code) {
  font-family: Monaco, Consolas, Courier New, monospace;
  background-color: var(--el-fill-color-dark);
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 0.9em;
}

.markdown-body :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}

.markdown-body :deep(blockquote) {
  margin: 8px 0;
  padding-left: 1em;
  border-left: 4px solid var(--el-border-color);
  color: var(--el-text-color-secondary);
}

.markdown-body :deep(a) {
  color: var(--el-color-primary);
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  width: 100%;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid var(--el-border-color);
  padding: 6px 12px;
}

.markdown-body :deep(th) {
  background-color: var(--el-fill-color-light);
}
</style>