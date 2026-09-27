import type { MetadataRoute } from 'next';

/** Lets Android/Chrome "Add to home screen" use the temple logo and colours.
 * (Browser-tab and iPhone icons come from app/favicon.ico, app/icon.png and
 * app/apple-icon.png, which Next.js links automatically.) */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Sri Varasidhi Vinayaka Swamy Temple, Thorur',
    short_name: 'SVVD Thorur',
    start_url: '/',
    display: 'standalone',
    background_color: '#fbf6ec',
    theme_color: '#7a1c1c',
    icons: [
      { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
      { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
    ],
  };
}
