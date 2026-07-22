import { AppBar, Box, Button, Toolbar, Typography } from '@mui/material';
import KeyIcon from '@mui/icons-material/Key';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import { useApiKeysDialog } from '../apiKeys/ApiKeysProvider';
import { ApiKeysStatus } from '../apiKeys/ApiKeysStatus';

export const DRAWER_WIDTH = 280;

export function TopBar() {
  const { openDialog } = useApiKeysDialog();
  return (
    <AppBar
      position="fixed"
      color="default"
      elevation={1}
      sx={{ zIndex: (theme) => theme.zIndex.drawer + 1, bgcolor: 'background.paper' }}
    >
      <Toolbar>
        <SmartToyIcon color="primary" sx={{ mr: 1 }} />
        <Typography variant="h6" noWrap sx={{ fontWeight: 700 }}>
          AI Lead Generator
        </Typography>
        <Box sx={{ flexGrow: 1 }} />
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <ApiKeysStatus onClick={openDialog} />
          <Button variant="outlined" startIcon={<KeyIcon />} onClick={openDialog}>
            API Keys
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
