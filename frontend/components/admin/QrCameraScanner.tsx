'use client';

import React, { useEffect, useRef, useState } from 'react';
import jsQR from 'jsqr';
import { Camera, Keyboard } from 'lucide-react';
import { btnGhost } from '@/components/ui/styles';

/**
 * Live camera QR scanner for validating tickets at the temple counter from a
 * phone browser - no separate barcode-scanner hardware needed. Decodes frames
 * locally with jsQR (no image ever leaves the device). Calls onDetect once
 * per mount the first time a code is read; the parent decides what happens
 * next (usually: look the ticket up, show the result, remount to scan again).
 */
export default function QrCameraScanner({
  onDetect,
  onUseManualEntry,
}: {
  onDetect: (data: string) => void;
  onUseManualEntry: () => void;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const rafRef = useRef<number | null>(null);
  const detectedRef = useRef(false);
  const [error, setError] = useState('');
  const [starting, setStarting] = useState(true);

  useEffect(() => {
    let cancelled = false;

    function tick() {
      if (cancelled || detectedRef.current) return;
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (video && canvas && video.readyState === video.HAVE_ENOUGH_DATA) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          const frame = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const code = jsQR(frame.data, frame.width, frame.height);
          if (code?.data && !detectedRef.current) {
            detectedRef.current = true;
            onDetect(code.data);
            return;
          }
        }
      }
      rafRef.current = requestAnimationFrame(tick);
    }

    async function start() {
      if (!navigator.mediaDevices?.getUserMedia) {
        setError('Camera access is not supported in this browser. Enter the code manually instead.');
        setStarting(false);
        return;
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
        setStarting(false);
        tick();
      } catch {
        if (!cancelled) {
          setError('Could not access the camera. Check the browser’s camera permission, or enter the code manually.');
          setStarting(false);
        }
      }
    }

    start();

    return () => {
      cancelled = true;
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (error) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 p-6 text-center text-sm text-gray-600">
        <p>{error}</p>
        <button type="button" className={`${btnGhost} mt-3`} onClick={onUseManualEntry}>
          <Keyboard className="h-4 w-4" aria-hidden="true" /> Enter code manually
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="relative overflow-hidden rounded-lg bg-black" style={{ aspectRatio: '4 / 3' }}>
        <video ref={videoRef} className="h-full w-full object-cover" muted playsInline aria-hidden="true" />
        <canvas ref={canvasRef} className="hidden" />
        {starting && (
          <div className="absolute inset-0 flex items-center justify-center gap-2 text-sm text-white">
            <Camera className="h-4 w-4 animate-pulse" aria-hidden="true" /> Starting camera…
          </div>
        )}
        {!starting && <div className="pointer-events-none absolute inset-8 rounded-lg border-2 border-white/70" />}
      </div>
      <p className="text-center text-xs text-gray-500">Point the camera at the ticket&apos;s QR code.</p>
      <div className="text-center">
        <button type="button" className={btnGhost} onClick={onUseManualEntry}>
          <Keyboard className="h-4 w-4" aria-hidden="true" /> Enter code manually instead
        </button>
      </div>
    </div>
  );
}
