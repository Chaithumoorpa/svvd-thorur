import axios from 'axios';

const baseURL = typeof window === 'undefined'
  ? (process.env.INTERNAL_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://backend:8000/api/v1')
  : (process.env.NEXT_PUBLIC_API_BASE_URL && !process.env.NEXT_PUBLIC_API_BASE_URL.includes('backend')
    ? process.env.NEXT_PUBLIC_API_BASE_URL
    : '/api/v1');

if (!baseURL && typeof window === 'undefined') {
  // eslint-disable-next-line no-console
  console.error('Missing API base URL environment variable');
}

export const api = axios.create({
  baseURL: baseURL || undefined,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Add request interceptor to add token to headers
api.interceptors.request.use(
  (config) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token and redirect to login if unauthorized
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        // Only redirect if not already on the login page
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// If running in the browser and the baseURL uses the Docker service name
// (e.g. contains "backend:"), warn the developer because the browser cannot
// resolve Docker service hostnames — the browser must use a host-accessible
// address like http://localhost:8000.
if (typeof window !== 'undefined' && baseURL && baseURL.includes('backend')) {
  // eslint-disable-next-line no-console
  console.warn(
    `NEXT_PUBLIC_API_BASE_URL (${baseURL}) appears to use a Docker service name. ` +
    'Browser requests cannot resolve Docker service hostnames — use localhost or a public hostname instead.'
  );
}



export interface Festival {
  id: number;
  name: string;
  description?: string;
  date?: string;
  is_active: boolean;
}

export interface FestivalCreate {
  name: string;
  description?: string;
  date?: string;
}

export async function getFestivals() {
  const res = await api.get<Festival[]>('/festivals/');
  return res.data;
}

export async function createFestival(data: FestivalCreate) {
  const res = await api.post<Festival>('/festivals/', data);
  return res.data;
}

export async function updateFestival(id: number, data: Partial<FestivalCreate> & { is_active?: boolean }) {
  const res = await api.put<Festival>(`/festivals/${id}`, data);
  return res.data;
}

export async function deleteFestival(id: number) {
  const res = await api.delete<Festival>(`/festivals/${id}`);
  return res.data;
}

export async function getAnnouncements() {
  const res = await api.get('/announcements');
  return res.data;
}

// Poojas API
export interface Pooja {
  id: number;
  name: string;
  description?: string;
  start_time?: string;
  end_time?: string;
  pooja_type: string;
  is_paid: boolean;
  suggested_amount?: number;
  is_active: boolean;
}

export interface PoojaCreate {
  name: string;
  description?: string;
  start_time?: string;
  end_time?: string;
  pooja_type?: string;
  is_paid?: boolean;
  suggested_amount?: number;
}

export interface PoojaUpdate {
  name?: string;
  description?: string;
  start_time?: string;
  end_time?: string;
  pooja_type?: string;
  is_paid?: boolean;
  suggested_amount?: number;
  is_active?: boolean;
}

export async function getPoojas() {
  // Assuming list_active_poojas returns list, admin might need all. 
  // If backend filters by active=True, admin might treat hidden ones as deleted for now.
  // Or we update backend to show all for admin. 
  // For now, let's use the standard list endpoint.
  const res = await api.get<Pooja[]>('/poojas/');
  return res.data;
}

export async function createPooja(data: PoojaCreate) {
  const res = await api.post<Pooja>('/poojas/', data);
  return res.data;
}

export async function updatePooja(id: number, data: PoojaUpdate) {
  const res = await api.put<Pooja>(`/poojas/${id}`, data);
  return res.data;
}

export async function deletePooja(id: number) {
  const res = await api.delete<Pooja>(`/poojas/${id}`);
  return res.data;
}

// Gallery API
export interface Gallery {
  id: number;
  title: string;
  description?: string;
  image_url: string;
  category: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface GalleryCreate {
  title: string;
  description?: string;
  image_url: string;
  category: string;
  is_active?: boolean;
}

export interface GalleryUpdate {
  title?: string;
  description?: string;
  image_url?: string;
  category?: string;
  is_active?: boolean;
}

export async function getGallery() {
  const res = await api.get<Gallery[]>('/gallery/');
  return res.data;
}

export async function createGallery(data: GalleryCreate) {
  const res = await api.post<Gallery>('/gallery/', data);
  return res.data;
}

export async function updateGallery(id: number, data: GalleryUpdate) {
  const res = await api.put<Gallery>(`/gallery/${id}`, data);
  return res.data;
}

export async function deleteGallery(id: number) {
  const res = await api.delete<Gallery>(`/gallery/${id}`);
  return res.data;
}

// Members API
export interface TempleMember {
  id: number;
  name: string;
  phone: string;
  email?: string;
  role?: string;
  is_active?: boolean;
}

export interface TempleMemberCreate {
  name: string;
  phone: string;
  email?: string;
  role?: string;
}

export interface TempleMemberUpdate {
  name?: string;
  phone?: string;
  email?: string;
  role?: string;
  is_active?: boolean;
}

export async function getMembers() {
  const res = await api.get<TempleMember[]>('/temple-members/');
  return res.data;
}

export async function createMember(data: TempleMemberCreate) {
  const res = await api.post<TempleMember>('/temple-members/', data);
  return res.data;
}

export async function updateMember(id: number, data: TempleMemberUpdate) {
  const res = await api.put<TempleMember>(`/temple-members/${id}`, data);
  return res.data;
}

export async function deleteMember(id: number) {
  const res = await api.delete<TempleMember>(`/temple-members/${id}`);
  return res.data;
}

// Donors API
export async function generateDonorReceipt(id: number) {
  const res = await api.post(`/donors/${id}/generate-receipt`);
  return res.data;
}

export async function getDonorReceipt(id: number) {
  const res = await api.get(`/donors/${id}/receipt`, { responseType: 'blob' });
  return res.data;
}

// Stats API
export interface VisitorStats {
  total_visitors: number;
  today_visitors: number;
}

export async function trackVisit() {
  const res = await api.post('/stats/track');
  return res.data;
}

export async function getVisitorStats() {
  const res = await api.get<VisitorStats>('/stats/stats');
  return res.data;
}

// Finance API
export type IncomeSource = 'SEVA' | 'DONATION' | 'HUNDI' | 'MANUAL';
export type PaymentMode = 'CASH' | 'UPI' | 'BANK' | 'CHEQUE';
export type ExpenseCategory = 'SALARY' | 'MATERIAL' | 'MAINTENANCE' | 'FESTIVAL' | 'OTHER';

export interface IncomeTransaction {
  id: string;
  source_type: IncomeSource;
  amount: number;
  payment_mode: PaymentMode;
  reference_id?: string;
  notes?: string;
  received_by: number;
  received_at: string;
}

export interface ExpenseTransaction {
  id: string;
  category: ExpenseCategory;
  description: string;
  amount: number;
  payment_mode: PaymentMode;
  paid_to: string;
  approved_by: number;
  expense_date: string;
  notes?: string;
}

export interface FinanceSummary {
  total_income: number;
  total_expenses: number;
  balance: number;
  income_by_source: Record<string, number>;
  expense_by_category: Record<string, number>;
}

export interface LedgerEntry {
  date: string;
  particulars: string;
  voucher_no: string;
  credit: number;
  debit: number;
  balance: number;
}

export async function addIncome(data: any) {
  const res = await api.post<IncomeTransaction>('/finance/income', data);
  return res.data;
}

export async function addExpense(data: any) {
  const res = await api.post<ExpenseTransaction>('/finance/expense', data);
  return res.data;
}

export async function getFinanceSummary() {
  const res = await api.get<FinanceSummary>('/finance/summary');
  return res.data;
}

export async function getLedger(startDate?: string, endDate?: string) {
  const params = { start_date: startDate, end_date: endDate };
  const res = await api.get<LedgerEntry[]>('/finance/ledger', { params });
  return res.data;
}

export async function exportFinanceCSV(startDate?: string, endDate?: string) {
  const params = { start_date: startDate, end_date: endDate };
  const res = await api.get('/finance/ledger/csv', { params, responseType: 'blob' });
  return res.data;
}

export async function exportFinancePDF(startDate?: string, endDate?: string) {
  const params = { start_date: startDate, end_date: endDate };
  const res = await api.get('/finance/ledger/pdf', { params, responseType: 'blob' });
  return res.data;
}

export async function getMonthlyFinanceReport(year: number, month: number) {
  const params = { year, month };
  const res = await api.get('/finance/reports/monthly', { params });
  return res.data;
}

export async function getMonthlyFinanceReportPDF(year: number, month: number) {
  const params = { year, month };
  const res = await api.get('/finance/reports/monthly/pdf', { params, responseType: 'blob' });
  return res.data;
}
