import { request } from '../utils/request';
import type { file } from './file';

export interface repo {
    id: string;
    name: string;
    desc: string;
    owner_id: string;
    collaborators: string[];
    files: file[];//definition in ./file.ts
    results: result[];
}

export interface result {
    source_file: boolean;
    file_id: string;
    filename: string;
    size: number;
    uploaded_at: string;
    status: string;
}

export const getRepo = (repoId: string) => {
    console.log("getRepo", repoId);
    return request.get(`/repos/${repoId}`).then(response => {
        return response;
    });
}

export const addRepo = (owner_id: string, data: { name: string; desc: string }) => {
    return request.post(`/repos/?owner_id=${owner_id}`, data).then(response => {
        return response;
    });
}

export const deleteRepo = (repoId: string) => {
    return request.delete(`/repos/${repoId}`).then(response => {
        return response;
    });
}

export const updateRepoName = (repoId: string, data: { new_name: string; new_desc: string }) => {
    return request.put(`/repos/${repoId}/name`, data).then(response => {
        return response;
    });
}

export const updateRepoDesc = (repoId: string, data: { new_name: string; new_desc: string }) => {
    return request.put(`/repos/${repoId}/desc`, data).then(response => {
        return response;
    });
}

export const updateRepoCollaborators = (repoId: string, data: { collaborator_id: string }) => {
    return request.post(`/repos/${repoId}/collaborators`, data).then(response => {
        return response;
    });
}


