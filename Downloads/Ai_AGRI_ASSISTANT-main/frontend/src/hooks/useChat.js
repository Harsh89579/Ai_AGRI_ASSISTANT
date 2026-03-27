import { useState, useEffect, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const CHAT_URL = `${API_BASE_URL}/api/chat`;

export const useChat = () => {
    const [sessionId, setSessionId] = useState('');
    const [messages, setMessages] = useState([]);
    const [sessions, setSessions] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    // Initialize session
    useEffect(() => {
        const savedSessionId = localStorage.getItem('agri_session_id');
        if (savedSessionId) {
            setSessionId(savedSessionId);
            loadChatHistory(savedSessionId);
        } else {
            createNewSession();
        }
        refreshSessions();
    }, []);

    const createNewSession = () => {
        const newId = uuidv4();
        setSessionId(newId);
        setMessages([]);
        localStorage.setItem('agri_session_id', newId);
        refreshSessions();
    };

    const switchSession = (id) => {
        setSessionId(id);
        localStorage.setItem('agri_session_id', id);
        loadChatHistory(id);
    };

    const loadChatHistory = async (id) => {
        try {
            const res = await fetch(`${API_BASE_URL}/api/chat/history/${id}`);
            if (res.ok) {
                const data = await res.json();
                setMessages(data.history.map(h => ({
                    role: h.role,
                    content: h.message,
                    timestamp: h.timestamp,
                    source: h.role === 'bot' ? 'knowledge_base' : null
                })));
            }
        } catch (err) {
            console.error('Failed to load history:', err);
        }
    };

    const refreshSessions = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/api/chat/session`);
            if (res.ok) {
                const data = await res.json();
                setSessions(data);
            }
        } catch (err) {
            console.error('Failed to fetch sessions:', err);
        }
    };

    const sendMessage = async (text) => {
        if (!text.trim()) return;

        const userMsg = { 
            role: 'user', 
            content: text, 
            timestamp: new Date().toISOString() 
        };
        
        setMessages(prev => [...prev, userMsg]);
        setIsLoading(true);

        try {
            const resp = await fetch(CHAT_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, message: text }),
            });

            const data = await resp.json();
            const botMsg = {
                role: 'bot',
                content: data.reply,
                source: data.source,
                follow_ups: data.follow_ups || [],
                timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, botMsg]);
            refreshSessions();
        } catch (err) {
            setMessages(prev => [...prev, {
                role: 'bot',
                content: 'I am having trouble connecting to the servers. Please try again later.',
                source: 'error',
                follow_ups: [],
                timestamp: new Date().toISOString()
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    return {
        sessionId,
        messages,
        sessions,
        isLoading,
        sendMessage,
        createNewSession,
        switchSession
    };
};
