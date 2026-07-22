import { Alert, Snackbar } from '@mui/material';
import { createContext, ReactNode, useCallback, useContext, useMemo, useState } from 'react';
import { errorToMessage } from '../../api/errors';

type Severity = 'success' | 'error' | 'info' | 'warning';

interface NotifyState {
  open: boolean;
  message: string;
  severity: Severity;
}

interface NotifyContextValue {
  notify: (message: string, severity?: Severity) => void;
  notifyError: (err: unknown) => void;
}

const NotifyContext = createContext<NotifyContextValue | null>(null);

export function NotificationsProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<NotifyState>({
    open: false,
    message: '',
    severity: 'info',
  });

  const notify = useCallback((message: string, severity: Severity = 'info') => {
    setState({ open: true, message, severity });
  }, []);

  const notifyError = useCallback(
    (err: unknown) => {
      setState({ open: true, message: errorToMessage(err), severity: 'error' });
    },
    [],
  );

  const value = useMemo(() => ({ notify, notifyError }), [notify, notifyError]);

  return (
    <NotifyContext.Provider value={value}>
      {children}
      <Snackbar
        open={state.open}
        autoHideDuration={6000}
        onClose={() => setState((s) => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity={state.severity}
          variant="filled"
          onClose={() => setState((s) => ({ ...s, open: false }))}
          sx={{ whiteSpace: 'pre-line', maxWidth: 500 }}
        >
          {state.message}
        </Alert>
      </Snackbar>
    </NotifyContext.Provider>
  );
}

export function useNotify(): NotifyContextValue {
  const ctx = useContext(NotifyContext);
  if (!ctx) throw new Error('useNotify must be used within NotificationsProvider');
  return ctx;
}
