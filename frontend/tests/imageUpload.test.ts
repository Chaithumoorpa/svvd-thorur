import { AxiosError } from 'axios';
import { describe, expect, it } from 'vitest';
import {
  MAX_EDGE_PX, UPLOAD_LIMIT_BYTES, UnsupportedImageError, isUploadableAsIs, photoUploadErrorMessage, scaledSize,
} from '@/lib/imageUpload';

describe('scaledSize', () => {
  it('shrinks the longest edge to the cap, keeping the aspect ratio', () => {
    expect(scaledSize(8000, 6000)).toEqual({ width: MAX_EDGE_PX, height: 1536 });
    expect(scaledSize(3000, 4000)).toEqual({ width: 1536, height: MAX_EDGE_PX });
  });

  it('never upscales a photo that is already small enough', () => {
    expect(scaledSize(1200, 900)).toEqual({ width: 1200, height: 900 });
    expect(scaledSize(MAX_EDGE_PX, 10)).toEqual({ width: MAX_EDGE_PX, height: 10 });
  });

  it('never rounds an extreme panorama down to zero pixels', () => {
    expect(scaledSize(100000, 10).height).toBe(1);
  });
});

describe('isUploadableAsIs', () => {
  it('passes accepted types within the size cap', () => {
    expect(isUploadableAsIs({ type: 'image/png', size: 1024 })).toBe(true);
  });

  it('rejects phone formats and oversized files', () => {
    expect(isUploadableAsIs({ type: 'image/heic', size: 1024 })).toBe(false);
    expect(isUploadableAsIs({ type: '', size: 1024 })).toBe(false);
    expect(isUploadableAsIs({ type: 'image/jpeg', size: UPLOAD_LIMIT_BYTES + 1 })).toBe(false);
  });
});

describe('photoUploadErrorMessage', () => {
  const notConfigured = 'not configured';

  it('explains an unreadable format with a way out', () => {
    expect(photoUploadErrorMessage(new UnsupportedImageError(), notConfigured)).toMatch(/screenshot/);
  });

  it('distinguishes uploads being switched off from network failures', () => {
    const disabled = new AxiosError('x', '503', undefined, undefined, { status: 503 } as never);
    expect(photoUploadErrorMessage(disabled, notConfigured)).toBe(notConfigured);
    expect(photoUploadErrorMessage(new AxiosError('Network Error'), notConfigured)).toMatch(/internet connection/);
  });
});
