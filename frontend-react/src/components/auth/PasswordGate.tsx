/**
 * The password gate: nothing in the app renders until this tab holds a
 * session from the shared password. A 401 anywhere, or Sign out, ends the
 * session and brings the gate back with the cache emptied, so nothing from
 * the old session is left on screen.
 */

import { FormEvent, ReactNode, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { login } from '../../api/auth';
import { errorToMessage } from '../../api/errors';
import { clearLegacyKeys, setToken, useSignedIn } from '../../store/session';
import { Button, Field } from '../ui/Primitives';

export function PasswordGate({ children }: { children: ReactNode }) {
  const signedIn = useSignedIn();
  const queryClient = useQueryClient();
  const wasSignedIn = useRef(signedIn);

  useEffect(() => {
    clearLegacyKeys();
  }, []);

  // Runs after the app has unmounted, so clearing starts no refetches.
  useEffect(() => {
    if (wasSignedIn.current && !signedIn) queryClient.clear();
    wasSignedIn.current = signedIn;
  }, [signedIn, queryClient]);

  if (signedIn) return <>{children}</>;
  return <SignIn />;
}

function SignIn() {
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!password || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      setToken(await login(password));
    } catch (err) {
      setError(errorToMessage(err));
      setSubmitting(false);
    }
  };

  return (
    <main className="gate">
      <form className="gate__card" onSubmit={submit}>
        <h1 className="gate__title">Leads</h1>
        <p className="gate__lede">Enter the password to open the app.</p>
        <Field
          label="Password"
          id="gate-password"
          type="password"
          autoFocus
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? 'gate-error' : undefined}
        />
        {error && (
          <p className="gate__error" id="gate-error" role="alert">
            {error}
          </p>
        )}
        <Button tone="primary" type="submit" loading={submitting} disabled={!password}>
          Enter
        </Button>
      </form>
    </main>
  );
}
