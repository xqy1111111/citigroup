import React, { useState } from 'react';
import Modal from './Modal';

interface Repo {
    id: string;
    name: string;
    desc: string;
    owner_id: string;
    collaborators: string[];
    files: string[];
    results: string[];
}

interface SettingsModalProps {
    repo: Repo;
    onSave: (repo: Repo) => void;
    onDelete: (id: string) => void;
    onClose: (repo: Repo) => void;
}

function SettingsModal({ repo, onSave, onDelete, onClose }: SettingsModalProps) {
    const [editedRepo, setEditedRepo] = useState<Repo>({
        ...repo,
        name: repo.name || '',
        desc: repo.desc || ''
    });

    const handleChange = (field: 'name' | 'desc', value: string) => {
        setEditedRepo(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const handleSave = () => {
        onClose(editedRepo);
    };

    return (
        <Modal>
            <h2>仓库设置</h2>
            <input
                type="text"
                value={editedRepo.name}
                onChange={(e) => handleChange('name', e.target.value)}
                placeholder="仓库名称"
            />
            <input
                type="text"
                value={editedRepo.desc}
                onChange={(e) => handleChange('desc', e.target.value)}
                placeholder="仓库描述"
            />
            <div className="modal-actions">
                <button
                    className="delete-button"
                    onClick={() => onDelete(repo.id)}
                >
                    删除仓库
                </button>
                <button onClick={handleSave}>保存</button>
            </div>
        </Modal>
    );
}

export default SettingsModal; 