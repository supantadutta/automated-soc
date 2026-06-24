import { describe, it, expect } from 'vitest';
import {
  cn,
  formatCost,
  formatNumber,
  severityColor,
  verdictColor,
  truncate,
  initials,
} from './utils';

describe('formatCost', () => {
  it('renders sub-cent values with 4 decimals', () => {
    expect(formatCost(0.0004)).toBe('$0.0004');
  });
  it('renders normal values with 2 decimals', () => {
    expect(formatCost(1.5)).toBe('$1.50');
  });
  it('handles null/NaN', () => {
    expect(formatCost(null)).toBe('$0.00');
    expect(formatCost(undefined)).toBe('$0.00');
  });
});

describe('severityColor', () => {
  it('maps known severities and is case-insensitive', () => {
    expect(severityColor('Critical')).toBe('#ef4444');
    expect(severityColor('high')).toBe('#f97316');
    expect(severityColor('unknown')).toBe('#64748b');
  });
});

describe('verdictColor', () => {
  it('maps true positive to red and benign/FP to green', () => {
    expect(verdictColor('True Positive')).toBe('#ef4444');
    expect(verdictColor('False Positive')).toBe('#22c55e');
    expect(verdictColor('Benign')).toBe('#22c55e');
  });
});

describe('misc helpers', () => {
  it('cn merges class names', () => {
    expect(cn('a', false && 'b', 'c')).toContain('a');
  });
  it('truncate adds ellipsis past the limit', () => {
    expect(truncate('abcdef', 3)).toBe('abc…');
    expect(truncate('ab', 3)).toBe('ab');
  });
  it('formatNumber abbreviates thousands/millions', () => {
    expect(formatNumber(1500)).toBe('1.5K');
    expect(formatNumber(2_000_000)).toBe('2.0M');
    expect(formatNumber(42)).toBe('42');
  });
  it('initials returns up to two letters', () => {
    expect(initials('Jane Doe')).toBe('JD');
  });
});
