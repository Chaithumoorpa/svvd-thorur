import axios, { AxiosError } from 'axios';
import type {
  ActivityItem, Announcement, AnnouncementInput, AppUser, AuditLog, CommitteeMember,
  ContactInput, ContactMessage, ContactStatus, CounterTicketInput, DashboardStats, Donation,
  DonationInput, Donor, DonorInput, ExpenseInput, Festival, FestivalInput, FinanceSummary,
  GalleryInput, GalleryItem, HomePayload, IncomeInput, LedgerEntry, Me, Member, MemberInput,
  Paged, Pooja, PoojaInput, SevaBookingInput, SevaTicket, Temple, TempleTiming,
  TempleTimingInput, TempleUpdate, TicketStatus, UserCreateInput, UserUpdateInput, VisitorStats,
} from './types';

export * from './types';

/**
 * Browser calls go through the Next.js rewrite (/api/v1 -> backend). Server-side calls
 * (see lib/server-api.ts) talk to the backend directly.
 */
export const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
});

const TOKEN_KEY = 'token';

export function getStoredToken(): string | null {
  try {
    return typeof window === 'undefined' ? null : window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string | null): void {
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token);
    else window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable (private mode) - session simply will not persist */
  }
}

api.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const url = error.config?.url ?? '';
    // An expired/invalid session anywhere in the admin area sends the user back to sign in.
    if (error.response?.status === 401 && typeof window !== 'undefined' && !url.includes('/auth/login')) {
      setStoredToken(null);
      if (window.location.pathname.startsWith('/admin')) window.location.href = '/login';
    }
    return Promise.reject(error);
  },
);

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
export const login = async (username: string, password: string) =>
  (await api.post<{ access_token: string; must_change_password: boolean }>('/auth/login', { username, password })).data;
export const register = async (data: { username: string; password: string; email?: string }) =>
  (await api.post<AppUser>('/auth/register', data)).data;
export const getMe = async () => (await api.get<Me>('/auth/verify')).data;
export const changePassword = async (current_password: string, new_password: string) =>
  (await api.post('/auth/change-password', { current_password, new_password })).data;
export const listUsers = (p = 1, pageSize = 50) => page<AppUser>('/auth/admin/users', { page: p, page_size: pageSize });
export const createUser = async (data: UserCreateInput) => (await api.post<AppUser>('/auth/admin/users', data)).data;
export const updateUser = async (id: number, data: UserUpdateInput) =>
  (await api.patch<AppUser>(`/auth/admin/users/${id}`, data)).data;

// ---------------------------------------------------------------------------- temple
export const getTemple = async () => (await api.get<Temple>('/temple/')).data;
export const updateTemple = async (data: TempleUpdate) => (await api.put<Temple>('/temple/', data)).data;
export const listAllTimings = async () => (await api.get<TempleTiming[]>('/temple/timings/all')).data;
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
export const bookSeva = async (data: SevaBookingInput) => (await api.post<SevaTicket>('/seva-tickets/', data)).data;

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

// ------------------------------------------------------------------------------- members
export const listMembers = (p = 1, pageSize = 100) => page<Member>('/temple-members/', { page: p, page_size: pageSize });
export const createMember = async (data: MemberInput) => (await api.post<Member>('/temple-members/', data)).data;
export const updateMember = async (id: number, data: Partial<MemberInput>) =>
  (await api.put<Member>(`/temple-members/${id}`, data)).data;
export const deleteMember = async (id: number) => (await api.delete<Member>(`/temple-members/${id}`)).data;

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

// ------------------------------------------------------------------------------ finance
export const getFinanceSummary = async () => (await api.get<FinanceSummary>('/finance/summary')).data;
export const getLedger = (p = 1, startDate?: string, endDate?: string, pageSize = 25) =>
  page<LedgerEntry>('/finance/ledger', { page: p, page_size: pageSize, start_date: startDate || undefined, end_date: endDate || undefined });
export const addIncome = async (data: IncomeInput) => (await api.post('/finance/income', data)).data;
export const addExpense = async (data: ExpenseInput) => (await api.post('/finance/expense', data)).data;
export const exportLedger = async (kind: 'csv' | 'pdf', startDate: string, endDate: string) =>
  (await api.get<Blob>(`/finance/ledger/${kind}`, { params: { start_date: startDate, end_date: endDate }, responseType: 'blob' })).data;
export const getMonthlyReportPdf = async (year: number, month: number) =>
  (await api.get<Blob>('/finance/reports/monthly/pdf', { params: { year, month }, responseType: 'blob' })).data;

// ---------------------------------------------------------------------------- dashboard
export const getDashboardStats = async () => (await api.get<DashboardStats>('/meta/stats')).data;
export const getRecentActivity = async () => (await api.get<ActivityItem[]>('/meta/activity')).data;
export const listAuditLogs = (p = 1, filters: { entity_type?: string; action?: string } = {}, pageSize = 50) =>
  page<AuditLog>('/audit-logs/', { page: p, page_size: pageSize, ...filters });

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
