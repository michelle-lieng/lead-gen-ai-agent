/**
 * The project's conversation.
 *
 * Each project has exactly one thread, kept by the backend, so reopening a
 * project — on this device or another — picks it up where it left off. Lines
 * appear on screen the moment they are written and are saved in small batches
 * behind them; a failed save is retried and never holds up the run that wrote
 * the line.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { appendChat, getChat } from '../api/chat';
import { ChatEntry, ChatEntryCreate } from '../api/types';
import { queryKeys } from './queryKeys';

export interface ThreadLine extends ChatEntryCreate {
  key: string;
  at: Date;
}

/** How long to gather lines before saving them together. */
const SAVE_DELAY_MS = 500;
const RETRY_MIN_MS = 2000;
const RETRY_MAX_MS = 30000;
const PAGE_SIZE = 200;
const MAX_FAILURES_AFTER_LEAVING = 5;

export function useProjectChat(projectId: number) {
  // Fetched fresh on every visit and never cached between them: lines written
  // during a visit live in local state, so a cached copy would be missing them
  // and a background refetch would show them twice.
  const history = useQuery({
    queryKey: queryKeys.chat(projectId),
    queryFn: () => getChat(projectId, { limit: PAGE_SIZE }),
    enabled: !Number.isNaN(projectId),
    gcTime: 0,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  const [older, setOlder] = useState<ChatEntry[]>([]);
  const [olderHasMore, setOlderHasMore] = useState<boolean | null>(null);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [local, setLocal] = useState<ThreadLine[]>([]);
  const [unsaved, setUnsaved] = useState(0);

  const queue = useRef<ChatEntryCreate[]>([]);
  const sending = useRef(false);
  const timer = useRef<number>();
  const retryDelay = useRef(RETRY_MIN_MS);
  const failures = useRef(0);
  const mounted = useRef(true);
  const localId = useRef(0);

  const flush = useCallback(async () => {
    window.clearTimeout(timer.current);
    if (sending.current || queue.current.length === 0) return;
    sending.current = true;
    const batch = queue.current.slice(0, PAGE_SIZE);
    let failed = false;
    try {
      await appendChat(projectId, batch);
      queue.current = queue.current.slice(batch.length);
      retryDelay.current = RETRY_MIN_MS;
      failures.current = 0;
    } catch {
      // Keep the lines queued and try again later, backing off.
      failed = true;
      failures.current += 1;
      retryDelay.current = Math.min(retryDelay.current * 2, RETRY_MAX_MS);
    } finally {
      sending.current = false;
      if (mounted.current) setUnsaved(queue.current.length);
    }
    // Once the project is closed nobody is watching, so stop retrying eventually.
    const givenUp = !mounted.current && failures.current >= MAX_FAILURES_AFTER_LEAVING;
    if (queue.current.length > 0 && !givenUp) {
      timer.current = window.setTimeout(flush, failed ? retryDelay.current : 0);
    }
  }, [projectId]);

  useEffect(() => {
    mounted.current = true;
    return () => {
      // Leaving the project: save whatever is still waiting right away.
      mounted.current = false;
      void flush();
    };
  }, [flush]);

  /** Add a line to the thread: on screen now, saved shortly after. */
  const append = useCallback(
    (entry: ChatEntryCreate) => {
      queue.current.push(entry);
      if (!mounted.current) {
        void flush();
        return;
      }
      setLocal((current) => [
        ...current,
        { ...entry, key: `local-${localId.current++}`, at: new Date() },
      ]);
      setUnsaved(queue.current.length);
      if (!sending.current) {
        window.clearTimeout(timer.current);
        timer.current = window.setTimeout(flush, SAVE_DELAY_MS);
      }
    },
    [flush],
  );

  const hasMore = olderHasMore ?? history.data?.has_more ?? false;

  const loadEarlier = useCallback(async () => {
    const first = older[0] ?? history.data?.entries[0];
    if (!first || loadingOlder) return;
    setLoadingOlder(true);
    try {
      const page = await getChat(projectId, { before: first.id, limit: PAGE_SIZE });
      setOlder((current) => [...page.entries, ...current]);
      setOlderHasMore(page.has_more);
    } finally {
      setLoadingOlder(false);
    }
  }, [older, history.data, loadingOlder, projectId]);

  const lines = useMemo<ThreadLine[]>(
    () => [
      ...[...older, ...(history.data?.entries ?? [])].map(toLine),
      ...local,
    ],
    [older, history.data, local],
  );

  return {
    lines,
    append,
    /** Nothing may be written until the saved thread is on screen. */
    ready: history.isSuccess,
    loading: history.isLoading,
    loadError: history.error,
    hasMore,
    loadingOlder,
    loadEarlier,
    /** Lines written but not yet confirmed saved. */
    unsaved,
  };
}

function toLine(entry: ChatEntry): ThreadLine {
  return {
    key: `saved-${entry.id}`,
    at: new Date(entry.created_at),
    role: entry.role,
    kind: entry.kind,
    text: entry.text,
    payload: entry.payload,
  };
}
