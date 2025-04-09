import { request } from "../utils/request";
export interface chatHistory {
    "user_id": string,
    "repo_id": string,
    "texts": {
        "question": chat,
        "answer": chat
    }[]
}

export interface chat {
    "sayer": string, //"assistant"
    "text": string,
    "timestamp": string
}

export const getChatHistory = (userID: string, repoId: string) => {
    return request.get(`/chat/?user_id=${userID}&repo_id=${repoId}`).then(response => {
        return response;
    });
}


export const getChat = (userID: string, repoId: string, message: string) => {
    return request.post(`/chat/${userID}/${repoId}?message=${message}`).then(response => {
        return response;
    });
}

export const getChatWithFile = (userID: string, repoId: string, message: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    return request.post(
        `/chat/${userID}/${repoId}/with-file?message=${encodeURIComponent(message)}`,
        formData,
        {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        }
    ).then(response => {
        return response;
    });
}

export const getChatWithFileID =(userID: string, repoId: string, message: string, fileID: string) => {
    return request.post(`/chat/${userID}/${repoId}/file?file_id=${fileID}&message=${message}`,null ,{timeout:120000}).then(response => { //120s都有超时的可能,emm
        return response;
    });
}

export const getChatWithMultipleFileID =(userID: string, repoId: string, message: string, fileIDs: string[]) => {
    return request.post(`/chat/${userID}/${repoId}/multiple_files?message=${message}`,fileIDs ,{timeout:300000}).then(response => { 
        return response;
    });
}