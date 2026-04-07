import { create } from 'zustand';
import { AgentState } from '../types';
import { api } from '../api/client';

interface AppState {
    isLoading: boolean;
    error: string | null;
    analysisResult: AgentState | null;
    history: any[]; // Using any for now, or define a RepairLog type
    
    // Actions
    uploadImage: (file: File, notes?: string) => Promise<void>;
    uploadManual: (file: File) => Promise<void>;
    fetchHistory: () => Promise<void>;
    resetError: () => void;
}

export const useAppStore = create<AppState>((set) => ({
    isLoading: false,
    error: null,
    analysisResult: null,

    uploadImage: async (file, notes) => {
        set({ isLoading: true, error: null });
        try {
            const result = await api.analyzeImage(file, notes);
            set({ analysisResult: result, isLoading: false });
        } catch (err: any) {
            set({ 
                error: err.response?.data?.detail || 'Failed to analyze image', 
                isLoading: false 
            });
        }
    },

    uploadManual: async (file) => {
         set({ isLoading: true, error: null });
        try {
            await api.ingestManual(file);
            set({ isLoading: false });
            alert("Manual uploaded successfully!");
        } catch (err: any) {
             set({ 
                error: err.response?.data?.detail || 'Failed to upload manual', 
                isLoading: false 
            });
        }
    },
    
    // History Actions
    history: [],
    fetchHistory: async () => {
        set({ isLoading: true, error: null });
        try {
            const history = await api.getHistory();
            set({ history, isLoading: false });
        } catch (err: any) {
            set({ 
                error: err.response?.data?.detail || 'Failed to fetch history', 
                isLoading: false 
            });
        }
    },

    resetError: () => set({ error: null })
}));
