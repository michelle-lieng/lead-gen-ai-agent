/**
 * API keys.
 *
 * Nothing in this product runs without the user's own OpenAI and Jina keys, so
 * the state is carried permanently in the running head and the sheet only
 * appears when it is opened or when a run is blocked for want of a key.
 */

import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react';
import { useApiKeys } from '../../store/apiKeys';
import { Modal } from '../ui/Modal';
import { Button, Field } from '../ui/Primitives';
import { useNotify } from '../ui/Toasts';

interface KeysApi {
  openDialog: () => void;
  /** True when both keys are present; otherwise opens the sheet and returns false. */
  requireKeys: () => boolean;
}

const KeysContext = createContext<KeysApi | null>(null);

export function ApiKeysProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const { openaiKey, jinaKey, googleKey, hasKeys, setKeys, clearKeys } = useApiKeys();
  const { notify } = useNotify();

  const [draftOpenai, setDraftOpenai] = useState(openaiKey);
  const [draftJina, setDraftJina] = useState(jinaKey);
  const [draftGoogle, setDraftGoogle] = useState(googleKey);

  const openDialog = useCallback(() => {
    setDraftOpenai(openaiKey);
    setDraftJina(jinaKey);
    setDraftGoogle(googleKey);
    setOpen(true);
  }, [openaiKey, jinaKey, googleKey]);

  const requireKeys = useCallback(() => {
    if (hasKeys) return true;
    notify('Enter your OpenAI and Jina keys before running anything.', 'warning');
    openDialog();
    return false;
  }, [hasKeys, notify, openDialog]);

  const api = useMemo(() => ({ openDialog, requireKeys }), [openDialog, requireKeys]);

  const save = () => {
    setKeys({ openaiKey: draftOpenai, jinaKey: draftJina, googleKey: draftGoogle });
    notify('Keys saved in this browser.', 'success');
    setOpen(false);
  };

  return (
    <KeysContext.Provider value={api}>
      {children}
      <Modal
        open={open}
        title="Your API keys"
        note="Held in this browser only and sent with each request that needs them. The server keeps no keys of its own."
        onClose={() => setOpen(false)}
        width={520}
        footer={
          <>
            <Button
              tone="danger"
              icon="trash"
              disabled={!openaiKey && !jinaKey && !googleKey}
              onClick={() => {
                clearKeys();
                setDraftOpenai('');
                setDraftJina('');
                setDraftGoogle('');
                notify('Keys cleared from this browser.', 'info');
              }}
            >
              Clear keys
            </Button>
            <div style={{ flex: 1 }} />
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button
              tone="primary"
              icon="check"
              disabled={!draftOpenai.trim() || !draftJina.trim()}
              onClick={save}
            >
              Save keys
            </Button>
          </>
        }
      >
        <div style={{ display: 'grid', gap: 18 }}>
          <Field
            label="OpenAI key"
            type="password"
            autoComplete="off"
            spellCheck={false}
            placeholder="sk-…"
            value={draftOpenai}
            onChange={(event) => setDraftOpenai(event.target.value)}
            hint="Writes the search queries, extracts company names, and answers every enrichment column."
          />
          <Field
            label="Jina key"
            type="password"
            autoComplete="off"
            spellCheck={false}
            placeholder="jina_…"
            value={draftJina}
            onChange={(event) => setDraftJina(event.target.value)}
            hint="Runs the searches and reads the pages the answers come from."
          />
          <Field
            label="Google Places key (optional)"
            type="password"
            autoComplete="off"
            spellCheck={false}
            placeholder="AIza…"
            value={draftGoogle}
            onChange={(event) => setDraftGoogle(event.target.value)}
            hint="Finds businesses on Google Maps when you name a location. Needs Places API (New) enabled."
          />
          <p
            style={{
              paddingTop: 14,
              borderTop: '1px solid var(--line)',
              fontSize: 12,
              lineHeight: 1.55,
              color: 'var(--text-2)',
            }}
          >
            Keys are stored in this browser’s local storage, which any script running on
            this page can read. Use “Clear keys” when you are finished on a shared machine.
          </p>
        </div>
      </Modal>
    </KeysContext.Provider>
  );
}

export function useApiKeysDialog(): KeysApi {
  const context = useContext(KeysContext);
  if (!context) throw new Error('useApiKeysDialog must be used inside ApiKeysProvider');
  return context;
}
