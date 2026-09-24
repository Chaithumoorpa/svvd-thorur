/** DTOs mirroring the FastAPI response models. Money is a JSON number (rupees). */

export type Role = 'SUPER_ADMIN' | 'ADMIN' | 'TRUSTEE' | 'STAFF' | 'GENERAL_USER';

export type Permission =
  | 'dashboard:view'
  | 'content:write'
  | 'temple:write'
  | 'messages:manage'
  | 'tickets:manage'
  | 'members:read'
  | 'members:write'
  | 'donors:read'
  | 'donors:write'
  | 'donations:read'
  | 'donations:write'
  | 'finance:read'
  | 'finance:write'
  | 'users:manage'
  | 'audit:read';

export interface Paged<T> {
  items: T[];
  total: number;
}

export interface Temple {
  id: number;
  name: string;
  deity_name: string | null;
  tagline: string | null;
  history: string | null;
  address: string | null;
  village: string | null;
  district: string | null;
  state: string | null;
  pincode: string | null;
  map_url: string | null;
  contact_phone: string | null;
  contact_email: string | null;
  whatsapp_number: string | null;
  hero_image_url: string | null;
  facebook_url: string | null;
  instagram_url: string | null;
  youtube_url: string | null;
}

export type TempleUpdate = Partial<Omit<Temple, 'id'>>;

export interface TempleTiming {
  id: number;
  label: string;
  start_time: string; // HH:MM:SS
  end_time: string;
  days: string;
  note: string | null;
  sort_order: number;
  is_active: boolean;
}

export type TempleTimingInput = Omit<TempleTiming, 'id'>;

