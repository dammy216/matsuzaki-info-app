import { useState, useEffect, useRef } from "react";

export const useWebSocket = (url: string) => {
    const [messages, setMessages] = useState<string[]>([]);
    const socketRef = useRef<WebSocket | null>(null);

    //WebSocket接続
    useEffect(() => {
        const socket = new WebSocket(url);
        socketRef.current = socket;

        socket.onopen = () => console.log("WebSocket 接続成功");

        socket.onmessage = (event) => {
            console.log("受信:", event.data);
            setMessages((prev) => [...prev, event.data]);
        };

        //エラー処理
        socket.onerror = (error) => console.error("WebSocket エラー:", error);
        socket.onclose = () => console.log("WebSocket 接続が閉じました");

        return () => {
            socket.close();
        };
    }, [url]);

    //webSocketにメッセージを送る
    const sendMessage = (data: object) => {
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify(data));
        } else {
            console.error("WebSocket が開いていません");
        }
    };

    return { messages, sendMessage };
};
