import { create } from 'zustand';
import { UserResponse } from '@/types/api';
import { AuthService } from '@/lib/auth';

interface AuthState {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: UserResponse | null) => void;
  loadUser: () => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  setUser: (user) =>
    set({
      user,
      isAuthenticated: !!user,
      isLoading: false,
    }),

  loadUser: () => {
    try {
      const user = AuthService.getUser();
      const isAuthenticated = AuthService.isAuthenticated();
      set({
        user,
        isAuthenticated,
        isLoading: false,
      });
    } catch (error) {
      console.error('Failed to load user:', error);
      // Clear any corrupted auth data
      AuthService.clearAuth();
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },

  logout: () => {
    AuthService.clearAuth();
    set({
      user: null,
      isAuthenticated: false,
    });
  },
}));
