import type { Team } from "@/lib/api";
import { listTeams } from "@/lib/api/sdk.gen";
import { useQuery } from "@tanstack/react-query";
import { type ReactNode, createContext, useContext, useState } from "react";

type TeamContextType = {
  currentTeam: Team | null;
  setCurrentTeam: (team: Team | null) => void;
  teams: Team[];
  isLoading: boolean;
};

const TeamContext = createContext<TeamContextType | undefined>(undefined);

export function TeamProvider({ children }: { children: ReactNode }) {
  const [currentTeam, setCurrentTeam] = useState<Team | null>(null);

  const { data: teams = [], isLoading } = useQuery({
    queryKey: ["teams"],
    queryFn: async () => {
      const response = await listTeams();
      return response.data?.items ?? [];
    },
  });

  return (
    <TeamContext.Provider
      value={{
        currentTeam,
        setCurrentTeam,
        teams,
        isLoading,
      }}
    >
      {children}
    </TeamContext.Provider>
  );
}

export function useTeam() {
  const context = useContext(TeamContext);
  if (context === undefined) {
    throw new Error("useTeam must be used within a TeamProvider");
  }
  return context;
}
