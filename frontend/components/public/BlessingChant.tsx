'use client';

import { useEffect, useRef, useState } from 'react';
import { Pause, Play } from 'lucide-react';

/**
 * The temple's own Veda Ashirvachanam recording. Served from frontend/public,
 * so adding or replacing the file is all it takes. Until it exists, this
 * component renders nothing.
 */
export const CHANT_SRC = '/audio/veda-ashirvachanam.mp3';

// Browsers only let audio start after a real tap, click or key press - a
// pointerdown from a touch screen doesn't count, so listen for these.
const ACTIVATION_EVENTS = ['click', 'touchend', 'keydown'] as const;

type State = 'loading' | 'waiting' | 'playing' | 'paused' | 'unavailable';

/**
 * Plays the blessing chant once when the page opens. Browsers (and every
 * iPhone) block sound until the visitor interacts with the page, so if
 * autoplay is refused it starts on their first tap anywhere instead, and the
 * button lets them start, pause or replay it at any time.
 */
export default function BlessingChant({ src = CHANT_SRC }: { src?: string }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [state, setState] = useState<State>('loading');

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    let active = true;
    const stopWaiting = () => ACTIVATION_EVENTS.forEach((e) => document.removeEventListener(e, onFirstInteraction));
    function onFirstInteraction() {
      stopWaiting();
      audio?.play().catch(() => undefined);
    }
    // The file may have already failed to load before React attached onError.
    if (audio.error) {
      setState('unavailable');
      return;
    }
    audio.play().catch((err: DOMException) => {
      if (!active) return;
      if (err.name !== 'NotAllowedError') {
        setState('unavailable'); // missing or unplayable file
        return;
      }
      setState((s) => (s === 'unavailable' ? s : 'waiting'));
      ACTIVATION_EVENTS.forEach((e) => document.addEventListener(e, onFirstInteraction));
    });
    return () => {
      active = false;
      stopWaiting();
      audio.pause();
    };
  }, []);

  const toggle = (e: React.MouseEvent) => {
    e.stopPropagation(); // this click is the toggle, not the page-wide "first tap"
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) audio.play().catch(() => undefined);
    else audio.pause();
  };

  return (
    <div className={state === 'unavailable' ? 'hidden' : 'mt-4 flex flex-col items-center gap-1'}>
      <audio
        ref={audioRef}
        src={src}
        preload="auto"
        onPlay={() => setState('playing')}
        onPause={() => setState('paused')}
        onEnded={() => setState('paused')}
        onError={() => setState('unavailable')}
      />
      {state !== 'unavailable' && (
        <>
          <button
            type="button"
            onClick={toggle}
            className="inline-flex items-center gap-2 rounded-full border border-amber-300 bg-amber-50 px-4 py-1.5 text-sm text-maroon hover:bg-amber-100"
          >
            {state === 'playing'
              ? <><Pause className="h-4 w-4" aria-hidden="true" /> Pause Veda Ashirvachanam</>
              : <><Play className="h-4 w-4" aria-hidden="true" /> Play Veda Ashirvachanam</>}
          </button>
          {state === 'waiting' && <p className="text-xs text-gray-500">Tap anywhere to hear the blessing chant.</p>}
        </>
      )}
    </div>
  );
}
