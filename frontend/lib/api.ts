import axios, { AxiosError } from 'axios';
import { prepareImageForUpload, reencodeAsJpeg } from './imageUpload';
import type {
  ActivityItem, Announcement, AnnouncementInput, AppUser, AssetCondition, AssetVerification, AuditLog, BlessingReview,
  BudgetStatus, CommitteeMember, ContactInput, ContactMessage, ContactStatus, CounterTicketInput, DashboardStats,
  Donation, DonationInput, Donor, DonorInput, Expense, ExpenseCategory, ExpenseInput, ExpenseStatus, Festival,
  FestivalCost, FestivalInput, FinanceSummary, InventoryItem, InventoryItemInput, InventorySummary, ItemKind,
  MovementType, PaymentMode, StockMovement, FinanceAnalytics, InventoryAnalytics, AuditAnalytics,
  GalleryInput, GalleryItem, HomePayload, HundiQrInfo, IncomeInput, LedgerEntry, Me, Member, MemberInput,
  Letter, LetterInput, LetterStatus, LetterTemplate, MySignature, SealStatus, SignatureStatus,
  Paged, PersonalBlessing, Pooja, PoojaInput, SevaBookingOnlineInput, SevaCalendarDay, SevaDay, SevaTicket,
  Temple, TempleTiming,
  TempleTimingInput, TempleUpdate, TicketStatus, UploadUrlResponse, UserCreateInput,
  UserUpdateInput, VisitorStats,
} from './types';

export * from './types';

/**
 * Browser calls go through the Next.js rewrite (/api/v1 -> backend). Server-side calls
 * (see lib/server-api.ts) talk to the backend directly.
 *
 * The session itself is an HttpOnly cookie the backend sets at sign-in: the browser
 * sends it with every /api/v1 request, and no JavaScript here can read it (so a script
 * injected into the page couldn't steal it either). X-Requested-With is required by
 * the backend on cookie-authenticated writes - another site can't add that header.
 */
export const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json', Accept: 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
});

// Not a secret - just "this browser signed in", so the public header can skip asking
// the server for anonymous visitors. The server's answer (getMe) is always the truth.
const SIGNED_IN_KEY = 'signedIn';

export function isProbablySignedIn(): boolean {
  try {
    return typeof window !== 'undefined' && window.localStorage.getItem(SIGNED_IN_KEY) === '1';
  } catch {
    return false;
  }
}

export function markSignedIn(signedIn: boolean): void {
  try {
    if (signedIn) window.localStorage.setItem(SIGNED_IN_KEY, '1');
    else window.localStorage.removeItem(SIGNED_IN_KEY);
  } catch {
    /* storage unavailable (private mode) - the header just checks with the server */
  }
}

if (typeof window !== 'undefined') {
  try {
    window.localStorage.removeItem('token'); // the old readable session token, from before cookies
  } catch {
    /* storage unavailable */
  }
}

/** Ends the session on every device (see POST /auth/logout). Never fails. */
export async function logout(): Promise<void> {
  markSignedIn(false);
  try {
    await api.post('/auth/logout');
  } catch {
    /* already signed out / offline - the cookie expires on its own */
  }
}

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const url = error.config?.url ?? '';
    // An expired/invalid session anywhere in the admin area sends the user back to sign in.
    if (error.response?.status === 401 && typeof window !== 'undefined' && !url.includes('/auth/login')) {
      markSignedIn(false);
      if (window.location.pathname.startsWith('/admin')) window.location.href = '/login';
    }
    return Promise.reject(error);
  },
);

// Sliding session: the cookie is short-lived (ACCESS_TOKEN_EXPIRE_MINUTES on the
// backend), but as long as the user is actually doing something, this silently renews
// it every so often - stop being active and it simply expires, and the next request's
// 401 signs them out via the interceptor above. Renewal never extends a session past
// SESSION_MAX_HOURS from sign-in (enforced by the backend). Module-scoped (not a React
// effect) so it covers the whole site with one set of listeners.
const REFRESH_MIN_INTERVAL_MS = 10 * 60 * 1000;
let lastRefreshAt = 0;

