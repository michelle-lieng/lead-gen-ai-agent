import { http } from './client';
import { ChatEntry, ChatEntryCreate, ChatHistory, MessagePlan } from './types';

/** A page of the project's conversation, oldest first. */
export async function getChat(
  projectId: number,
  options: { before?: number; limit?: number } = {},
): Promise<ChatHistory> {
  const { data } = await http.get<ChatHistory>(`/api/projects/${projectId}/chat`, {
    params: options,
  });
  return data;
}

/** Append entries to the project's conversation, in the order they happened. */
export async function appendChat(
  projectId: number,
  entries: ChatEntryCreate[],
): Promise<ChatEntry[]> {
  const { data } = await http.post<ChatEntry[]>(`/api/projects/${projectId}/chat`, {
    entries,
  });
  return data;
}

/** What one chat message asks the agent to do. Nothing runs on the server. */
export async function interpretMessage(
  projectId: number,
  instruction: string,
): Promise<MessagePlan> {
  const { data } = await http.post<MessagePlan>(
    `/api/projects/${projectId}/chat/interpret`,
    { instruction },
  );
  return data;
}
