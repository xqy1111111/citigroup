import React, { useState } from 'react';
import Modal from './Modal';
import { repo } from '../../../api/user.tsx';

interface SettingsModalProps {
    repo: repo;
    onSave: (repo: repo) => void;
    onDelete: (id: string) => void;
    onClose: (repo: repo) => void;
}

function SettingsModal({ repo, onSave, onDelete, onClose }: SettingsModalProps) {
    const [editedRepo, setEditedRepo] = useState<repo>({
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