function refreshSessionOnActivity() {
  if (!isProbablySignedIn()) return;
  const now = Date.now();
  if (now - lastRefreshAt < REFRESH_MIN_INTERVAL_MS) return;
  lastRefreshAt = now;
  api.post('/auth/refresh').catch(() => {
    /* already expired/ended - the next real request 401s and signs out */
  });
}

if (typeof window !== 'undefined') {
  (['click', 'keydown', 'scroll', 'touchstart'] as const).forEach((evt) =>
    window.addEventListener(evt, refreshSessionOnActivity, { passive: true }),
  );
}

/** Human-readable message from any API failure (FastAPI `detail` string or validation list). */
export function apiError(error: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) return 'Cannot reach the server. Check your connection and try again.';
    const detail = (error.response.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail.length) {
      return detail
        .map((d: { loc?: unknown[]; msg?: string }) => {
          const field = Array.isArray(d.loc) ? String(d.loc[d.loc.length - 1]) : '';
          const msg = (d.msg ?? '').replace(/^Value error, /, '');
          return field && field !== 'body' ? `${field.replace(/_/g, ' ')}: ${msg}` : msg;
        })
        .join('; ');
    }
    if (error.response.status === 403) return 'You do not have permission to do this.';
    if (error.response.status === 429) return 'Too many requests. Please wait a moment.';
  }
  return fallback;
}

const total = (headers: Record<string, unknown>): number => Number(headers['x-total-count'] ?? 0);

async function page<T>(url: string, params?: Record<string, unknown>): Promise<Paged<T>> {
  const res = await api.get<T[]>(url, { params });
  return { items: res.data, total: total(res.headers as Record<string, unknown>) || res.data.length };
}

// ------------------------------------------------------------------------------ auth
/** Step 1: username + password. An account with an email on file gets back
 * otp_required: true (a sign-in code was just emailed) instead of a session -
 * call verifyLoginOtp next. An account with no email gets a session directly,
 * same as login always worked before two-factor existed. */
export async function login(username: string, password: string, turnstile_token?: string) {
  const { data } = await api.post<{ otp_required: boolean; must_change_password?: boolean }>(
    '/auth/login', { username, password, turnstile_token },
  );
  if (!data.otp_required) markSignedIn(true);
  return data;
}
/** Step 2, only when login() returned otp_required: true. */
export async function verifyLoginOtp(username: string, code: string) {
  const { data } = await api.post<{ must_change_password: boolean }>('/auth/login/verify-otp', { username, code });
  markSignedIn(true);
  return data;
}
export const forgotPassword = async (email: string, turnstile_token?: string) =>
  (await api.post<{ message: string }>('/auth/forgot-password', { email, turnstile_token })).data;
export const forgotUsername = async (identifier: string, turnstile_token?: string) =>
  (await api.post<{ message: string }>('/auth/forgot-username', { identifier, turnstile_token })).data;
export const resetPassword = async (token: string, new_password: string) =>
  (await api.post<{ message: string }>('/auth/reset-password', { token, new_password })).data;
/** Sign-up step 1: checks the details and emails a code - no account exists yet. */
export const requestRegisterCode = async (data: { username: string; email: string; phone: string; turnstile_token?: string }) =>
  (await api.post<{ message: string }>('/auth/register/request-code', data)).data;
/** Sign-up step 2: the emailed code proves the address; the account is created and signed in. */
export const register = async (data: {
  username: string; password: string; email: string; phone: string; accept_terms: boolean; email_code: string;
}) => { const user = (await api.post<AppUser>('/auth/register', data)).data; markSignedIn(true); return user; };
export const listUnverifiedSignups = async () => (await api.get<AppUser[]>('/auth/admin/users/unverified')).data;
export const purgeUnverifiedSignups = async () =>
  (await api.post<{ deleted: number }>('/auth/admin/users/purge-unverified')).data;
