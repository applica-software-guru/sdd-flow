import { describe, expect, it } from 'vitest';
import { getApiErrorMessage } from '../hooks/useTenants';

describe('getApiErrorMessage', () => {
  it('returns backend detail when available', () => {
    const error = {
      response: {
        data: {
          detail: 'User is already a member',
        },
      },
    };

    expect(getApiErrorMessage(error, 'fallback')).toBe('User is already a member');
  });

  it('returns fallback when backend detail is missing', () => {
    const error = {
      response: {
        data: {},
      },
    };

    expect(getApiErrorMessage(error, 'fallback')).toBe('fallback');
  });

  it('returns fallback when error shape is unknown', () => {
    expect(getApiErrorMessage(new Error('boom'), 'fallback')).toBe('fallback');
  });
});