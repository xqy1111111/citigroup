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

export const userLogin = (data: loginData) => {
    return request.post('/users/authenticate/', {
        username_or_email: data.username || data.email,
        password: data.password
    }).then(response => {
        return response;
    });
}

export const getUser = (userId: string) => {
    return request.get(`/users/${userId}`).then(response => {
        return response;
    });
}

export const userRegister = (data: loginData) => {
    return request.post('/users/', data).then(response => {
        return response;
    });
}