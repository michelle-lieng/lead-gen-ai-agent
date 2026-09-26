/**
 * A project's identity: the coloured square and the initials inside it.
 *
 * Derived from the record's own id so a project keeps the same colour in the
 * sidebar, on the home grid, and across reloads — recognising a project by its
 * colour only works if the colour never moves.
 */

/** Saturated enough to carry white initials at 4.5:1 or better. */
const COLORS = [
  '#12305c', // Kiyu navy
  '#0f6f62', // teal
  '#5b43b8', // violet
  '#9c5410', // amber
  '#a52c50', // rose
  '#246b39', // green
];

export function projectColor(id: number): string {
  return COLORS[Math.abs(id) % COLORS.length];
}

/** Up to two initials from the project's name, falling back to a letter. */
export function projectInitials(name: string): string {
  const words = name
    .trim()
    .split(/[\s\-_/]+/)
    .filter(Boolean);
  if (words.length === 0) return 'P';
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}
