import React, { useEffect, useCallback, useState } from "react";
import { useParams } from "react-router-dom";
import { MenuBar } from "../../components/MenuBar/MenuBar";
import { NavigationBar } from "../../components/NavigationBar/NavigationBar";
import { Sidebar } from "../../components/Sidebar/Sidebar";
import { useUser } from "../../utils/UserContext";
import { getUser, userData, downloadFile, uploadFile, getRepo, processFile } from "../../api/user";
import "./General.css";

export function General() {
  const { repoId } = useParams<{ repoId: string }>();
  const { currentRepo, setCurrentRepo } = useUser();
  const [owner, setOwner] = useState<string>('');
  const [loaded, setLoaded] = useState(false);

  const handleDownload = useCallback((fileId: string) => {
    downloadFile(fileId)
      .then((response) => {
        const url = window.URL.createObjectURL(response);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `file_${fileId}.xlsx`);
        document.body.appendChild(link);
        link.click();
        link.remove();
      })
      .catch((error) => {
        console.error("下载文件时出错:", error);
      });
  }, []);

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    console.log(file);
    if (file) {
      uploadFile(repoId!, file, true)
        .then((response) => {
          console.log("文件上传成功:", response);
          getRepo(repoId!).then((response) => {
            setCurrentRepo(response);
          });
        })
        .catch((error) => {
          console.error("上传文件时出错:", error);
        });
    }
  }, []);

  const handleProcessFile = useCallback((fileId: string) => {
    processFile(repoId!, fileId)
      .then((response) => {
        console.log("文件处理成功:", response);
        getRepo(repoId!).then((response) => {
          setCurrentRepo(response);
        });
      })
      .catch((error) => {
        console.error("处理文件时出错:", error);
      });
  }, []);

  useEffect(() => {
    const fetchOwner = async () => {
      const owner = await getUser(currentRepo.owner_id);
      setOwner(owner.username);
      setLoaded(true);
    };
    fetchOwner();
  }, [loaded]);
  
  if (!loaded) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container">
      <MenuBar />
      <div className="main-content">
        <NavigationBar />
        <Sidebar />
        <div className="content">
          <div className="stats-container">
            <div className="stat-card">
              <div className="stat-title">项目名称</div>
              <div className="stat-value">{currentRepo.name}</div>
              <div className="stat-desc">所有者: {owner}</div>
            </div>
            <div className="stat-card">
              <div className="stat-title">项目描述</div>
              <div className="stat-value-desc">{currentRepo.desc}</div>
              <div className="stat-desc">创建时间: {new Date().toLocaleDateString()}</div>
            </div>
            <div className="stat-card">
              <div className="stat-title">文件数量</div>
              <div className="stat-value">{currentRepo.files.length}</div>
              <div className="stat-desc">上传文件</div>
            </div>
            <div className="stat-card">
              <div className="stat-title">结果数量</div>
              <div className="stat-value">{currentRepo.results.length}</div>
              <div className="stat-desc">生成结果</div>
            </div>
          </div>

          <div className="data-container">
            <div className="data-card">
              <div className="data-header">
                <h3 style={{ flex: 1 }}>文件列表</h3>
                <input 
                  type="file" 
                  onChange={handleFileUpload} 
                  style={{ display: 'none' }} 
                  id="file-upload" 
                />
                <label htmlFor="file-upload" className="upload-button">
                  上传文件
                </label>
              </div>
              <div className="data-content">
                <table>
                  <thead>
                    <tr>
                      <th>文件名</th>
                      <th>大小</th>
                      <th>上传时间</th>
                      <th>状态</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentRepo.files.map((file) => (
                      <tr key={file.file_id}>
                        <td>{file.filename}</td>
                        <td>{(file.size / 1024).toFixed(2)} KB</td>
                        <td>{new Date(file.uploaded_at).toLocaleString()}</td>
                        <td>
                          <div className="status-badge processing">
                            {(parseFloat(file.status) * 100).toFixed(1)}%
                          </div>
                        </td>
                        <td>
                          <button 
                            onClick={() => handleProcessFile(file.file_id)}
                            className="process-button"
                          >
                            处理
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="data-card">
              <div className="data-header">
                <h3>结果列表</h3>
              </div>
              <div className="data-content">
                <table>
                  <thead>
                    <tr>
                      <th>文件名</th>
                      <th>大小</th>
                      <th>生成时间</th>
                      <th>状态</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentRepo.results.map((result) => (
                      <tr key={result.file_id}>
                        <td>{result.filename}</td>
                        <td>{(result.size / 1024).toFixed(2)} KB</td>
                        <td>{new Date(result.uploaded_at).toLocaleString()}</td>
                        <td>
                          <div className="status-badge completed">
                            {result.status}
                          </div>
                        </td>
                        <td>
                          <button 
                            onClick={() => handleDownload(result.file_id)}
                            className="download-button"
                          >
                            下载
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