export const getMe = async () => (await api.get<Me>('/auth/verify')).data;
export const changePassword = async (current_password: string, new_password: string) =>
  (await api.post('/auth/change-password', { current_password, new_password })).data;
export const deleteMyAccount = async (password: string) =>
  (await api.delete('/auth/me', { data: { password } })).data;
export const listUsers = (p = 1, pageSize = 50) => page<AppUser>('/auth/admin/users', { page: p, page_size: pageSize });
export const createUser = async (data: UserCreateInput) => (await api.post<AppUser>('/auth/admin/users', data)).data;
export const updateUser = async (id: number, data: UserUpdateInput) =>
  (await api.patch<AppUser>(`/auth/admin/users/${id}`, data)).data;
export const deleteUser = async (id: number) => (await api.delete(`/auth/admin/users/${id}`)).data;

// ---------------------------------------------------------------------------- temple
export const getTemple = async () => (await api.get<Temple>('/temple/')).data;
export const updateTemple = async (data: TempleUpdate) => (await api.put<Temple>('/temple/', data)).data;
export const listAllTimings = async () => (await api.get<TempleTiming[]>('/temple/timings/all')).data;
export const getHundiQr = async () => (await api.get<HundiQrInfo>('/temple/hundi-qr')).data;
export const createTiming = async (data: TempleTimingInput) => (await api.post<TempleTiming>('/temple/timings', data)).data;
export const updateTiming = async (id: number, data: Partial<TempleTimingInput>) =>
  (await api.put<TempleTiming>(`/temple/timings/${id}`, data)).data;
export const deleteTiming = async (id: number) => (await api.delete<TempleTiming>(`/temple/timings/${id}`)).data;

// ------------------------------------------------------------------------ public data
export const getHome = async () => (await api.get<HomePayload>('/public/home')).data;
export const getCommittee = async () => (await api.get<CommitteeMember[]>('/public/committee')).data;
export const trackVisit = async () => (await api.post('/stats/track')).data;
export const getVisitorStats = async () => (await api.get<VisitorStats>('/stats/stats')).data;
export const submitContact = async (data: ContactInput) =>
  (await api.post<{ id: number; status: ContactStatus }>('/contacts/', data)).data;
export const requestBookingOtp = async (email: string) =>
  (await api.post<{ message: string }>('/seva-tickets/booking/request-otp', { email })).data;
export const verifyBookingOtp = async (email: string, code: string) =>
  (await api.post<{ booking_token: string }>('/seva-tickets/booking/verify-otp', { email, code })).data;
export const bookSeva = async (data: SevaBookingOnlineInput) => (await api.post<SevaTicket>('/seva-tickets/', data)).data;

// ------------------------------------------------------------ seva calendar & blessings
/** Every day from `start` to `end` (YYYY-MM-DD, inclusive) with the seva's
 * bookings - the rolling contribution-style grid. Public, briefly cached. */
export const getSevaCalendar = async (poojaId: number, start: string, end: string) =>
  (await api.get<SevaCalendarDay[]>(`/poojas/${poojaId}/calendar`, { params: { start, end } })).data;
/** One day: the calendar pop-up, and that date's public blessings page. */
export const getSevaDay = async (poojaId: number, date: string) =>
  (await api.get<SevaDay>(`/poojas/${poojaId}/calendar/${date}`)).data;
/** The devotee's own blessing page (linked from their greeting email). */
export const getPersonalBlessing = async (ticketId: string) =>
  (await api.get<PersonalBlessing>(`/seva-tickets/${ticketId}/blessing`)).data;

/** Presigned S3 POST upload of an already-prepared photo via `endpoint`. */
async function uploadPhoto(endpoint: string, photo: File): Promise<UploadUrlResponse> {
  const { data } = await api.post<UploadUrlResponse>(endpoint, { content_type: photo.type });
  const form = new FormData();
  Object.entries(data.fields).forEach(([key, value]) => form.append(key, value));
  form.append('file', photo);
  // Plain axios, not the `api` instance: it must not carry a bearer token to S3.
  await axios.post(data.upload_url, form);
  return data;
}

