import { create } from 'zustand';
import { User } from '@/types/api';
import { TOKEN_STORAGE_KEY, USER_STORAGE_KEY } from '@/utils/constants';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  logout: () => void;
  initAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,

  setUser: (user) => {
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
    set({ user, isAuthenticated: true });
  },

  setToken: (token) => {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
    set({ token });
  },

  logout: () => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
    set({ user: null, token: null, isAuthenticated: false });
  },

  initAuth: () => {
    try {
      const token = localStorage.getItem(TOKEN_STORAGE_KEY);
      const userJson = localStorage.getItem(USER_STORAGE_KEY);
      
      if (token && userJson) {
        const user = JSON.parse(userJson) as User;
        set({ 
          token, 
          user, 
          isAuthenticated: true,
          isLoading: false 
        });
      } else {
        set({ isLoading: false });
      }
    } catch (error) {
      console.error('Failed to init auth:', error);
      set({ isLoading: false });
    }
  },
}));
