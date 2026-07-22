import { createContext, ReactNode, useCallback, useContext, useMemo, useState } from 'react';
import { getApiKeys, hasBothKeys } from '../../store/apiKeys';
import { useNotify } from '../common/Notifications';
import { ApiKeysDialog } from './ApiKeysDialog';

interface ApiKeysContextValue {
  openDialog: () => void;
  /**
   * Returns true if both keys are present. Otherwise opens the keys dialog,
   * shows a hint, and returns false — used to guard AI actions.
   */
  requireKeys: () => boolean;
}

const ApiKeysContext = createContext<ApiKeysContextValue | null>(null);

export function ApiKeysProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const { notify } = useNotify();

  const openDialog = useCallback(() => setOpen(true), []);

  const requireKeys = useCallback(() => {
    if (hasBothKeys(getApiKeys())) return true;
    notify('Please enter your OpenAI and Jina API keys first.', 'warning');
    setOpen(true);
    return false;
  }, [notify]);

  const value = useMemo(() => ({ openDialog, requireKeys }), [openDialog, requireKeys]);

  return (
    <ApiKeysContext.Provider value={value}>
      {children}
      <ApiKeysDialog open={open} onClose={() => setOpen(false)} />
    </ApiKeysContext.Provider>
  );
}

export function useApiKeysDialog(): ApiKeysContextValue {
  const ctx = useContext(ApiKeysContext);
  if (!ctx) throw new Error('useApiKeysDialog must be used within ApiKeysProvider');
  return ctx;
}
