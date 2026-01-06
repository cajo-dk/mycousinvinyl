import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

interface ViewControlsConfig {
  viewKey: string;
  searchPlaceholder: string;
  searchValue: string;
  onSearchChange: (value: string) => void;
  onSearchSubmit: () => void;
  filtersContent?: ReactNode;
}

interface ViewControlsContextValue {
  controls: ViewControlsConfig | null;
  setControls: (controls: ViewControlsConfig | null) => void;
  showFilters: boolean;
  setShowFilters: (value: boolean) => void;
}

const ViewControlsContext = createContext<ViewControlsContextValue | undefined>(undefined);

export function ViewControlsProvider({ children }: { children: ReactNode }) {
  const [controls, setControls] = useState<ViewControlsConfig | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    setShowFilters(false);
  }, [controls?.viewKey]);

  const value = useMemo(
    () => ({
      controls,
      setControls,
      showFilters,
      setShowFilters,
    }),
    [controls, showFilters]
  );

  return (
    <ViewControlsContext.Provider value={value}>
      {children}
    </ViewControlsContext.Provider>
  );
}

export function useViewControls() {
  const context = useContext(ViewControlsContext);
  if (!context) {
    throw new Error('useViewControls must be used within a ViewControlsProvider');
  }
  return context;
}
