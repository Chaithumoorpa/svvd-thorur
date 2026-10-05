import { isAxiosError } from 'axios';

/**
 * Phone photos are routinely 8-20 MB (50-108 MP cameras) and often HEIC/HEIF,
 * while uploads are capped at the backend's S3_MAX_UPLOAD_MB and accept only
 * JPEG/PNG/WEBP/GIF. Re-encoding in the browser fixes both, keeps uploads quick
 * on mobile data, and drops EXIF metadata - including GPS location - from
 * photos that may be shown publicly.
 */
export const MAX_EDGE_PX = 2048;
export const UPLOAD_LIMIT_BYTES = 8 * 1024 * 1024;
const JPEG_QUALITY = 0.85;
const ACCEPTED_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp', 'image/gif']);

/** The file couldn't be decoded by this browser (e.g. HEIC on Android Chrome). */
export class UnsupportedImageError extends Error {
  constructor() {
    super('Unsupported image');
    this.name = 'UnsupportedImageError';
  }
}

export function scaledSize(width: number, height: number, maxEdge = MAX_EDGE_PX): { width: number; height: number } {
  const longest = Math.max(width, height);
  if (longest <= maxEdge) return { width, height };
  const scale = maxEdge / longest;
  return { width: Math.max(1, Math.round(width * scale)), height: Math.max(1, Math.round(height * scale)) };
}

/** Whether a file can go to S3 untouched: a type the backend accepts, within the size cap. */
export function isUploadableAsIs(file: { type: string; size: number }): boolean {
  return ACCEPTED_TYPES.has(file.type) && file.size <= UPLOAD_LIMIT_BYTES;
}

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new UnsupportedImageError());
    img.src = url;
  });
}

/**
 * `always`: re-encode every photo (strips metadata) - for devotee photos that
 * may be published. `if-needed`: only when the file is too big or in a format
 * the backend rejects - for staff uploads, so a crisp PNG poster stays as-is.
 * GIFs are never re-encoded (that would drop the animation).
 */
export async function prepareImageForUpload(file: File, mode: 'always' | 'if-needed'): Promise<File> {
  if (file.type === 'image/gif' || (mode === 'if-needed' && isUploadableAsIs(file))) return file;

  const url = URL.createObjectURL(file);
  try {
    // <img> decodes whatever this browser can display (HEIC on Safari, for one)
    // and draws it with its EXIF orientation applied.
    const img = await loadImage(url);
    if (!img.naturalWidth || !img.naturalHeight) throw new UnsupportedImageError();
    const { width, height } = scaledSize(img.naturalWidth, img.naturalHeight);
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new UnsupportedImageError();
    ctx.fillStyle = '#fff'; // JPEG has no transparency - avoid black behind transparent PNGs
    ctx.fillRect(0, 0, width, height);
    ctx.drawImage(img, 0, 0, width, height);
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', JPEG_QUALITY));
    if (!blob) throw new UnsupportedImageError();
    const name = `${file.name.replace(/\.[^.]*$/, '') || 'photo'}.jpg`;
    return new File([blob], name, { type: 'image/jpeg' });
  } finally {
    URL.revokeObjectURL(url);
  }
}

/**
 * What to tell the person when a photo upload fails. A refusal by the server
 * names the step and code (e.g. "photo storage error 403 AccessDenied"), so a
 * screenshot from a devotee's phone is enough to tell an S3 permission problem
 * from a rate limit or a backend fault.
 */
export function photoUploadErrorMessage(err: unknown, notConfigured: string): string {
  if (err instanceof UnsupportedImageError) {
    return "This photo's format can't be opened on this device. Choose a JPG or PNG photo, or take a screenshot of it and upload that.";
  }
  if (!isAxiosError(err)) return 'Upload failed. Please try again, or choose a different photo.';
  if (!err.response) return 'Upload failed. Check your internet connection and try again.';
  const { status, data } = err.response;
  if ((err.config?.url ?? '').includes('.amazonaws.com')) {
    const code = typeof data === 'string' ? /<Code>([^<]+)<\/Code>/.exec(data)?.[1] : undefined;
    return `Upload failed (photo storage error ${status}${code ? ` ${code}` : ''}). You can still book without a photo.`;
  }
  if (status === 503) return notConfigured;
  const detail = data && typeof data === 'object' && 'detail' in data ? (data as { detail: unknown }).detail : null;
  if ((status === 400 || status === 429) && typeof detail === 'string') return detail;
  return `Upload failed (server error ${status}). Please try again, or choose a different photo.`;
}
