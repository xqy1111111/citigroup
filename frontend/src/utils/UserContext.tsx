import React, { createContext, useState, useContext } from 'react';
import { userData,getUser, repo, addRepo as addRepoAPI, deleteRepo as deleteRepoAPI, updateRepoName, updateRepoDesc, getRepo} from '../api/user.tsx';


interface UserContextType {
    user: userData;
    repos: repo[];
    updateUser: (updates: userData) => Promise<void>;
    addRepo: (repo: { name: string; desc: string }) => Promise<repo>;
    deleteRepo: (repoId: string) => Promise<void>;
    updateRepo: (repoId: string, updates: { name: string; desc: string }) => Promise<void>;
    resetUser: () => void;
}

const defaultUserState: userData = {
    id: "",
    username: "",
    email: "",
    profile_picture: "",
    repos: [],
    collaborations: []
};

const defaultRepo:repo = {
    id: "",
    name: "",
    desc: "",
    owner_id: "",
    collaborators: [],
    files: [],
    results: []
};

const defaultReposList: repo[] = [];

const UserContext = createContext<UserContextType>({
    user: defaultUserState,
    repos: defaultReposList,
    updateUser: async () => {},
    addRepo: async () => ({ 
        id: "",
        name: "",
        desc: "",
        owner_id: "",
        collaborators: [],
        files: [],
        results: []
    }),
    deleteRepo: async () => {},
    updateRepo: async () => {},
    resetUser: () => {}
});

export function UserProvider({ children }: { children: React.ReactNode }) {
    const [userState, setUserState] = useState<userData>(defaultUserState);
    const [reposState, setreposState] = useState<repo[]>(defaultReposList);

    const updateUser = async (updates: userData) => {
        console.log('Received updates:', updates);
        try {
            if (updates.repos && updates.repos.length > 0) {
                let detailedRepos: repo[] = await Promise.all(
                    updates.repos.map(async (repoID) => {
                        try {
                            const repoDetail:repo = await getRepo(repoID);
                            return repoDetail;
                        } catch (error) {
                            console.error(`获取仓库 ${repoID} 详细信息失败:`, error);
                            return defaultRepo;
                        }
                    })
                );
                detailedRepos = detailedRepos.filter(repo => repo.id !== "");
                // 一起更新两个状态
                await Promise.all([
                    setUserState(updates),
                    setreposState(detailedRepos)
                ]);
            } else {
                setUserState(updates);
            }
        } catch (error) {
            console.error('更新用户信息失败:', error);
            throw error;
        }
    };

    const addRepo = async (repo: { name: string; desc: string }): Promise<repo> => {
        try {
            const response:repo = await addRepoAPI(userState.id, {
                name: repo.name,
                desc: repo.desc,
            });

            const newRepo = response;
            console.log(newRepo);
            await Promise.all([
                    setreposState(prev => [...prev, newRepo])
                ]);
            return newRepo;
        } catch (error) {
            console.error('添加仓库失败:', error);
            throw error;
        }
    };

    const deleteRepo = async (repoId: string): Promise<void> => {
        try {
            await deleteRepoAPI(repoId);
            setUserState(prev => ({
                ...prev,
                repos: prev.repos.filter(repo => repo !== repoId)
            }));
            setreposState(prev => prev.filter(repo => repo.id !== repoId));
        } catch (error) {
            console.error('删除仓库失败:', error);
            throw error;
        }
    };

    const updateRepo = async (repoId: string, updates: { name: string; desc: string }): Promise<void> => {
        try {
            if (updates.name !== reposState.find(repo => repo.id === repoId)?.name) {
                await updateRepoName(repoId, {
                    new_name: updates.name,
                    new_desc: updates.desc
                });
            }
            
            if (updates.desc !== reposState.find(repo => repo.id === repoId)?.desc) {
                await updateRepoDesc(repoId, {
                    new_name: updates.name,
                    new_desc: updates.desc
                });
            }

            const response:repo = await getRepo(repoId);
            const updatedRepo = response;

            setreposState(prev => prev.map(repo =>
                repo.id === repoId ? updatedRepo : repo
            ));
        } catch (error) {
            console.error('更新仓库失败:', error);
            throw error;
        }
    };

    const resetUser = () => {
        setUserState(defaultUserState);
        setreposState(defaultReposList);
    };

    //这里就是对外的接口列表
    const value: UserContextType = {
        user: userState,
        repos: reposState,
        updateUser,
        addRepo,
        deleteRepo,
        updateRepo,
        resetUser
    };

    return (
        <UserContext.Provider value={value}>
            {children}
        </UserContext.Provider>
    );
}

export function useUser(): UserContextType {
    const context = useContext(UserContext);
    return context;
} 