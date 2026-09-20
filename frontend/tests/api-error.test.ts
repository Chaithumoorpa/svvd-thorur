import { AxiosError } from 'axios';
import { describe, expect, it } from 'vitest';
import { apiError } from '@/lib/api';

function axiosError(status: number | null, data?: unknown): AxiosError {
  const err = new AxiosError('failed');
  if (status !== null) {
    err.response = { status, data, statusText: '', headers: {}, config: {} as never };
  }
  return err;
}

describe('apiError', () => {
  it('uses the FastAPI detail string', () => {
    expect(apiError(axiosError(400, { detail: 'Username already exists' }))).toBe('Username already exists');
  });

  it('flattens validation errors into a readable sentence', () => {
    const err = axiosError(422, {
      detail: [
        { loc: ['body', 'amount'], msg: 'Input should be greater than 0' },
        { loc: ['body', 'pan_number'], msg: 'Value error, PAN must look like ABCDE1234F' },
      ],
    });
    expect(apiError(err)).toBe('amount: Input should be greater than 0; pan number: PAN must look like ABCDE1234F');
  });

  it('explains network failures, 403 and 429', () => {
    expect(apiError(axiosError(null))).toMatch(/cannot reach the server/i);
    expect(apiError(axiosError(403, {}))).toMatch(/permission/i);
    expect(apiError(axiosError(429, {}))).toMatch(/too many/i);
  });

  it('falls back for unknown errors', () => {
    expect(apiError(new Error('boom'), 'Custom fallback')).toBe('Custom fallback');
  });
});
