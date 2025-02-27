import "../reset.css";
import "./Chat.css";
import React, { useEffect, useRef, useState } from 'react';
import { MenuBar } from "../../components/MenuBar/MenuBar";
import { NavigationBar } from "../../components/NavigationBar/NavigationBar";
import { Sidebar } from "../../components/Sidebar/Sidebar";
import { useUser } from "../../utils/UserContext.tsx";
import { chat, chatHistory, getChatHistory, getChat, getChatWithFile } from "../../api/user";

interface ChatMessage {
    content: string;
    type: string;
}

interface QuickInput {
    id: number;
    text: string;
}

function Chat() {
    const { user, currentRepo } = useUser();
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [inputValue, setInputValue] = useState<string>("");
    const [isTyping, setIsTyping] = useState<boolean>(false);
    const chatHistoryRef = React.useRef<HTMLDivElement | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    useEffect(() => {
        if (chatHistoryRef.current) {
            chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
        }
    }, [messages]);

    useEffect(() => {
        const fetchChatHistory = async () => {
            try {
                const history = await getChatHistory(user.id, currentRepo.id);
                let formattedMessages: ChatMessage[] = history.texts.flatMap(text => [
                    { content: text.question.text, type: text.question.sayer },
                    { content: text.answer.text, type: text.answer.sayer }
                ]);
                formattedMessages = [{ content: "你好，我可以回答您的任何问题！", type: "assistant" }, ...formattedMessages];
                setMessages(formattedMessages);
            } catch (error) {
                console.error("获取聊天历史失败:", error);
            }
        };

        fetchChatHistory();
    }, []);

    const quickInputs: QuickInput[] = [
        { id: 1, text: "你能帮我在识别金融欺诈方面做些什么吗？" },
        { id: 2, text: "能帮分析一下这个文件显示内容的欺诈概率吗." },
        { id: 3, text: "如何实现..." },
        { id: 4, text: "有什么建议..." },
    ];

    const handleQuickInput = (text: string): void => {
        setInputValue(text);
    };


    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            setSelectedFile(file);
        }
    };

    const handleRemoveFile = () => {
        setSelectedFile(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const handleSendMessage = async (): Promise<void> => {
        if (!inputValue.trim()) return;

        const userMessage: ChatMessage = {
            content: selectedFile 
                ? `${inputValue} [附件: ${selectedFile.name}]` 
                : inputValue,
            type: "user",
        };

        setMessages((prev) => [...prev, userMessage, {content: "正在思考中...", type: "assistant"}]);
        setInputValue("");
        setIsTyping(true);

        try {
            let response;
            if (selectedFile) {
                response = await getChatWithFile(user.id, currentRepo.id, inputValue, selectedFile);
                setSelectedFile(null); // 清除已选择的文件
                if (fileInputRef.current) {
                    fileInputRef.current.value = ''; // 清除文件输入框
                }
            } else {
                response = await getChat(user.id, currentRepo.id, inputValue);
            }
            
            setMessages((prev) => [...prev.slice(0, prev.length-1)]);
            typeWriterEffect(response.text);
        } catch (error) {
            console.error("发送消息失败:", error);
            setMessages((prev) => [...prev.slice(0, prev.length-1), {
                content: "消息发送失败，请重试",
                type: "assistant"
            }]);
            setIsTyping(false);
        }
    };

    const typeWriterEffect = (text: string) => {
        let index = 0;
        const aiMessage: ChatMessage = { content: "", type: "assistant" };

        setMessages((prev) => [...prev, aiMessage]);

        const interval = setInterval(() => {
            if (index < text.length) {
                aiMessage.content += text.charAt(index);
                setMessages((prev) => {
                    const newMessages = [...prev];
                    newMessages[newMessages.length - 1] = aiMessage;
                    return newMessages;
                });
                index++;
            } else {
                clearInterval(interval);
                setIsTyping(false);
            }
        }, 10); //10MS刷新一个字符
    };

    const handleKeyPress = (
        e: React.KeyboardEvent<HTMLTextAreaElement>
    ): void => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

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
                                            message.type === "assistant"
                                                ? "/public/robot.svg"
                                                : "/public/user.svg"
                                        }
                                        alt={`${message.type} avatar`}
                                        className="message-avatar"
                                    />
                                    <div className="message-content-wrapper">
                                        <div className="message-content">{message.content}</div>
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
                            <div className="input-container">
                                <textarea
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    onKeyPress={handleKeyPress}
                                    placeholder="输入消息，按Enter发送..."
                                    disabled={isTyping}
                                />
                                <div className="file-upload-container">
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        onChange={handleFileSelect}
                                        style={{ display: 'none' }}
                                        disabled={isTyping}
                                    />
                                    <button 
                                        onClick={() => fileInputRef.current?.click()}
                                        className="file-button"
                                        disabled={isTyping}
                                    >
                                     <img src="/public/upload.svg" alt="上传文件" className="upload-icon" />
                                     {!selectedFile && (
                                        <div className="selected-file-prompt">
                                            [至多可选1个文件] 请选择文件 (支持PDF,DOCX,XLSX,TXT,JPG等)
                                        </div>
                                     )}
                                    </button>
                                    {selectedFile && (
                                        <div className="selected-file">
                                            <span>{selectedFile.name}</span>
                                            <button onClick={handleRemoveFile}>×</button>
                                        </div>
                                    )}
                                </div>
                            </div>
                            <button 
                                onClick={handleSendMessage} 
                                className="send-button" 
                                disabled={isTyping}
                            >
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
