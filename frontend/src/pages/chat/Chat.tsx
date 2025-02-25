import "../reset.css";
import "./Chat.css";
import React, { useEffect, useState } from 'react';
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
        { id: 1, text: "你好，请问..." },
        { id: 2, text: "能帮我解释一下..." },
        { id: 3, text: "如何实现..." },
        { id: 4, text: "有什么建议..." },
        { id: 5, text: "有什么建议..." },
        { id: 6, text: "有什么建议..." },
    ];

    const handleQuickInput = (text: string): void => {
        setInputValue(text);
    };

    const handleSendMessage = async (): Promise<void> => {
        if (!inputValue.trim()) return;

        const userMessage: ChatMessage = {
            content: inputValue,
            type: "user",
        };

        setMessages((prev) => [...prev, userMessage, {content: "正在思考中...", type: "assistant"}]);
        setInputValue("");
        setIsTyping(true);

        try {
            const response = await getChat(user.id, currentRepo.id, inputValue);
            setMessages((prev) => [...prev.slice(0, prev.length-1)]);
            typeWriterEffect(response.text);
        } catch (error) {
            console.error("发送消息失败:", error);
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
        }, 33); //33MS刷新一个字符
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
                            <textarea
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder="输入消息，按Enter发送..."
                            />
                            <button onClick={handleSendMessage} className="send-button" disabled={isTyping}>
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
