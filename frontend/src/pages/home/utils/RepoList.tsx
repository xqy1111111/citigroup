import React from 'react';

interface Repo {
    id: string;
    name: string;
    desc: string;
    owner_id: string;
    collaborators: string[];
    files: string[];
    results: string[];
}

interface RepoListProps {
    repos: Repo[];
    onOpenSettings: (repo: Repo) => void;
    onEnterRepo?: (repo: Repo) => void;
}

function RepoList({ repos, onOpenSettings, onEnterRepo }: RepoListProps) {
    return (
        <div className="repo-list">
            {repos.map(repo => (
                <div key={repo.id} className="repo-item">
                    <div className="repo-content">
                        <h2>{repo.name}</h2>
                        <p>{repo.desc}</p>
                    </div>
                    <div className="repo-actions">
                        <button
                            className="settings-button"
                            onClick={() => onOpenSettings(repo)}
                        >
                            设置
                        </button>
                        <button
                            className="enter-button"
                            onClick={() => onEnterRepo && onEnterRepo(repo)}
                        >
                            进入
                        </button>
                    </div>
                </div>
            ))}
        </div>
    );
}

export default RepoList; 