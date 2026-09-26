/**
 * An anchored popover, portalled to the body.
 *
 * The grid scrolls in both directions and clips its overflow, so a menu drawn
 * inside it would be cut off. Every menu in the app is therefore positioned
 * from its anchor's rect in a fixed layer, flips above the anchor when the
 * viewport runs out below, and is clamped to stay on screen.
 */

import {
  KeyboardEvent as ReactKeyboardEvent,
  ReactNode,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from 'react';
import { createPortal } from 'react-dom';
import { Icon, IconName } from './Icon';

const GAP = 4;
const EDGE = 8;

export function Popover({
  anchor,
  onClose,
  children,
  align = 'start',
  width,
  label,
}: {
  /** The element the menu hangs from; null closes it. */
  anchor: HTMLElement | null;
  onClose: () => void;
  children: ReactNode;
  align?: 'start' | 'end';
  width?: number;
  label: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null);

  const place = useCallback(() => {
    const node = ref.current;
    if (!anchor || !node) return;
    const a = anchor.getBoundingClientRect();
    const box = node.getBoundingClientRect();

    let top = a.bottom + GAP;
    if (top + box.height > window.innerHeight - EDGE) {
      const above = a.top - GAP - box.height;
      top = above >= EDGE ? above : Math.max(EDGE, window.innerHeight - EDGE - box.height);
    }

    let left = align === 'end' ? a.right - box.width : a.left;
    left = Math.min(Math.max(EDGE, left), Math.max(EDGE, window.innerWidth - EDGE - box.width));

    setPos({ top, left });
  }, [anchor, align]);

  useLayoutEffect(() => {
    if (!anchor) return undefined;
    place();
    // Re-place rather than close: a menu opened over a scrolling grid should
    // stay attached to its column head.
    const onMove = () => place();
    window.addEventListener('resize', onMove);
    window.addEventListener('scroll', onMove, true);
    return () => {
      window.removeEventListener('resize', onMove);
      window.removeEventListener('scroll', onMove, true);
    };
  }, [anchor, place]);

  // Focus the first item, and hand focus back to the anchor on close.
  useEffect(() => {
    if (!anchor) return undefined;
    const timer = window.setTimeout(() => {
      ref.current?.querySelector<HTMLElement>('[data-pop-item]')?.focus();
    }, 0);
    return () => {
      window.clearTimeout(timer);
      if (document.body.contains(anchor)) anchor.focus({ preventScroll: true });
    };
  }, [anchor]);

  useEffect(() => {
    if (!anchor) return undefined;
    const onPointerDown = (event: PointerEvent) => {
      const target = event.target as Node;
      if (ref.current?.contains(target) || anchor.contains(target)) return;
      onClose();
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.stopPropagation();
        onClose();
      }
    };
    document.addEventListener('pointerdown', onPointerDown, true);
    document.addEventListener('keydown', onKeyDown, true);
    return () => {
      document.removeEventListener('pointerdown', onPointerDown, true);
      document.removeEventListener('keydown', onKeyDown, true);
    };
  }, [anchor, onClose]);

  if (!anchor) return null;

  const onKeyDown = (event: ReactKeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return;
    event.preventDefault();
    const items = Array.from(
      ref.current?.querySelectorAll<HTMLElement>('[data-pop-item]') ?? [],
    );
    if (items.length === 0) return;
    const at = items.indexOf(document.activeElement as HTMLElement);
    const next =
      event.key === 'ArrowDown'
        ? items[(at + 1) % items.length]
        : items[(at - 1 + items.length) % items.length];
    next.focus();
  };

  return createPortal(
    <div
      ref={ref}
      className="pop"
      role="menu"
      aria-label={label}
      onKeyDown={onKeyDown}
      style={{
        top: pos?.top ?? -9999,
        left: pos?.left ?? -9999,
        width,
        visibility: pos ? 'visible' : 'hidden',
      }}
    >
      {children}
    </div>,
    document.body,
  );
}

/* ------------------------------------------------------------------- items */

export function PopItem({
  icon,
  children,
  onClick,
  tone,
  checked,
}: {
  icon?: IconName;
  children: ReactNode;
  onClick: () => void;
  tone?: 'danger';
  checked?: boolean;
}) {
  return (
    <button
      type="button"
      data-pop-item="true"
      role={checked === undefined ? 'menuitem' : 'menuitemradio'}
      aria-checked={checked}
      className="pop__item"
      data-tone={tone}
      onClick={onClick}
    >
      {icon && <Icon name={icon} size={14} />}
      <span>{children}</span>
      {checked && (
        <span className="pop__item__mark" aria-hidden="true">
          <Icon name="check" size={13} />
        </span>
      )}
    </button>
  );
}

export function PopLabel({ children }: { children: ReactNode }) {
  return <span className="pop__label">{children}</span>;
}

export function PopRule() {
  return <hr className="pop__rule" />;
}

export function PopNote({ children }: { children: ReactNode }) {
  return <p className="pop__note">{children}</p>;
}
