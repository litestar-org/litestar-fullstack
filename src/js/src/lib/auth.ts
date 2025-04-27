import { create } from 'zustand';
import { accountLogin, accountLogout, accountProfile } from '@/lib/api/sdk.gen';
import { User, Team } from '@/lib/api/types.gen';

interface AuthState {
  user: User | null;
  currentTeam: Team | null;
  teams: Team[];
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  setCurrentTeam: (team: Team) => void;
  setTeams: (teams: Team[]) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  currentTeam: null,
  teams: [],
  isLoading: false,
  isAuthenticated: false,
  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      await accountLogin({ body: { username: email, password } });
      const { data: user } = await accountProfile();
      set({ user, isAuthenticated: true });
    } finally {
      set({ isLoading: false });
    }
  },
  logout: async () => {
    set({ isLoading: true });
    try {
      await accountLogout();
      set({ user: null, currentTeam: null, isAuthenticated: false });
    } finally {
      set({ isLoading: false });
    }
  },
  checkAuth: async () => {
    set({ isLoading: true });
    try {
      const { data: user } = await accountProfile();
      set({ user, isAuthenticated: true });
    } catch {
      set({ user: null, currentTeam: null, isAuthenticated: false });
    } finally {
      set({ isLoading: false });
    }
  },
  setCurrentTeam: (team: Team) => set({ currentTeam: team }),
  setTeams: (teams: Team[]) => set({ teams }),
}));
