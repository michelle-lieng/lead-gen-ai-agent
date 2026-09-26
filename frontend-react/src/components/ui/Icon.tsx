/**
 * The icon set.
 *
 * One 1.5px stroke on a 16px grid, round caps and joins — the weight a grid
 * database sets its chrome in. Field-type glyphs (`field-*`) are the ones that
 * matter most: they are how a column declares what it holds before anyone
 * reads a value.
 */

export type IconName =
  | 'search'
  | 'import'
  | 'download'
  | 'trash'
  | 'pencil'
  | 'key'
  | 'plus'
  | 'close'
  | 'check'
  | 'alert'
  | 'info'
  | 'stop'
  | 'more'
  | 'sidebar'
  | 'panel'
  | 'rows'
  | 'expand'
  | 'copy'
  | 'chevron-left'
  | 'chevron-right'
  | 'chevron-down'
  | 'sparkle'
  | 'field-text'
  | 'field-longtext'
  | 'field-number'
  | 'field-select';

const PATHS: Record<IconName, JSX.Element> = {
  search: (
    <>
      <circle cx="7.25" cy="7.25" r="4.25" />
      <path d="M10.5 10.5 13.5 13.5" />
    </>
  ),
  import: (
    <>
      <path d="M8 10.5V2.5" />
      <path d="M5 7.5 8 10.5l3-3" />
      <path d="M2.75 11v2.5h10.5V11" />
    </>
  ),
  download: (
    <>
      <path d="M8 2.5v8" />
      <path d="M5 7.5 8 10.5l3-3" />
      <path d="M3 13.5h10" />
    </>
  ),
  trash: (
    <>
      <path d="M2.75 4.25h10.5" />
      <path d="M6.25 4.25V2.75h3.5v1.5" />
      <path d="M4 4.25v9a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-9" />
      <path d="M6.5 6.75v5M9.5 6.75v5" />
    </>
  ),
  pencil: (
    <>
      <path d="M11.25 2.25 13.75 4.75 5.5 13H3v-2.5z" />
      <path d="M9.5 4 12 6.5" />
    </>
  ),
  key: (
    <>
      <circle cx="5.5" cy="6" r="2.75" />
      <path d="M7.4 7.9 13.5 14" />
      <path d="M11.25 11.75 12.5 10.5M9.5 10 10.75 8.75" />
    </>
  ),
  plus: <path d="M8 3v10M3 8h10" />,
  close: <path d="M4 4l8 8M12 4l-8 8" />,
  check: <path d="M3 8.5 6.25 11.75 13 5" />,
  alert: (
    <>
      <path d="M8 2.5 14.5 13.5h-13z" />
      <path d="M8 6.5v3.25" />
      <path d="M8 11.75h.01" />
    </>
  ),
  info: (
    <>
      <circle cx="8" cy="8" r="5.75" />
      <path d="M8 7.25v4" />
      <path d="M8 5h.01" />
    </>
  ),
  stop: <rect x="4" y="4" width="8" height="8" rx="1.25" />,
  more: (
    <>
      <circle cx="3.75" cy="8" r="1.1" fill="currentColor" stroke="none" />
      <circle cx="8" cy="8" r="1.1" fill="currentColor" stroke="none" />
      <circle cx="12.25" cy="8" r="1.1" fill="currentColor" stroke="none" />
    </>
  ),
  sidebar: (
    <>
      <rect x="2.25" y="3" width="11.5" height="10" rx="1.5" />
      <path d="M6.25 3v10" />
    </>
  ),
  panel: (
    <>
      <rect x="2.25" y="3" width="11.5" height="10" rx="1.5" />
      <path d="M9.75 3v10" />
    </>
  ),
  rows: (
    <>
      <path d="M2.5 4.25h11M2.5 8h11M2.5 11.75h11" />
    </>
  ),
  expand: (
    <>
      <path d="M9.5 3h3.5v3.5" />
      <path d="M6.5 13H3V9.5" />
      <path d="M13 3 9.25 6.75M3 13l3.75-3.75" />
    </>
  ),
  copy: (
    <>
      <rect x="5.75" y="5.75" width="7.5" height="7.5" rx="1.25" />
      <path d="M10.25 5.75V4a1.25 1.25 0 0 0-1.25-1.25H4A1.25 1.25 0 0 0 2.75 4v5a1.25 1.25 0 0 0 1.25 1.25h1.75" />
    </>
  ),
  'chevron-left': <path d="M10 3.5 5.5 8l4.5 4.5" />,
  'chevron-right': <path d="M6 3.5 10.5 8 6 12.5" />,
  'chevron-down': <path d="M3.5 6 8 10.5 12.5 6" />,
  // The AI field's own mark: a four-point star with a small second star.
  sparkle: (
    <>
      <path d="M6.25 2.25 7.4 5.1 10.25 6.25 7.4 7.4 6.25 10.25 5.1 7.4 2.25 6.25 5.1 5.1z" />
      <path d="M11.75 9.25 12.4 10.85 14 11.5 12.4 12.15 11.75 13.75 11.1 12.15 9.5 11.5 11.1 10.85z" />
    </>
  ),
  // Single line text: the "A" a grid database prints over a text column.
  'field-text': (
    <>
      <path d="M3.25 12 7 4h1.25L12 12" />
      <path d="M4.9 9.1h6.2" />
    </>
  ),
  // Long text: stacked lines, the last one short.
  'field-longtext': (
    <>
      <path d="M2.75 4.25h10.5M2.75 7.25h10.5M2.75 10.25h10.5M2.75 13.25h6" />
    </>
  ),
  'field-number': (
    <>
      <path d="M6.25 2.75 4.75 13.25M11.25 2.75 9.75 13.25" />
      <path d="M3 6.25h10.25M2.75 9.75H13" />
    </>
  ),
  // Single select: the chevron in a circle.
  'field-select': (
    <>
      <circle cx="8" cy="8" r="5.75" />
      <path d="M5.75 6.75 8 9.25l2.25-2.5" />
    </>
  ),
};

interface IconProps {
  name: IconName;
  size?: number;
  className?: string;
  /** Solid fill for glyphs drawn as shapes rather than lines. */
  filled?: boolean;
}

export function Icon({ name, size = 14, className, filled = false }: IconProps) {
  return (
    <svg
      viewBox="0 0 16 16"
      width={size}
      height={size}
      className={className}
      fill={filled ? 'currentColor' : 'none'}
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      style={{ display: 'block', flex: 'none' }}
    >
      {PATHS[name]}
    </svg>
  );
}
