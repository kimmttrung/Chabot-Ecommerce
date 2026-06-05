// src/hooks/useSessions.ts
import { useState, useEffect, useCallback } from 'react';
import { sessionApi, type SessionData } from '../services/api';

export const useSessions = () => {
    const [sessions, setSessions] = useState<SessionData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchSessions = useCallback(async () => {
        try {
            setLoading(true);
            const data = await sessionApi.getAll();
            setSessions(data);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    }, []);

    const createSession = useCallback(async () => {
        try {
            const newSession = await sessionApi.create();
            const newSessionData: SessionData = {
                id: newSession.session_id,
                title: newSession.title,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            };
            setSessions(prev => [newSessionData, ...prev]);
            return newSessionData.id;
        } catch (err) {
            console.error(err);
            return null;
        }
    }, []);

    const deleteSession = useCallback(async (id: string) => {
        try {
            await sessionApi.delete(id);
            setSessions(prev => prev.filter(s => s.id !== id));
            return true;
        } catch (err) {
            console.error(err);
            return false;
        }
    }, []);

    useEffect(() => {
        fetchSessions();
    }, [fetchSessions]);

    return { sessions, loading, error, fetchSessions, createSession, deleteSession };
};