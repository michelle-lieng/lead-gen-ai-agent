/**
 * The confirmation card: what the agent is about to do, shown in the chat
 * before any search or column research runs.
 *
 * The card is a saved chat entry carrying the plan. Whether it can still be
 * started is read from the thread itself, so it survives a reload with no
 * extra state: it is live only while it is the newest line.
 */

import type { MessagePlan } from '../../api/types';
import type { ThreadLine } from '../../hooks/useProjectChat';

export const STARTED_LINE = 'Started.';
export const CANCELLED_LINE = 'Cancelled. Nothing ran.';

/** A search or new columns wait for Start; continuing and replies do not. */
export function needsConfirmation(plan: MessagePlan): boolean {
  return plan.find || plan.criteria.length > 0 || plan.columns.length > 0;
}

/** Anything at all left to run. */
export function hasWork(plan: MessagePlan): boolean {
  return needsConfirmation(plan) || plan.continue_columns.length > 0;
}

export interface CardEdits {
  base: string;
  removedCriteria: number[];
  removedColumns: number[];
  /** Columns that were going to be continued, removed from the card. */
  removedContinue: number[];
  /** Skip the Google Maps search but keep the web search. */
  removedLocation: boolean;
}

/** The plan as the user left the card: edited search, removed chips dropped. */
export function applyCardEdits(plan: MessagePlan, edits: CardEdits): MessagePlan {
  const base = edits.base.trim();
  const find = plan.find && base !== '';
  return {
    ...plan,
    find,
    find_instruction: find ? base : '',
    location: find && !edits.removedLocation ? plan.location : '',
    criteria: plan.criteria.filter((_, index) => !edits.removedCriteria.includes(index)),
    columns: plan.columns.filter((_, index) => !edits.removedColumns.includes(index)),
    continue_columns: plan.continue_columns.filter(
      (_, index) => !edits.removedContinue.includes(index),
    ),
  };
}

const plural = (count: number, one: string, many: string) => `${count} ${count === 1 ? one : many}`;

/** One line for the card's saved text, e.g. `Search "…" · 2 criteria · 1 column`. */
export function summarisePlan(plan: MessagePlan): string {
  return [
    plan.find ? `Search "${plan.find_instruction}"` : null,
    plural(plan.criteria.length, 'criterion', 'criteria'),
    plural(plan.columns.length, 'column', 'columns'),
  ]
    .filter(Boolean)
    .join(' · ');
}

export function isActiveCard(lines: ThreadLine[], index: number, running: boolean): boolean {
  return lines[index]?.kind === 'breakdown' && index === lines.length - 1 && !running;
}

export type CardState = 'active' | 'started' | 'cancelled' | 'replaced';

/** What became of a card, read from the first line written after it. */
export function cardState(lines: ThreadLine[], index: number): CardState {
  const next = lines[index + 1];
  if (!next) return 'active';
  if (next.text === STARTED_LINE) return 'started';
  if (next.text === CANCELLED_LINE) return 'cancelled';
  return 'replaced';
}

const strings = (value: unknown): string[] =>
  Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];

/**
 * The plan a card was saved with, or null when the entry carries none that can
 * be trusted; such a card renders as a plain line rather than breaking the chat.
 */
export function readCardPlan(payload: unknown): MessagePlan | null {
  const plan = (payload as { plan?: unknown } | null | undefined)?.plan;
  if (!plan || typeof plan !== 'object') return null;
  const raw = plan as Record<string, unknown>;
  if (typeof raw.find !== 'boolean') return null;
  return {
    find: raw.find,
    find_instruction: typeof raw.find_instruction === 'string' ? raw.find_instruction : '',
    location: typeof raw.location === 'string' ? raw.location : '',
    criteria: strings(raw.criteria),
    columns: strings(raw.columns),
    continue_columns: Array.isArray(raw.continue_columns)
      ? (raw.continue_columns as MessagePlan['continue_columns'])
      : [],
    reply: typeof raw.reply === 'string' ? raw.reply : '',
  };
}
