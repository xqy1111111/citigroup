import "../reset.css";
import "./Chat.css";
import React from "react";
import { useState, useRef, useEffect } from "react";
import { MenuBar } from "../../components/MenuBar/MenuBar";
import { NavigationBar } from "../../components/NavigationBar/NavigationBar";
import { Sidebar } from "../../components/Sidebar/Sidebar";
import { useUser } from "../../utils/UserContext.tsx";

interface ChatMessage {
    content: string;
    type: 'ai' | 'user';
    timestamp: string;
    username?: string;
    profile_picture?: string;
}

interface QuickInput {
    id: number;
    text: string;
}

function Chat() {
    const { user } = useUser();
    // 存储聊天记录
    const [messages, setMessages] = useState<ChatMessage[]>([{
        content: `欢迎 ${user.username}，来询问我相关问题吧！`,
        type: "ai",
        timestamp: new Date().toLocaleTimeString(),
    }]);
    // 存储输入框的值
    const [inputValue, setInputValue] = useState<string>("");
    // 创建聊天历史区域的引用
    const chatHistoryRef = useRef<HTMLDivElement | null>(null);

    // 自动滚动到最新消息
    useEffect(() => {
        if (chatHistoryRef.current) {
            chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
        }
    }, [messages]);

    // 快捷输入选项
    const quickInputs: QuickInput[] = [
            { id: 1, text: "你好，请问..." },
            { id: 2, text: "能帮我解释一下..." },
            { id: 3, text: "如何实现..." },
            { id: 4, text: "有什么建议..." },
            { id: 5, text: "有什么建议..." },
            { id: 6, text: "有什么建议..." },
        ];

    // 处理快捷输入点击
    const handleQuickInput = (text: string): void => {
        setInputValue(text);
    };

    // 处理发送消息
    const handleSendMessage = async (): Promise<void> => {
        if (!inputValue.trim()) return;

        // 添加用户消息到聊天记录
        const userMessage: ChatMessage = {
            content: inputValue,
            type: "user",
            timestamp: new Date().toLocaleTimeString(),
            username: user.username,
            profile_picture: user.profile_picture,
        };
        setMessages((prev) => [...prev, userMessage]);
        setInputValue("");

        // 模拟AI回复
        const aiMessage: ChatMessage = {
            content: `回复 ${user.username}：这是一个AI回复的示例消息`,
            type: "ai",
            timestamp: new Date().toLocaleTimeString(),
        };
        setMessages((prev) => [...prev, aiMessage]);
    };

    // 处理按键事件（回车发送）
    const handleKeyPress = (
        e: React.KeyboardEvent<HTMLTextAreaElement>
    ): void => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    // ... 其余代码保持不变 ...
    // existing code...
    return (
        <div className="Container">
            <MenuBar />
            <div className="main-content">
                <NavigationBar />
                <Sidebar />
                <div className="content">
                    <div className="Chat">
                        <div className="Chat-History" ref={chatHistoryRef}>
                            {messages.map((message, index) => (
                                <div key={index} className={`message ${message.type}-message`}>
                                    <img
                                        src={
                                            message.type === "ai"
                                                ? "/public/robot.svg"
                                                : "/public/user.svg"
                                        }
                                        alt={`${message.type} avatar`}
                                        className="message-avatar"
                                    />
                                    <div className="message-content-wrapper">
                                        <div className="message-content">{message.content}</div>
                                        <div className="message-timestamp">{message.timestamp}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="Quick-Inputs">
                            {quickInputs.map((item) => (
                                <div
                                    key={item.id}
                                    className="quick-input-item"
                                    onClick={() => handleQuickInput(item.text)}
                                >
                                    {item.text}
                                </div>
                            ))}
                        </div>
                        <div className="Chat-Input">
                            <textarea
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder="输入消息，按Enter发送..."
                            />
                            <button onClick={handleSendMessage} className="send-button">
                                发送
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Chat;
