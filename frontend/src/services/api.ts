// services/api.ts
const API_BASE = 'http://localhost:8000/api';

export interface SessionData {
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
}

export const sessionApi = {
    getAll: async (): Promise<SessionData[]> => {
        const res = await fetch(`${API_BASE}/sessions`);
        if (!res.ok) throw new Error('Failed to fetch sessions');
        const data = await res.json();
        return data.sessions;
    },
    create: async (): Promise<{ session_id: string; title: string }> => {
        const res = await fetch(`${API_BASE}/sessions`, { method: 'POST' });
        if (!res.ok) throw new Error('Failed to create session');
        return res.json();
    },
    delete: async (id: string): Promise<void> => {
        const res = await fetch(`${API_BASE}/sessions/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete session');
    },
};

export interface ChatMessage {
    session_id: string;
    message: string;
}

export interface ChatResponse {
    session_id: string;
    response: string;
    title?: string;
    history: any[];
}

export const chatApi = {
    send: async (sessionId: string, message: string): Promise<ChatResponse> => {
        const res = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, message }),
        });
        if (!res.ok) throw new Error('Failed to send message');
        return res.json();
    },
};