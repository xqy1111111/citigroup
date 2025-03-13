import { request } from '../utils/request';

export const processFile = (repoId: string, fileId: string) => {
    return request.post<void>(`/process/${fileId}/multiprocess?repo_id=${repoId}`).then(response => {
        return response;
    });
}
