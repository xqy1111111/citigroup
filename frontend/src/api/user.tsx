import { config } from '../config/api';
import { request } from '../utils/request';

export interface loginData {
  username: string;
  email: string;
  password: string;
  profile_picture: string;
}

export interface authResponse {
  user_id: string;
  message: string;
}

export interface userData {
  id: string;
  username: string;
  email: string;
  profile_picture: string;
  repos: string[];
  collaborations: string[];
}

export interface repo {
  id: string;
  name: string;
  desc: string;
  owner_id: string;
  collaborators: string[];
  files: string[];
  results: string[];
}

export interface file {
  file_id: string;
  filename: string;
  size: number;
  upload_date: string;
  status: string;
}

//user的三个api
export async function userLogin(data: loginData): Promise<authResponse> {
  const response = await request.post('/users/authenticate/', {
    username_or_email: data.username,
    password: data.password
  }) as authResponse;
  return response;
}

export async function getUser(userId: string): Promise<userData> {
  const response = await request.get(`/users/${userId}`) as userData;
  return response;
}

export async function userRegister(data: loginData): Promise<userData> {
  const response = await request.post('/users/', data) as userData;
  return response;
}

//repo的api
export async function getRepo(repoId: string): Promise<repo> {
  const response = await request.get(`/repos/${repoId}`) as repo;
  return response;
}

export async function addRepo(owner_id: string, data: { name: string; desc: string }): Promise<repo> {
  console.log(data);
  const response = await request.post(`/repos/?owner_id=${owner_id}`, data) as repo;
  return response;
}

export async function deleteRepo(repoId: string): Promise<void> {
  await request.delete(`/repos/${repoId}`);
}

export async function updateRepoName(repoId: string, data: { new_name: string; new_desc: string }): Promise<void> {
  await request.put(`/repos/${repoId}/name`, data);
}

export async function updateRepoDesc(repoId: string, data: { new_name: string; new_desc: string }): Promise<void> {
  await request.put(`/repos/${repoId}/desc`, data);
}

// file的api
export async function uploadFile(repoId: string, file: File, source: boolean = false): Promise<file> {
  const formData = new FormData();
  formData.append('cur_file', file);
  const response = await request.post(`files/upload?repo_id=${repoId}&source=${source}`, formData) as file;
  return response;
}

export async function getFileMetadata(fileId: string, source: boolean = false): Promise<file> {
  const response = await request.get(`files/${fileId}?source=${source}`) as file;
  return response;
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
export async function downloadFile(fileId: string): Promise<Blob> {
  const response = await request.get(`/files/${fileId}/download`, {
    responseType: 'blob'  // 指定响应类型为blob
  }) as Blob;
  return response;
}

export async function deleteFile(fileId: string): Promise<void> {
  await request.delete(`/files/${fileId}`);
}
