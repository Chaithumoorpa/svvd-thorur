import { describe, expect, it } from 'vitest';
import { isEmbeddableMap, templeAddress, templeLocation, templeName } from '@/lib/site';
import type { Temple } from '@/lib/types';

const temple = { id: 1, name: 'Sri Test Temple', village: 'Thorur', district: null, state: 'AP', address: '1 Temple Rd', pincode: '506163' } as Temple;

describe('site helpers', () => {
  it('falls back gracefully when no profile exists', () => {
    expect(templeName(null)).toBeTruthy();
    expect(templeAddress(null)).toBe('');
    expect(templeLocation(null)).toBe('');
  });

  it('joins only the parts that are set', () => {
    expect(templeLocation(temple)).toBe('Thorur, AP');
    expect(templeAddress(temple)).toBe('1 Temple Rd, Thorur, AP, 506163');
  });

  it('only embeds Google Maps embed URLs', () => {
    expect(isEmbeddableMap('https://www.google.com/maps/embed?pb=abc')).toBe(true);
    expect(isEmbeddableMap('https://evil.example/maps/embed')).toBe(false);
    expect(isEmbeddableMap('javascript:alert(1)')).toBe(false);
    expect(isEmbeddableMap(null)).toBe(false);
  });
});