/** Uploads a devotee's occasion photo straight to S3 (presigned POST, public
 * but rate limited - nobody is signed in while booking). The object is
 * private: it reaches the website only once staff approve it. Always
 * re-encoded first (strips EXIF/GPS, since it may be published); returns the
 * stored key and that re-encoded photo, which is what the form should preview.
 * Throws UnsupportedImageError if this browser can't read the file. */
export async function uploadBlessingPhoto(file: File): Promise<{ key: string; photo: File }> {
  const photo = await reencodeAsJpeg(file);
  return { key: (await uploadPhoto('/seva-tickets/booking/upload-url', photo)).key, photo };
}

// -------------------------------------------------------------------- announcements
export const getAnnouncements = async () => (await api.get<Announcement[]>('/announcements/')).data;
export const listAllAnnouncements = (p = 1, pageSize = 50) =>
  page<Announcement>('/announcements/admin/all', { page: p, page_size: pageSize });
export const createAnnouncement = async (data: AnnouncementInput) =>
  (await api.post<Announcement>('/announcements/', data)).data;
export const updateAnnouncement = async (id: number, data: AnnouncementInput) =>
  (await api.put<Announcement>(`/announcements/${id}`, data)).data;
export const deleteAnnouncement = async (id: number) => (await api.delete<Announcement>(`/announcements/${id}`)).data;

// ---------------------------------------------------------------------------- festivals
export const getFestivals = async (upcoming = false) =>
  (await api.get<Festival[]>('/festivals/', { params: { upcoming } })).data;
export const listAllFestivals = (p = 1, pageSize = 50) => page<Festival>('/festivals/admin/all', { page: p, page_size: pageSize });
export const createFestival = async (data: FestivalInput) => (await api.post<Festival>('/festivals/', data)).data;
/** Adds the computed festivals for the next 12 months that aren't there yet (the daily cron job does the same). */
export const fillFestivalCalendar = async () => (await api.post<{ added: number }>('/festivals/calendar/fill')).data;
export const updateFestival = async (id: number, data: Partial<FestivalInput>) =>
  (await api.put<Festival>(`/festivals/${id}`, data)).data;
export const deleteFestival = async (id: number) => (await api.delete<Festival>(`/festivals/${id}`)).data;

// -------------------------------------------------------------------------------- poojas
export const getPoojas = async () => (await api.get<Pooja[]>('/poojas/')).data;
export const listAllPoojas = (p = 1, pageSize = 100) => page<Pooja>('/poojas/admin/all', { page: p, page_size: pageSize });
export const createPooja = async (data: PoojaInput) => (await api.post<Pooja>('/poojas/', data)).data;
export const updatePooja = async (id: number, data: Partial<PoojaInput>) => (await api.put<Pooja>(`/poojas/${id}`, data)).data;
export const deletePooja = async (id: number) => (await api.delete<Pooja>(`/poojas/${id}`)).data;

// ------------------------------------------------------------------------------- gallery
export const getGallery = async (category?: string) =>
  (await api.get<GalleryItem[]>('/gallery/', { params: { category, page_size: 200 } })).data;
export const listAllGallery = (p = 1, pageSize = 100) => page<GalleryItem>('/gallery/admin/all', { page: p, page_size: pageSize });
export const createGallery = async (data: GalleryInput) => (await api.post<GalleryItem>('/gallery/', data)).data;
export const updateGallery = async (id: number, data: Partial<GalleryInput>) =>
  (await api.put<GalleryItem>(`/gallery/${id}`, data)).data;
export const deleteGallery = async (id: number) => (await api.delete<GalleryItem>(`/gallery/${id}`)).data;

/** Uploads a gallery photo straight to S3 (presigned POST) and returns its public URL. */
export async function uploadGalleryPhoto(file: File): Promise<string> {
  return (await uploadPhoto('/gallery/upload-url', await prepareImageForUpload(file))).public_url;
}

