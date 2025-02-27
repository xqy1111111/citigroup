import React from "react";
import { useUser } from "../../utils/UserContext";
import { useNavigate } from "react-router-dom";
import "./Sidebar.css";
import "../../styles/icons.css";

export function Sidebar() {
  const { currentRepo, repos, setCurrentRepo } = useUser();
  const navigate = useNavigate();

  const handleRepoClick = (repo) => {
    if (repo.id !== currentRepo.id) { // 只在点击不同的仓库时更新
      setCurrentRepo(repo);
      navigate(`/repo/${repo.id}`);
    }
  };

  return (
    <div className="sidebar">
      <div className="current-repo">
        <h3>当前仓库: {currentRepo.id ? currentRepo.name : "无"}</h3>
        {currentRepo.files.length > 0 ? (
          <div className="file-list">
            {currentRepo.files.map(file => (
              <div 
                key={file.file_id} 
                className="sidebar-repo-item" 
                onClick={() => navigate(`/info/${file.file_id}`)}
              >
                {file.filename}
              </div>
            ))}
          </div>
        ) : (
          <div className="no-files">该仓库没有文件</div>
        )}
      </div>

      <div className="history-repo">
        <h3>历史仓库</h3>
        {repos.filter(repo => repo.id !== currentRepo.id).length > 0 ? (
          repos.filter(repo => repo.id !== currentRepo.id).map(repo => (
            <div key={repo.id} className="sidebar-repo-item" onClick={() => handleRepoClick(repo)}>
              {repo.name}
            </div>
          ))
        ) : (
          <div className="no-history">没有历史仓库</div>
        )}
      </div>

    </div>
  );
} 