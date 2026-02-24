import { createHash } from 'crypto';

export function slugifyTitle(title: string): string {
  return title
    .toLowerCase()
    .trim()
    .replace(/["']/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export function formatDateSlug(date: Date): string {
  return date.toISOString().slice(0, 10);
}

export function buildSlug(date: Date, title: string): string {
  return `${formatDateSlug(date)}--${slugifyTitle(title)}`;
}

export function hashSlug(slug: string): string {
  return createHash('sha256').update(slug).digest('hex');
}
