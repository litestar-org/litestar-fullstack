import { accountLogout } from "@/lib/api/sdk.gen";
import { create } from "zustand";

interface User {
	id: string;
	email: string;
	avatar_url: string | null;
}

interface AuthState {
	user: User | null;
	isLoading: boolean;
	error: string | null;
	setUser: (user: User | null) => void;
	setError: (error: string | null) => void;
	logout: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
	user: null,
	isLoading: true,
	error: null,
	setUser: (user) => set({ user, isLoading: false }),
	setError: (error) => set({ error, isLoading: false }),
	logout: async () => {
		try {
			await accountLogout();
			set({ user: null, isLoading: false, error: null });
		} catch (error) {
			set({ error: "Failed to logout", isLoading: false });
		}
	},
}));
