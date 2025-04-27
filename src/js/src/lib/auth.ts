import { create } from 'zustand';
import { AccessService } from '@/lib/api/services/AccessService';

interface AuthState {
  user: any | null;
  currentTeam: any | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  setCurrentTeam: (team: any) => void;
}

const accessService = new AccessService();

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  currentTeam: null,
  isLoading: false,
  isAuthenticated: false,
  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      await accessService.accountLogin({
        username: email,
        password,
      });
      const { data: user } = await accessService.accountProfile();
      set({ user, isAuthenticated: true });
    } finally {
      set({ isLoading: false });
    }
  },
  logout: async () => {
    set({ isLoading: true });
    try {
      await accessService.accountLogout();
      set({ user: null, currentTeam: null, isAuthenticated: false });
    } finally {
      set({ isLoading: false });
    }
  },
  checkAuth: async () => {
    set({ isLoading: true });
    try {
      const { data: user } = await accessService.accountProfile();
      set({ user, isAuthenticated: true });
    } catch {
      set({ user: null, currentTeam: null, isAuthenticated: false });
    } finally {
      set({ isLoading: false });
    }
  },
  setCurrentTeam: (team: any) => set({ currentTeam: team }),
}));
