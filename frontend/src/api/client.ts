import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true // Important for sending the HttpOnly refresh token cookie
});

// Configure Request Interceptor to attach Access Token
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Configure Response Interceptor for Auto-Refresh
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        
        // If 401 Unauthorized, and we haven't already retried this request
        if (error.response?.status === 401 && !originalRequest._retry) {
            // Bypass interceptor for auth routes
            if (originalRequest.url?.includes('/login') || originalRequest.url?.includes('/refresh')) {
                return Promise.reject(error);
            }

            originalRequest._retry = true;
            try {
                // Warning: We shouldn't use apiClient here to avoid infinite interceptor loops
                const refreshResponse = await axios.post(`${API_URL}/refresh`, {}, {
                    withCredentials: true // send the cookie
                });
                
                const { access_token } = refreshResponse.data;
                localStorage.setItem('access_token', access_token);
                
                // Update header and retry
                originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
                return apiClient(originalRequest);
            } catch (refreshError) {
                // Refresh failed, meaning session is fully dead
                localStorage.removeItem('access_token');
                // Could emit event here to redirect user to login
                return Promise.reject(refreshError);
            }
        }
        return Promise.reject(error);
    }
);

export const api = {
    // Auth
    login: async (formData: FormData) => {
        const response = await apiClient.post('/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        localStorage.setItem('access_token', response.data.access_token);
        return response.data;
    },
    
    logout: async () => {
        await apiClient.post('/logout');
        localStorage.removeItem('access_token');
    },

    ingestManual: async (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return apiClient.post('/ingest', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },

    analyzeImage: async (file: File, notes?: string, onProgress?: (step: string) => void) => {
        const formData = new FormData();
        formData.append('file', file);
        if (notes) formData.append('notes', notes);
        
        const token = localStorage.getItem('access_token');
        const headers: HeadersInit = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        
        const response = await fetch(`${API_URL}/analyze`, {
            method: 'POST',
            body: formData,
            headers
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText);
        }

        if (!response.body) throw new Error("No response body");

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let done = false;
        let finalResult = null;
        let buffer = '';

        while (!done) {
            const { value, done: readerDone } = await reader.read();
            done = readerDone;
            if (value) {
                buffer += decoder.decode(value, { stream: true });
            }
            
            // Process all complete SSE messages in the buffer
            const payloads = buffer.split('\n\n');
            buffer = payloads.pop() || ''; // Keep incomplete segment
            
            for (const payload of payloads) {
                if (payload.startsWith('data: ')) {
                    const dataStr = payload.slice(6);
                    const data = JSON.parse(dataStr);
                    if (data.error) throw new Error(data.error);
                    if (data.step === 'done' || data.step === 'paused_for_approval') {
                        finalResult = data.result;
                    } else if (onProgress) {
                        onProgress(data.step);
                    }
                }
            }
        }

        // Process any remaining data left in the buffer after stream closes
        if (buffer.trim()) {
            const remaining = buffer.trim();
            if (remaining.startsWith('data: ')) {
                const dataStr = remaining.slice(6);
                try {
                    const data = JSON.parse(dataStr);
                    if (data.error) throw new Error(data.error);
                    if (data.step === 'done' || data.step === 'paused_for_approval') {
                        finalResult = data.result;
                    }
                } catch (e) {
                    console.warn('Failed to parse final SSE buffer:', e);
                }
            }
        }

        return finalResult;
    },

    // History
    getHistory: async () => {
        const response = await apiClient.get(`/history`);
        return response.data;
    },

    // Admin - User Management
    getUsers: async () => {
        const response = await apiClient.get('/admin/users');
        return response.data;
    },
    createUser: async (data: { email: string; password: string; role: string; employee_id?: string }) => {
        const response = await apiClient.post('/admin/users', data);
        return response.data;
    },
    deleteUser: async (email: string) => {
        const response = await apiClient.delete(`/admin/users/${encodeURIComponent(email)}`);
        return response.data;
    },
    toggleUser: async (email: string) => {
        const response = await apiClient.patch(`/admin/users/${encodeURIComponent(email)}/toggle`);
        return response.data;
    },

    // Admin - Document Management
    getDocuments: async () => {
        const response = await apiClient.get('/admin/documents');
        return response.data;
    },
    toggleDocument: async (filename: string) => {
        const response = await apiClient.patch(`/admin/documents/${encodeURIComponent(filename)}/toggle`);
        return response.data;
    },

    // Super Admin
    setupSuperAdmin: async (data: any) => {
        const response = await apiClient.post('/setup-superadmin', data);
        return response.data;
    },
    getSuperAdminCompanies: async () => {
        const response = await apiClient.get('/superadmin/companies');
        return response.data;
    },
    getSuperAdminUsers: async () => {
        const response = await apiClient.get('/superadmin/users');
        return response.data;
    },
    getSuperAdminDocuments: async () => {
        const response = await apiClient.get('/superadmin/documents');
        return response.data;
    },
    toggleSuperAdminUser: async (userId: number) => {
        const response = await apiClient.patch(`/superadmin/users/${userId}/toggle`);
        return response.data;
    },
    deleteSuperAdminUser: async (userId: number) => {
        const response = await apiClient.delete(`/superadmin/users/${userId}`);
        return response.data;
    },
    toggleSuperAdminDocument: async (docId: number) => {
        const response = await apiClient.patch(`/superadmin/documents/${docId}/toggle`);
        return response.data;
    },
    deleteSuperAdminDocument: async (docId: number) => {
        const response = await apiClient.delete(`/superadmin/documents/${docId}`);
        return response.data;
    },
    toggleSuperAdminCompany: async (companyId: number) => {
        const response = await apiClient.patch(`/superadmin/companies/${companyId}/toggle`);
        return response.data;
    },

    // Support Chat
    getChatSessions: async () => {
        const response = await apiClient.get('/chat/sessions');
        return response.data;
    },

    getChatHistory: async (sessionId: number) => {
        const response = await apiClient.get(`/chat/sessions/${sessionId}`);
        return response.data;
    },

    getChatStream: (message: string, historyId?: number, sessionId?: number) => {
        const token = localStorage.getItem('access_token');
        const url = `${apiClient.defaults.baseURL}/chat/stream?message=${encodeURIComponent(message)}${historyId ? `&history_id=${historyId}` : ''}${sessionId ? `&session_id=${sessionId}` : ''}`;
        
        return fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
    }
};