// ------------------------------------------------------------------------------- members
export const listMembers = (p = 1, pageSize = 100) => page<Member>('/temple-members/', { page: p, page_size: pageSize });
export const createMember = async (data: MemberInput) => (await api.post<Member>('/temple-members/', data)).data;
export const updateMember = async (id: number, data: Partial<MemberInput>) =>
  (await api.put<Member>(`/temple-members/${id}`, data)).data;
export const deleteMember = async (id: number) => (await api.delete<Member>(`/temple-members/${id}`)).data;

/** Uploads a member's photo straight to S3 (presigned POST) and returns its public URL. */
export async function uploadMemberPhoto(file: File): Promise<string> {
  return (await uploadPhoto('/temple-members/upload-url', await prepareImageForUpload(file))).public_url;
}

// ------------------------------------------------------------------- donors & donations
export const listDonors = (p = 1, search?: string, pageSize = 25) =>
  page<Donor>('/donors/', { page: p, page_size: pageSize, search: search || undefined });
export const createDonor = async (data: DonorInput) => (await api.post<Donor>('/donors/', data)).data;
export const updateDonor = async (id: number, data: Partial<DonorInput> & { is_active?: boolean }) =>
  (await api.put<Donor>(`/donors/${id}`, data)).data;
export const deleteDonor = async (id: number) => (await api.delete<Donor>(`/donors/${id}`)).data;
export const listDonations = (p = 1, filters: { donor_id?: number; start_date?: string; end_date?: string } = {}, pageSize = 25) =>
  page<Donation>('/donations/', { page: p, page_size: pageSize, ...filters });
export const createDonation = async (data: DonationInput) => (await api.post<Donation>('/donations/', data)).data;
export const deleteDonation = async (id: number) => (await api.delete<{ message: string }>(`/donations/${id}`)).data;
export const issueReceipt = async (id: number) => (await api.post<Donation>(`/donations/${id}/receipt`)).data;
export const downloadReceipt = async (id: number) =>
  (await api.get<Blob>(`/donations/${id}/receipt`, { responseType: 'blob' })).data;

// ------------------------------------------------------------------------------ messages
export const listMessages = (p = 1, status?: ContactStatus, pageSize = 25) =>
  page<ContactMessage>('/contacts/', { page: p, page_size: pageSize, status });
export const updateMessage = async (id: number, data: { status?: ContactStatus; admin_notes?: string }) =>
  (await api.patch<ContactMessage>(`/contacts/${id}`, data)).data;
export const deleteMessage = async (id: number) => (await api.delete(`/contacts/${id}`)).data;

// -------------------------------------------------------------------------- seva tickets
export const listTickets = (p = 1, filters: { seva_date?: string; status?: TicketStatus; mobile?: string } = {}, pageSize = 25) =>
  page<SevaTicket>('/seva-tickets/', { page: p, page_size: pageSize, ...filters });
export const createCounterTicket = async (data: CounterTicketInput) =>
  (await api.post<SevaTicket>('/seva-tickets/admin', data)).data;
export const scanTicket = async (qr_token: string) =>
  (await api.post<{ success: boolean; message: string; ticket: SevaTicket | null }>('/seva-tickets/scan', { qr_token })).data;
export const downloadTicketPdf = async (id: string) =>
  (await api.get<Blob>(`/seva-tickets/${id}/pdf`, { params: { action: 'download' }, responseType: 'blob' })).data;
export const deleteTicket = async (id: string) => (await api.delete(`/seva-tickets/${id}`)).data;
export const getMyTickets = async () => (await api.get<SevaTicket[]>('/seva-tickets/mine')).data;
export const collectPayment = async (id: string) => (await api.post<SevaTicket>(`/seva-tickets/${id}/collect-payment`)).data;
export const getBlessingReviews = async () => (await api.get<BlessingReview[]>('/seva-tickets/blessing-reviews')).data;
/** Approve: publish the photo / show the blessing. Reject: delete the photo, keep the booking private. */
export const reviewBlessing = async (id: string, approve: boolean) =>
  (await api.post<SevaTicket>(`/seva-tickets/${id}/blessing-review`, { approve })).data;

