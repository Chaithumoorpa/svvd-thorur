'use client';

import { useEffect } from 'react';
import { trackVisit } from '@/lib/api';

export default function VisitorTracker() {
    useEffect(() => {
        // Only track once per session to avoid noise, 
        // although backend handles unique daily hits by IP.
        const hasTracked = sessionStorage.getItem('v_tracked');
        if (!hasTracked) {
            trackVisit().catch((err) => {
                // eslint-disable-next-line no-console
                console.error('Failed to track visit:', err);
            });
            sessionStorage.setItem('v_tracked', 'true');
        }
    }, []);

    return null;
}
