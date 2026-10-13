import { expect, test } from '@playwright/test';

/**
 * End-to-end workflow against a real backend + Postgres (see
 * frontend/e2e/README.md for how this environment is stood up). Everything
 * here goes through the actual HTTP API and database - no mocking - so a
 * pass proves the full stack (browser -> Next.js -> FastAPI -> Postgres and
 * back) actually works, not just that each layer works in isolation.
 *
 * Credentials come from E2E_ADMIN_USERNAME/E2E_ADMIN_PASSWORD, seeded by
 * e2e/seed_admin.py into whatever database the running backend points at.
 */
const ADMIN_USERNAME = process.env.E2E_ADMIN_USERNAME || 'e2eadmin';
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || 'E2ePassword123';

test.describe.configure({ mode: 'serial' });

test('unauthenticated visitors are redirected away from the admin panel', async ({ page }) => {
  await page.goto('/admin/temple');
  await page.waitForURL('**/login');
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
});

test('complete admin workflow: sign in, edit content, see it live, sign out', async ({ page }) => {
  const stamp = Date.now();
  const tagline = `E2E verified tagline ${stamp}`;
  const announcementTitle = `E2E Test Announcement ${stamp}`;
  const announcementMessage = `This notice was created by an automated end-to-end test at ${stamp}.`;

  await test.step('sign in as the seeded admin (single-factor: no email on file)', async () => {
    await page.goto('/login');
    await page.locator('#username').fill(ADMIN_USERNAME);
    await page.locator('#password').fill(ADMIN_PASSWORD);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await page.waitForURL('**/admin');
    await expect(page.getByRole('heading', { name: `Namaste, ${ADMIN_USERNAME}` })).toBeVisible();
  });

  await test.step('edit Temple Info and save', async () => {
    await page.goto('/admin/temple');
    await page.getByLabel('Temple name').fill('SVVD Thorur E2E Temple'); // required field renders as "Temple name *"
    await page.getByLabel('Tagline').fill(tagline);
    await page.getByRole('button', { name: 'Save changes' }).click();
    await expect(page.getByText('Temple information saved.')).toBeVisible();
  });

  await test.step('the new tagline is actually live on the public site', async () => {
    // The public homepage's temple data is fetched with `next: { revalidate: 60 }`
    // (see lib/server-api.ts) - a deliberate cache to spare the DB, which means a
    // real visitor (and this test) can see the old value for up to a minute after
    // saving. Poll instead of asserting once, so the test reflects that honestly
    // rather than racing it.
    await expect(async () => {
      await page.goto('/', { waitUntil: 'domcontentloaded' });
      await expect(page.getByText(tagline)).toBeVisible();
    }).toPass({ timeout: 75_000, intervals: [5_000] });
  });

  await test.step('create an announcement in the admin panel', async () => {
    await page.goto('/admin/announcements');
    await page.getByRole('button', { name: 'New announcement' }).click();
    await page.getByLabel('Title').fill(announcementTitle); // required field renders as "Title *"
    await page.getByLabel('Message').fill(announcementMessage);
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page.getByText('Announcement published.')).toBeVisible();
    await expect(page.getByRole('heading', { name: announcementTitle })).toBeVisible();
  });

  await test.step('the new announcement is live on the public Announcements page', async () => {
    // Same 60s server-side fetch cache as the temple profile above.
    await expect(async () => {
      await page.goto('/announcements', { waitUntil: 'domcontentloaded' });
      await expect(page.getByRole('heading', { name: announcementTitle })).toBeVisible();
      await expect(page.getByText(announcementMessage)).toBeVisible();
    }).toPass({ timeout: 75_000, intervals: [5_000] });
  });

  await test.step('sign out ends the session', async () => {
    await page.goto('/admin');
    await page.getByRole('button', { name: 'Sign out' }).click();
    await page.waitForURL('http://127.0.0.1:3100/');

    await page.goto('/admin/temple');
    await page.waitForURL('**/login');
  });
});
