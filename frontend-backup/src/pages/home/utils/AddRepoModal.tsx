import React, { useState } from 'react';
import Modal from './Modal';

interface AddRepoModalProps {
    onAdd: (repo: { name: string; desc: string }) => void;
    onClose: () => void;
}

interface NewRepo {
    name: string;
    desc: string;
}

function AddRepoModal({ onAdd, onClose }: AddRepoModalProps) {
    const [newRepo, setNewRepo] = useState<NewRepo>({
        name: "",
        desc: ""
    });

    const handleSubmit = () => {
        if (!newRepo.name.trim()) return;
        onAdd(newRepo);
        setNewRepo({ name: "", desc: "" });
    };

    return (
        <Modal>
            <h2>添加新仓库</h2>
            <input
                type="text"
                value={newRepo.name}
                onChange={(e) => setNewRepo(prev => ({ ...prev, name: e.target.value }))}
                placeholder="仓库名称"
            />
            <input
                type="text"
                value={newRepo.desc}
                onChange={(e) => setNewRepo(prev => ({ ...prev, desc: e.target.value }))}
                placeholder="仓库描述"
            />
            <div className="modal-actions">
                <button onClick={handleSubmit}>创建</button>
                <button onClick={onClose}>取消</button>
            </div>
        </Modal>
    );
}

export default AddRepoModal; 