export interface Announcement {
  id: number;
  title: string;
  message: string | null;
  start_date: string | null;
  end_date: string | null;
  is_active: boolean;
  source_festival_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface AnnouncementInput {
  title: string;
  message?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_active?: boolean;
}

export interface Festival {
  id: number;
  name: string;
  description: string | null;
  festival_date: string | null;
  end_date: string | null;
  location: string | null;
  image_url: string | null;
  festival_type: string;
  is_active: boolean;
  auto_announce: boolean;
  announce_days_before: number;
}

export interface FestivalInput {
  name: string;
  description?: string | null;
  festival_date?: string | null;
  end_date?: string | null;
  location?: string | null;
  image_url?: string | null;
  festival_type?: string;
  is_active?: boolean;
  auto_announce?: boolean;
  announce_days_before?: number;
}

export interface Pooja {
  id: number;
  name: string;
  description: string | null;
  start_time: string | null;
  end_time: string | null;
  pooja_type: string;
  is_paid: boolean;
  suggested_amount: number | null;
  sort_order: number;
  is_active: boolean;
}

export interface PoojaInput {
  name: string;
  description?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  pooja_type?: string;
  is_paid?: boolean;
  suggested_amount?: number | null;
  sort_order?: number;
  is_active?: boolean;
}

export interface GalleryItem {
  id: number;
  title: string;
  description: string | null;
  image_url: string;
  category: string;
  is_active: boolean;
  sort_order: number;
}

export interface GalleryInput {
  title: string;
  description?: string | null;
  image_url: string;
  category?: string;
  is_active?: boolean;
  sort_order?: number;
}

export interface UploadUrlResponse {
  upload_url: string;
  fields: Record<string, string>;
  public_url: string;
  key: string;
  max_bytes: number;
}

export interface Member {
  id: number;
  name: string;
  phone: string;
  email: string | null;
  position: string | null;
  show_on_website: boolean;
  sort_order: number;
  photo_url: string | null;
  is_active: boolean;
}

export interface MemberInput {
  name: string;
  phone: string;
  email?: string | null;
  position?: string | null;
  show_on_website?: boolean;
  sort_order?: number;
  photo_url?: string | null;
  is_active?: boolean;
}

export interface CommitteeMember {
  id: number;
  name: string;
  position: string | null;
  photo_url: string | null;
}

export interface Donor {
  id: number;
  name: string;
  phone: string | null;
  email: string | null;
  address: string | null;
  pan_number: string | null;
  is_active: boolean;
  donation_count: number;
  total_donated: number;
}

export interface DonorInput {
  name: string;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  pan_number?: string | null;
}

export type PaymentMode = 'CASH' | 'UPI' | 'BANK' | 'CHEQUE';
export type DonationType = 'general' | 'annadanam' | 'festival' | 'pooja' | 'construction' | 'other';

export interface Donation {
  id: number;
  donor_id: number;
  donor_name: string | null;
  amount: number;
  donation_type: string;
  purpose: string | null;
  donated_on: string;
  payment_mode: PaymentMode;
  receipt_number: string | null;
  receipt_generated_at: string | null;
}

export interface DonationInput {
  donor_id: number;
  amount: number;
  donation_type?: DonationType;
  purpose?: string | null;
  donated_on?: string | null;
  payment_mode?: PaymentMode;
}

export type ContactStatus = 'PENDING' | 'IN_PROGRESS' | 'RESOLVED' | 'REJECTED';

export interface ContactMessage {
  id: number;
  name: string;
  email: string;
  subject: string;
  message: string;
  status: ContactStatus;
  admin_notes: string | null;
  created_at: string;
}

export interface ContactInput {
  name: string;
  email: string;
  subject: string;
  message: string;
  website?: string;
}

export type TicketStatus = 'ACTIVE' | 'USED' | 'CANCELLED';

export interface SevaTicket {
  id: string;
  ticket_number: string;
  seva_id: number;
  seva_name: string;
  devotee_name: string;
  mobile_number: string;
  email?: string | null;
  seva_date: string;
  seva_time: string | null;
  payment_status: 'FREE' | 'PAID';
  amount: number;
  status: TicketStatus;
  source: 'ONLINE' | 'COUNTER';
  qr_token: string;
  booked_by_user_id?: number | null;
  created_at: string;
}

export interface SevaBookingInput {
  seva_id: number;
  devotee_name: string;
  mobile_number: string;
  seva_date: string;
  seva_time?: string | null;
}

/** Public online booking: gated on a verified email, see requestBookingOtp/verifyBookingOtp. */
export interface SevaBookingOnlineInput extends SevaBookingInput {
  email: string;
  booking_token: string;
}

export interface CounterTicketInput extends SevaBookingInput {
  seva_name?: string;
  payment_status?: 'FREE' | 'PAID';
  amount?: number;
}

export interface AppUser {
  id: number;
  username: string;
  email: string | null;
  phone: string | null;
  is_active: boolean;
  roles: Role[];
  must_change_password: boolean;
}

export interface UserCreateInput {
  username: string;
  password: string;
  email?: string | null;
  phone?: string | null;
  roles: Role[];
}

export interface UserUpdateInput {
  email?: string | null;
  phone?: string | null;
  is_active?: boolean;
  roles?: Role[];
  password?: string;
}

export interface Me {
  id: number;
  username: string;
  roles: Role[];
  permissions: Permission[];
  is_admin: boolean;
  is_super_admin: boolean;
  is_trustee: boolean;
  must_change_password: boolean;
  last_login: string | null;
}

export interface DashboardStats {
  poojas: number;
  announcements: number;
  donors: number;
  gallery: number;
  members: number;
  seva_tickets: number;
  seva_tickets_today: number;
  pending_messages: number;
  upcoming_festivals: number;
}

export interface ActivityItem {
  id: number;
  text: string;
  actor: string | null;
  action: string;
  entity_type: string;
  created_at: string;
}

export interface AuditLog {
  id: number;
  actor_username: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  summary: string | null;
  changes: unknown;
  ip_address: string | null;
  created_at: string;
}

export interface HomePayload {
  temple: Temple | null;
  timings: TempleTiming[];
  announcements: Announcement[];
  festivals: Festival[];
  poojas: Pooja[];
}

export type IncomeSource = 'SEVA' | 'DONATION' | 'HUNDI' | 'MANUAL';
export type ExpenseCategory = 'SALARY' | 'MATERIAL' | 'MAINTENANCE' | 'FESTIVAL' | 'OTHER';

export interface FinanceSummary {
  total_income: number;
  total_expenses: number;
  balance: number;
  income_by_source: Record<string, number>;
  expense_by_category: Record<string, number>;
}

export interface LedgerEntry {
  id: string;
  date: string;
  type: 'INCOME' | 'EXPENSE';
  category_or_source: string;
  description: string;
  amount: number; // signed
  payment_mode: string;
}

export interface IncomeInput {
  source_type: IncomeSource;
  amount: number;
  payment_mode: PaymentMode;
  reference_id?: string | null;
  notes?: string | null;
}

export interface ExpenseInput {
  category: ExpenseCategory;
  description: string;
  amount: number;
  payment_mode: PaymentMode;
  paid_to: string;
  expense_date: string;
  notes?: string | null;
}

export interface VisitorStats {
  total_visitors: number;
  today_visitors: number;
}
