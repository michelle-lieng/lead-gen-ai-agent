import { Alert, Button } from '@mui/material';
import { useState } from 'react';
import { useApiKeys } from '../../store/apiKeys';
import { useApiKeysDialog } from './ApiKeysProvider';

/** Dismissible banner prompting the user to enter API keys when missing. */
export function ApiKeysBanner() {
  const { hasKeys } = useApiKeys();
  const { openDialog } = useApiKeysDialog();
  const [dismissed, setDismissed] = useState(false);

  if (hasKeys || dismissed) return null;

  return (
    <Alert
      severity="warning"
      sx={{ mb: 2 }}
      onClose={() => setDismissed(true)}
      action={
        <Button color="inherit" size="small" onClick={openDialog}>
          Enter keys
        </Button>
      }
    >
      Enter your OpenAI and Jina API keys to run AI search and enrichment. Keys are
      stored only in your browser.
    </Alert>
  );
}
