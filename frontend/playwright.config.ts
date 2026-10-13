import { defineConfig, devices } from '@playwright/test';

// This sandbox pre-installs Chromium for Playwright at a fixed path instead
// of letting `npx playwright install` fetch one - point every browser
// launch at it directly so a version mismatch with @playwright/test never
// triggers a download attempt.
const CHROMIUM_PATH = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';

export default defineConfig({
  testDir: './e2e',
  timeout: 240_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://127.0.0.1:3100',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], launchOptions: { executablePath: CHROMIUM_PATH } },
    },
  ],
});
