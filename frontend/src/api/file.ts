import { request } from "../utils/request";

export interface file {
  file_id: string;
  filename: string;
  size: number;
  uploaded_at: string;
  status: string;
}

export const uploadFile = (repoId: string, file: File, source: boolean = false) => {
  console.log(file);
  const formData = new FormData();
  formData.append('cur_file', file);
  return request.post(`files/upload?repo_id=${repoId}&source=${source}`, formData, {
    'headers': { 'Content-Type': 'multipart/form-data' }
  }).then(response => {
    return response;
  });
}

export const getFileMetadata = (repoId: string, fileId: string, source: boolean = false) => {
  return request.get<file>(`files/${fileId}?repo_id=${repoId}&source=${source}`).then(response => {
    return response;
  });
}

// 下载文件的函数
// 使用示例：
// const blob = await downloadFile(fileId);
// const url = window.URL.createObjectURL(blob);
// const a = document.createElement('a');
// a.href = url;
// a.download = filename; // 设置下载的文件名
// document.body.appendChild(a);
// a.click();
// window.URL.revokeObjectURL(url);
// document.body.removeChild(a);
export const downloadFile = (fileId: string) => {
  return request.get<Blob>(`/files/${fileId}/download`, {
    responseType: 'blob'  // 指定响应类型为blob
  }).then(response => {
    return response;
  });
}

export const deleteFile = (fileId: string) => {
  return request.delete<void>(`/files/${fileId}`).then(response => {
    return response;
  });
}

export const getFileJsonResult = (fileId: string) => {
  return request.get(`/files/json_res/${fileId}`).then(response => {
    return response;
  });
}
