import { Chip } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';
import { useApiKeys } from '../../store/apiKeys';

/** Small chip showing whether both API keys are set. */
export function ApiKeysStatus({ onClick }: { onClick?: () => void }) {
  const { hasKeys } = useApiKeys();
  return (
    <Chip
      size="small"
      color={hasKeys ? 'success' : 'warning'}
      variant={hasKeys ? 'filled' : 'outlined'}
      icon={hasKeys ? <CheckCircleIcon /> : <WarningIcon />}
      label={hasKeys ? 'API keys set' : 'API keys needed'}
      onClick={onClick}
      sx={{ color: hasKeys ? 'white' : undefined }}
    />
  );
}
