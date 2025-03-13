import axios from "axios";
import {router} from "../router";
import {useUserStore} from "./state.ts";

export const request = axios.create();

request.interceptors.request.use(
    config => {
        console.log("1112");
    return config;
}, error => {
    console.log(error);
    return Promise.reject(error);
});

const userStore = useUserStore();


request.interceptors.response.use(response => {
    console.log("111");
    if (!userStore.isLoggedIn) {
        router.push("/login");
    }
    return response;
}, error => {
    if(error.response.status === 401||error.response.status === 400) {
        router.push("/login");
    }
    console.log(error);
    return Promise.reject(error);
});


