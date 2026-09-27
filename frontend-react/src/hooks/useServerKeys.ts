/**
 * Which API keys the server has. Runs need OpenAI and Jina; Google Places
 * only adds Google Maps to location searches.
 */

import { useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getServerKeys } from '../api/auth';
import { useNotify } from '../components/ui/Toasts';
import { hasRequiredKeys, useSignedIn } from '../store/session';
import { queryKeys } from './queryKeys';

export function useServerKeys(): {
  hasKeys: boolean;
  googleKey: boolean;
  requireKeys: () => boolean;
} {
  const signedIn = useSignedIn();
  const { notify } = useNotify();
  const { data } = useQuery({
    queryKey: queryKeys.serverKeys,
    queryFn: getServerKeys,
    enabled: signedIn,
  });
  const hasKeys = hasRequiredKeys(data);

  const requireKeys = useCallback(() => {
    if (hasKeys) return true;
    notify(
      "Set OPENAI_API_KEY and JINA_API_KEY in the backend's environment before running anything.",
      'warning',
    );
    return false;
  }, [hasKeys, notify]);

  return { hasKeys, googleKey: Boolean(data?.google), requireKeys };
}
