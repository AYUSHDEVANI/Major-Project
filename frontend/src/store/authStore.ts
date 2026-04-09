import { create } from 'zustand';
import { jwtDecode } from 'jwt-decode';
import { api } from '../api/client';

export interface User {
  id: string; // "sub" claim
  email: string;
  role: 'engineer' | 'admin' | 'viewer' | string;
  permissions?: string[];
  company_name?: string;
}

interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  user: User | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (formData: FormData) => Promise<void>;
  logout: () => Promise<void>;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  token: null,
  user: null,
  isLoading: false,
  error: null,

  login: async (formData: FormData) => {
    set({ isLoading: true, error: null });
    try {
      // The api.login call handles putting the token in localStorage
      const data = await api.login(formData);
      const token = data.access_token;
      
      const decoded = jwtDecode<any>(token);
      
      const user: User = {
        id: decoded.sub,
        email: decoded.email,
        role: decoded.role,
        permissions: decoded.permissions,
        company_name: decoded.company_name,
      };

      set({
        isAuthenticated: true,
        token,
        user,
        isLoading: false,
        error: null,
      });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Invalid email or password',
        isLoading: false,
        isAuthenticated: false,
        token: null,
        user: null,
      });
    }
  },

  logout: async () => {
    try {
      await api.logout();
    } catch (e) {
      console.warn("Logout endpoint failed, clearing local session anyway.");
    } finally {
      // client.ts handles localStorage clear, but we'll enforce it here too
      localStorage.removeItem('access_token');
      set({
        isAuthenticated: false,
        token: null,
        user: null,
        error: null,
      });
    }
  },

  hydrate: () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ isAuthenticated: false, token: null, user: null });
      return;
    }

    try {
      const decoded = jwtDecode<any>(token);
      
      // Basic expiration check
      if (decoded.exp * 1000 < Date.now()) {
        localStorage.removeItem('access_token');
        set({ isAuthenticated: false, token: null, user: null });
        return;
      }

      set({
        isAuthenticated: true,
        token,
        user: {
          id: decoded.sub,
          email: decoded.email,
          role: decoded.role,
          permissions: decoded.permissions,
          company_name: decoded.company_name,
        }
      });
    } catch (e) {
      localStorage.removeItem('access_token');
      set({ isAuthenticated: false, token: null, user: null });
    }
  }
}));
