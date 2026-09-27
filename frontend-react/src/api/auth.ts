import { http } from './client';
import type { ServerKeys } from './types';

/** Swap the shared password for a session token. */
export async function login(password: string): Promise<string> {
  const { data } = await http.post<{ token: string }>('/api/auth/login', { password });
  return data.token;
}

/** Which API keys the server has. */
export async function getServerKeys(): Promise<ServerKeys> {
  const { data } = await http.get<ServerKeys>('/api/auth/status');
  return data;
}
