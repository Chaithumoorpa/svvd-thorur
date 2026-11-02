/** Sections the lobby TV (/tv) can show - keep in sync with TV_SECTIONS in backend/app/schemas/temple.py. */
export const TV_SECTIONS = [
  { key: 'welcome', label: 'Welcome', hint: 'Deity name, tagline and the blessing animation' },
  { key: 'timings', label: 'Darshan timings', hint: 'From Timings' },
  { key: 'poojas', label: 'Poojas & sevas', hint: 'Names and fees, from Poojas & Sevas' },
  { key: 'blessings', label: "Today's blessings", hint: 'Devotee blessings you have approved' },
  { key: 'festivals', label: 'Upcoming festivals', hint: 'From Festivals' },
  { key: 'announcements', label: 'Announcements', hint: 'From Announcements' },
  { key: 'gallery', label: 'Photo slideshow', hint: 'From Gallery' },
  { key: 'committee', label: 'Committee', hint: 'Members marked "show on website"' },
  { key: 'qr', label: 'QR codes panel', hint: 'Register, sign in and book a seva from a phone' },
  { key: 'ticker', label: 'Scrolling announcement ticker', hint: 'Along the bottom of the screen' },
] as const;

export type TvSectionKey = (typeof TV_SECTIONS)[number]['key'];
export const ALL_TV_SECTIONS: string[] = TV_SECTIONS.map((s) => s.key);