// ------------------------------------------------------------------------------ finance
export const getFinanceSummary = async () => (await api.get<FinanceSummary>('/finance/summary')).data;
export const getLedger = (p = 1, startDate?: string, endDate?: string, pageSize = 25) =>
  page<LedgerEntry>('/finance/ledger', { page: p, page_size: pageSize, start_date: startDate || undefined, end_date: endDate || undefined });
export const addIncome = async (data: IncomeInput) => (await api.post('/finance/income', data)).data;

// ----------------------------------------------------------------------------- expenses
export interface ExpenseFilters {
  status?: ExpenseStatus; category?: ExpenseCategory; start_date?: string; end_date?: string;
  festival_id?: number; mine?: boolean; q?: string;
}
export const listExpenses = (p = 1, filters: ExpenseFilters = {}, pageSize = 25) =>
  page<Expense>('/finance/expenses', { page: p, page_size: pageSize, ...filters });
export const createExpense = async (data: ExpenseInput) => (await api.post<Expense>('/finance/expenses', data)).data;
export const updateExpense = async (id: string, data: Partial<ExpenseInput> & { reason?: string | null }) =>
  (await api.patch<Expense>(`/finance/expenses/${id}`, data)).data;
export const approveExpense = async (id: string) => (await api.post<Expense>(`/finance/expenses/${id}/approve`)).data;
export const rejectExpense = async (id: string, reason: string) =>
  (await api.post<Expense>(`/finance/expenses/${id}/reject`, { reason })).data;
export const voidExpense = async (id: string, reason: string) =>
  (await api.post<Expense>(`/finance/expenses/${id}/void`, { reason })).data;
export const getExpenseBill = async (id: string) =>
  (await api.get<{ url: string; content_type: string }>(`/finance/expenses/${id}/bill`)).data;
export const getBudgetStatus = async (month: string) =>
  (await api.get<BudgetStatus>('/finance/budgets', { params: { month } })).data;
export const setBudgets = async (month: string, lines: Array<{ category: ExpenseCategory; amount: number }>) =>
  (await api.put<BudgetStatus>(`/finance/budgets/${month}`, { lines })).data;
export const copyBudgets = async (month: string, fromMonth: string) =>
  (await api.post<BudgetStatus>(`/finance/budgets/${month}/copy-from/${fromMonth}`)).data;

/** A bill photo is shrunk and stripped of EXIF like any photo; a PDF goes up as is. */
export async function uploadExpenseBill(file: File): Promise<string> {
  const prepared = file.type === 'application/pdf' ? file : await prepareImageForUpload(file);
  return (await uploadPhoto('/finance/expenses/bill-upload-url', prepared)).key;
}

// ---------------------------------------------------------------------------- inventory
export const getInventorySummary = async () => (await api.get<InventorySummary>('/inventory/summary')).data;
export const listInventoryItems = async (filters: { kind?: ItemKind; low_stock?: boolean; q?: string; include_inactive?: boolean } = {}) =>
  (await api.get<InventoryItem[]>('/inventory/items', { params: filters })).data;
export const listInventoryCategories = async () => (await api.get<string[]>('/inventory/categories')).data;
export const createInventoryItem = async (data: InventoryItemInput) =>
  (await api.post<InventoryItem>('/inventory/items', data)).data;
export const updateInventoryItem = async (id: number, data: InventoryItemInput) =>
  (await api.patch<InventoryItem>(`/inventory/items/${id}`, data)).data;
