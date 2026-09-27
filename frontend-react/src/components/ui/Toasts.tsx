/**
 * Toasts, bottom-right, three deep.
 *
 * Severity reads from the icon and its ink, not from a coloured ground: a wash
 * behind every message would make routine confirmations shout as loudly as
 * failures.
 */

import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from 'react';
import { errorToMessage, isApiKeyError } from '../../api/errors';
import { Icon, IconName } from './Icon';
import { IconButton } from './Primitives';

export type NoticeTone = 'success' | 'error' | 'warning' | 'info';

interface Notice {
  id: number;
  tone: NoticeTone;
  message: string;
}

interface NotifyApi {
  notify: (message: string, tone?: NoticeTone) => void;
  notifyError: (err: unknown) => void;
}

const NotifyContext = createContext<NotifyApi | null>(null);

const TONE: Record<NoticeTone, { ink: string; icon: IconName; label: string }> = {
  success: { ink: 'var(--success)', icon: 'check', label: 'Done' },
  error: { ink: 'var(--danger)', icon: 'alert', label: 'Failed' },
  warning: { ink: 'var(--warning)', icon: 'alert', label: 'Check this' },
  info: { ink: 'var(--accent)', icon: 'info', label: 'Note' },
};

const LIFETIME_MS = 7000;

export function NotificationsProvider({ children }: { children: ReactNode }) {
  const [notices, setNotices] = useState<Notice[]>([]);
  const nextId = useRef(1);

  const dismiss = useCallback((id: number) => {
    setNotices((current) => current.filter((notice) => notice.id !== id));
  }, []);

  const notify = useCallback(
    (message: string, tone: NoticeTone = 'info') => {
      const id = nextId.current++;
      setNotices((current) => [...current.slice(-2), { id, tone, message }]);
      window.setTimeout(() => dismiss(id), LIFETIME_MS);
    },
    [dismiss],
  );

  const notifyError = useCallback(
    (err: unknown) => {
      notify(errorToMessage(err), isApiKeyError(err) ? 'warning' : 'error');
    },
    [notify],
  );

  const api = useMemo(() => ({ notify, notifyError }), [notify, notifyError]);

  return (
    <NotifyContext.Provider value={api}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {notices.map((notice) => {
          const tone = TONE[notice.tone];
          return (
            <div key={notice.id} className="toast">
              <span className="toast__icon" style={{ color: tone.ink }}>
                <Icon name={tone.icon} size={14} />
              </span>
              <div className="toast__body">
                <span className="toast__label" style={{ color: tone.ink }}>
                  {tone.label}
                </span>
                <span className="toast__text">{notice.message}</span>
              </div>
              <IconButton
                icon="close"
                label="Dismiss"
                compact
                onClick={() => dismiss(notice.id)}
              />
            </div>
          );
        })}
      </div>
    </NotifyContext.Provider>
  );
}

export function useNotify(): NotifyApi {
  const context = useContext(NotifyContext);
  if (!context) throw new Error('useNotify must be used inside NotificationsProvider');
  return context;
}
