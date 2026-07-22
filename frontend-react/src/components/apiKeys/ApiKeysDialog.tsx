import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  IconButton,
  InputAdornment,
  Link,
  Stack,
  TextField,
} from '@mui/material';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import { useEffect, useState } from 'react';
import { useApiKeys } from '../../store/apiKeys';
import { useNotify } from '../common/Notifications';

interface ApiKeysDialogProps {
  open: boolean;
  onClose: () => void;
}

/** Dialog for entering / clearing the user's OpenAI and Jina API keys. */
export function ApiKeysDialog({ open, onClose }: ApiKeysDialogProps) {
  const { openaiKey, jinaKey, setKeys, clearKeys } = useApiKeys();
  const { notify } = useNotify();

  const [openai, setOpenai] = useState(openaiKey);
  const [jina, setJina] = useState(jinaKey);
  const [showOpenai, setShowOpenai] = useState(false);
  const [showJina, setShowJina] = useState(false);

  // Re-seed local fields whenever the dialog is (re)opened.
  useEffect(() => {
    if (open) {
      setOpenai(openaiKey);
      setJina(jinaKey);
    }
  }, [open, openaiKey, jinaKey]);

  const handleSave = () => {
    setKeys({ openaiKey: openai, jinaKey: jina });
    notify('API keys saved.', 'success');
    onClose();
  };

  const handleClear = () => {
    clearKeys();
    setOpenai('');
    setJina('');
    notify('API keys cleared.', 'info');
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Your API Keys</DialogTitle>
      <DialogContent>
        <DialogContentText sx={{ mb: 2 }}>
          Enter your own OpenAI and Jina API keys. They are stored only in this
          browser (localStorage) and sent with each request that needs them.
        </DialogContentText>
        <Stack spacing={2}>
          <TextField
            label="OpenAI API Key"
            placeholder="sk-..."
            fullWidth
            type={showOpenai ? 'text' : 'password'}
            value={openai}
            onChange={(e) => setOpenai(e.target.value)}
            autoComplete="off"
            helperText={
              <>
                Get one at{' '}
                <Link href="https://platform.openai.com/api-keys" target="_blank" rel="noreferrer">
                  platform.openai.com/api-keys
                </Link>
              </>
            }
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={() => setShowOpenai((v) => !v)} edge="end">
                    {showOpenai ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          <TextField
            label="Jina API Key"
            placeholder="Your Jina key"
            fullWidth
            type={showJina ? 'text' : 'password'}
            value={jina}
            onChange={(e) => setJina(e.target.value)}
            autoComplete="off"
            helperText={
              <>
                Get one at{' '}
                <Link href="https://jina.ai/reader" target="_blank" rel="noreferrer">
                  jina.ai
                </Link>
              </>
            }
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={() => setShowJina((v) => !v)} edge="end">
                    {showJina ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          <Alert severity="info">
            Keys never leave your browser except to call this app's backend, which
            uses them to reach OpenAI and Jina on your behalf.
          </Alert>
        </Stack>
      </DialogContent>
      <DialogActions sx={{ justifyContent: 'space-between', px: 3, pb: 2 }}>
        <Button color="error" onClick={handleClear}>
          Clear keys
        </Button>
        <span>
          <Button onClick={onClose} sx={{ mr: 1 }}>
            Cancel
          </Button>
          <Button variant="contained" onClick={handleSave}>
            Save
          </Button>
        </span>
      </DialogActions>
    </Dialog>
  );
}