export const deleteInventoryItem = async (id: number) => (await api.delete(`/inventory/items/${id}`)).data;
export const getInventoryPhoto = async (id: number) => (await api.get<{ url: string }>(`/inventory/items/${id}/photo`)).data;
export async function uploadInventoryPhoto(file: File): Promise<string> {
  return (await uploadPhoto('/inventory/items/photo-upload-url', await prepareImageForUpload(file))).key;
}
export const listStockMovements = (p = 1, filters: { item_id?: number; type?: MovementType; festival_id?: number } = {}, pageSize = 25) =>
  page<StockMovement>('/inventory/movements', { page: p, page_size: pageSize, ...filters });
export const recordPurchase = async (data: {
  item_id: number; quantity: string; total_cost: string; vendor: string; payment_mode: PaymentMode;
  movement_date: string; notes?: string | null; bill_key?: string | null; expense_category?: ExpenseCategory | null;
}) => (await api.post<StockMovement>('/inventory/purchases', data)).data;
export const recordDonationInKind = async (data: {
  item_id: number; quantity: string; donor_name: string; donor_phone?: string | null; donor_address?: string | null;
  estimated_value?: string | null; movement_date: string; notes?: string | null;
}) => (await api.post<StockMovement>('/inventory/donations-in', data)).data;
export const recordUsage = async (data: {
  item_id: number; quantity: string; movement_date: string; pooja_id?: number | null; festival_id?: number | null;
  notes?: string | null;
}) => (await api.post<StockMovement>('/inventory/usage', data)).data;
export const recordAdjustment = async (data: {
  item_id: number; counted_quantity: string; reason: string; movement_date: string; notes?: string | null;
}) => (await api.post<StockMovement>('/inventory/adjustments', data)).data;
export const recordWriteOff = async (data: {
  item_id: number; quantity: string; reason: string; movement_date: string; notes?: string | null;
}) => (await api.post<StockMovement>('/inventory/write-offs', data)).data;
export const downloadInKindReceipt = async (movementId: number) =>
  (await api.get<Blob>(`/inventory/movements/${movementId}/receipt`, { responseType: 'blob' })).data;
export const verifyAsset = async (itemId: number, data: {
  verified_on: string; condition: AssetCondition; weight_grams?: string | null; notes?: string | null;
}) => (await api.post<AssetVerification>(`/inventory/items/${itemId}/verifications`, data)).data;
export const listAssetVerifications = async (itemId: number) =>
  (await api.get<AssetVerification[]>(`/inventory/items/${itemId}/verifications`)).data;
export const getFestivalCosts = async () => (await api.get<FestivalCost[]>('/inventory/festival-costs')).data;
export const exportLedger = async (kind: 'csv' | 'pdf', startDate: string, endDate: string) =>
  (await api.get<Blob>(`/finance/ledger/${kind}`, { params: { start_date: startDate, end_date: endDate }, responseType: 'blob' })).data;
export const getMonthlyReportPdf = async (year: number, month: number) =>
  (await api.get<Blob>('/finance/reports/monthly/pdf', { params: { year, month }, responseType: 'blob' })).data;

// ---------------------------------------------------------------------------- analytics
export const getFinanceAnalytics = async (months: number) =>
  (await api.get<FinanceAnalytics>('/analytics/finance', { params: { months } })).data;
export const getInventoryAnalytics = async (months: number) =>
  (await api.get<InventoryAnalytics>('/analytics/inventory', { params: { months } })).data;
export const getAuditAnalytics = async (days: number) =>
  (await api.get<AuditAnalytics>('/analytics/audit', { params: { days } })).data;

// ---------------------------------------------------------------------------- official letters
/** A signature/seal photo goes to the server as a data URL: re-drawn as a JPEG first (any
 * format the browser can open, at most 2048 px, no EXIF), then cleaned server-side into a
 * transparent mark. */
export async function imageAsDataUrl(file: File): Promise<string> {
  const jpeg = await reencodeAsJpeg(file);
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(jpeg);
  });
}
export const listLetters = (p = 1, filters: { status?: LetterStatus; q?: string } = {}, pageSize = 25) =>
  page<Letter>('/letters', { page: p, page_size: pageSize, ...filters });
