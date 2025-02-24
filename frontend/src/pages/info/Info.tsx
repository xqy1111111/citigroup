import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { MenuBar } from "../../components/MenuBar/MenuBar";
import { NavigationBar } from "../../components/NavigationBar/NavigationBar";
import { Sidebar } from "../../components/Sidebar/Sidebar";
import { request } from "../../utils/request";
import { config } from "../../config/api";
import "./Info.css";

interface InfoItem {
  key: string;
  value: string;
}

interface InfoSection {
  title: string;
  items: InfoItem[];
}

// 辅助函数：判断是否为多行内容
const isMultiLine = (value: string) => value.includes('\n');

export function Info() {
  const { fileId } = useParams<{ fileId: string }>();
  const [sections, setSections] = useState<InfoSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!fileId) {
        setError("未找到文件ID");
        setLoading(false);
        return;
      }

      try {
        const response = await request(`/process/${fileId}/process`, {
          method: 'POST',
        });

        // 假设后端返回的数据结构与我们需要的格式相同
        // 如果不同，需要在这里进行数据转换
        setSections(response.data);
        setLoading(false);
      } catch (err) {
        setError("获取数据失败");
        setLoading(false);
        console.error("Error fetching data:", err);
      }
    };

    fetchData();
  }, [fileId]);

  if (loading) {
    return (
      <div className="container">
        <MenuBar />
        <div className="main-content">
          <NavigationBar />
          <Sidebar />
          <div className="content">
            <div className="loading">加载中...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <MenuBar />
        <div className="main-content">
          <NavigationBar />
          <Sidebar />
          <div className="content">
            <div className="error">{error}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <MenuBar />
      <div className="main-content">
        <NavigationBar />
        <Sidebar />
        <div className="content">
          <div className="content-header">
            <h1>交易详情</h1>
          </div>

          <div className="info-container">
            {sections.map((section, index) => (
              <div key={index} className="info-section">
                <div className="info-section-header">
                  <h3>{section.title}</h3>
                </div>
                <div className="info-section-content">
                  {section.items.map((item, itemIndex) => (
                    <div key={itemIndex} className="info-item">
                      <div className="info-key">{item.key}</div>
                      <div className="info-value">
                        {isMultiLine(item.value) ? (
                          <div className="tree-view">
                            {item.value.split('\n').map((line, lineIndex) => (
                              <div key={lineIndex} className="tree-item">
                                {line}
                              </div>
                            ))}
                          </div>
                        ) : (
                          item.value
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
} 