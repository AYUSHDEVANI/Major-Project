import axios from 'axios';
import { AgentState } from '../types';

const API_URL = 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const api = {
    ingestManual: async (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return apiClient.post('/ingest', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },

    analyzeImage: async (file: File, notes?: string) => {
        const formData = new FormData();
        formData.append('file', file);
        if (notes) formData.append('notes', notes);
        
        const response = await apiClient.post<AgentState>('/analyze', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    },

    // History
    getHistory: async () => {
        const response = await axios.get(`${API_URL}/history`);
        return response.data;
    }
};