export const getLetter = async (id: number) => (await api.get<Letter>(`/letters/${id}`)).data;
export const getLetterTemplates = async () => (await api.get<LetterTemplate[]>('/letters/templates')).data;
export const createLetter = async (data: LetterInput) => (await api.post<Letter>('/letters', data)).data;
export const updateLetter = async (id: number, data: LetterInput) => (await api.put<Letter>(`/letters/${id}`, data)).data;
export const deleteLetter = async (id: number) => (await api.delete(`/letters/${id}`)).data;
export const letterAction = async (id: number, action: 'send' | 'recall' | 'issue') =>
  (await api.post<Letter>(`/letters/${id}/${action}`)).data;
export const revokeLetter = async (id: number, reason: string) =>
  (await api.post<Letter>(`/letters/${id}/revoke`, { reason })).data;
export const markSignatoryInk = async (id: number, signatoryId: number) =>
  (await api.post<Letter>(`/letters/${id}/signatories/${signatoryId}/paper`)).data;
export const signLetter = async (id: number, password: string) =>
  (await api.post<Letter>(`/letters/${id}/sign`, { password })).data;
export const declineLetter = async (id: number, reason: string) =>
  (await api.post<Letter>(`/letters/${id}/decline`, { reason })).data;
export const getLetterPdf = async (id: number) =>
  (await api.get<Blob>(`/letters/${id}/pdf`, { responseType: 'blob' })).data;
export const getMySignature = async () => (await api.get<MySignature>('/letters/mine')).data;
export const uploadMySignature = async (file: File) =>
  (await api.put<MySignature>('/letters/mine/signature', { image: await imageAsDataUrl(file) })).data;
export const getMySignatureImage = async () =>
  (await api.get<Blob>('/letters/mine/signature.png', { responseType: 'blob' })).data;
export const listSignatures = async () => (await api.get<SignatureStatus[]>('/letters/signatures')).data;
export const uploadSignature = async (memberId: number, file: File) =>
  (await api.put<SignatureStatus>(`/letters/signatures/${memberId}`, { image: await imageAsDataUrl(file) })).data;
/** Super Admin: which login signs letters as this member (null unlinks). */
export const linkMemberLogin = async (memberId: number, userId: number | null) =>
  (await api.put<SignatureStatus>(`/letters/signatures/${memberId}/login`, { user_id: userId })).data;
export const removeSignature = async (memberId: number) => (await api.delete(`/letters/signatures/${memberId}`)).data;
export const getSignatureImage = async (memberId: number) =>
  (await api.get<Blob>(`/letters/signatures/${memberId}.png`, { responseType: 'blob' })).data;
export const getSeal = async () => (await api.get<SealStatus>('/letters/seal')).data;
export const uploadSeal = async (file: File) =>
  (await api.put<SealStatus>('/letters/seal', { image: await imageAsDataUrl(file) })).data;
export const removeSeal = async () => (await api.delete('/letters/seal')).data;
export const getSealImage = async () => (await api.get<Blob>('/letters/seal.png', { responseType: 'blob' })).data;

// ---------------------------------------------------------------------------- dashboard
export const getDashboardStats = async () => (await api.get<DashboardStats>('/meta/stats')).data;
export const getRecentActivity = async () => (await api.get<ActivityItem[]>('/meta/activity')).data;
export const listAuditLogs = (p = 1, filters: { entity_type?: string; action?: string } = {}, pageSize = 50) =>
  page<AuditLog>('/audit-logs/', { page: p, page_size: pageSize, ...filters });

/** Show a PDF (or any blob) in a new tab. The tab is opened during the click, before the
 * download finishes, so pop-up blockers allow it. */
export async function openBlobInNewTab(load: () => Promise<Blob>): Promise<void> {
  const tab = window.open('', '_blank');
  try {
    const url = URL.createObjectURL(await load());
    if (tab) tab.location.href = url;
    else window.location.href = url;
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  } catch (err) {
    tab?.close();
    throw err;
  }
}

/** Save a Blob response as a file download. */
export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
