import React, { useState } from 'react';
import RepoList from './utils/RepoList.tsx';
import SettingsModal from './utils/SettingsModal.tsx';
import AddRepoModal from './utils/AddRepoModal.tsx';
import { MenuBar } from '../../components/MenuBar/MenuBar';
import { NavigationBar } from "../../components/NavigationBar/NavigationBar";
import { Sidebar } from "../../components/Sidebar/Sidebar";
import { useUser } from '../../utils/UserContext.tsx';
import { repo } from '../../api/user.tsx';
import "../reset.css";
import "./Home.css";
import { useNavigate } from 'react-router-dom';

interface SettingModalState {
    visible: boolean;
    repo: repo;
}


function Home() {
    const navigate = useNavigate();
    const { user, repos, addRepo, deleteRepo, updateRepo, setCurrentRepo } = useUser();
    const [settingModal, setSettingModal] = useState<SettingModalState>({
        visible: false,
        repo: {
            id: "",
            name: "",
            desc: "",
            owner_id: "",
            collaborators: [],
            files: [],
            results: []
        }
    });
    const [addModal, setAddModal] = useState(false);

    const isModalOpen = settingModal.visible || addModal;

    const handleAddRepo = (newRepo: { name: string; desc: string }) => {
        addRepo(newRepo);
        setAddModal(false);
    };

    // 处理编辑仓库
    const handleEditRepo = (editedRepo: repo) => {
        // 更新本地状态
        const updatedRepo = repos.find(repo => repo.id === editedRepo.id);
        if (updatedRepo) {
            updateRepo(editedRepo.id, {
                name: editedRepo.name,
                desc: editedRepo.desc
            });
        }
    };

    // 处理保存仓库编辑
    const handleEditOnclose = async (editedRepo: repo) => {
        try {
            await updateRepo(editedRepo.id, {
                name: editedRepo.name,
                desc: editedRepo.desc
            });
            setSettingModal({
                visible: false,
                repo: {
                    id: "",
                    name: "",
                    desc: "",
                    owner_id: "",
                    collaborators: [],
                    files: [],
                    results: []
                }
            });
        } catch (error) {
            console.error('保存仓库失败:', error);
        }
    };

    // 处理删除仓库
    const handleDeleteRepo = (repoId: string) => {
        deleteRepo(repoId);
        setSettingModal({
            visible: false,
            repo: {
                id: "",
                name: "",
                desc: "",
                owner_id: "",
                collaborators: [],
                files: [],
                results: []
            }
        });
    };

    // 打开设置弹窗
    const openSettings = (repo: repo) => {
        setSettingModal({ visible: true, repo });
    };

    // 处理进入仓库
    const handleEnterRepo = (repo: repo) => {
        //todo: 进入仓库(设置当前仓库)
        setCurrentRepo(repo);
        navigate(`/repo/${repo.id}`);
        console.log('进入仓库:', repo.name);
    };

    return (
        <>
            <div className={`Container ${isModalOpen ? 'modal-open' : ''}`}>
                <MenuBar />
                <div className="main-content">
                    <NavigationBar />
                    <Sidebar />
                    <div className="content">
                        <div className="Main">
                            {user.id ? (
                                <div className="Main-Repo">
                                    <h1 className="Main-Repo-Title">仓库列表</h1>
                                    <RepoList
                                        repos={repos as repo[]}
                                        onOpenSettings={openSettings}
                                        onEnterRepo={handleEnterRepo}
                                    />

                                    <button
                                        className="add-repo-button"
                                        onClick={() => setAddModal(true)}
                                    >
                                        + 添加新仓库
                                    </button>

                                    {settingModal.visible && (
                                        <SettingsModal
                                            repo={settingModal.repo}
                                            onSave={handleEditRepo}
                                            onDelete={handleDeleteRepo}
                                            onClose={handleEditOnclose}
                                        />
                                    )}

                                    {addModal && (
                                        <AddRepoModal
                                            onAdd={handleAddRepo}
                                            onClose={() => setAddModal(false)}
                                        />
                                    )}
                                </div>
                            ) : (
                                <div className="login-prompt">
                                    <h2>请先登录</h2>
                                    <p>登录后即可查看和管理您的仓库</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}

export default Home; 