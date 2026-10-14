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
  | 'expenses:submit'
  | 'inventory:read'
  | 'inventory:write'
  | 'inventory:manage'
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
  upi_vpa: string | null;
  /** Account holder name the bank shows in a devotee's UPI app. */
  bank_account_name: string | null;
  registration_number: string | null;
  pan_number: string | null;
  eighty_g_number: string | null;
}

export type TempleUpdate = Partial<Omit<Temple, 'id'>>;

/** e-Hundi: a UPI deep-link QR built from the temple's own VPA. A direct
 * devotee-to-temple transfer - never processed by this backend. */
export interface HundiQrInfo {
  configured: boolean;
  upi_vpa: string | null;
  payee_name: string | null;
  qr_base64: string | null;
  /** The payment link the QR encodes - opened directly by the "Donate via UPI" button. */
  upi_uri: string | null;
  /** Printed with the QR so devotees can verify they're paying the registered temple. */
  registration_number: string | null;
  pan_number: string | null;
  eighty_g_number: string | null;
}

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
  /** Set when the festival calendar computed this date (e.g. "sankashti-chaturthi:2026-10-29"). */
  source_key?: string | null;
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
  /** Bookings allowed per date (online + counter); null = unlimited. */
  daily_slot_cap: number | null;
  /** Devotees may add an occasion photo and show their blessing publicly. */
  public_blessings: boolean;
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
  daily_slot_cap?: number | null;
  public_blessings?: boolean;
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
  occasion?: string | null;
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
  occasion?: string | null;
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
  turnstile_token?: string;
}

export type TicketStatus = 'ACTIVE' | 'USED' | 'CANCELLED';
/** PENDING: a paid seva booked online, fee owed but not yet collected - see
 * /seva-tickets/{id}/collect-payment. Counter tickets are only ever FREE or PAID,
 * since staff collect payment (if any) at the moment they create the ticket. */
export type PaymentStatus = 'FREE' | 'PAID' | 'PENDING';

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
  payment_status: PaymentStatus;
  amount: number;
  occasion?: string | null;
  photo_url?: string | null;
  show_publicly?: boolean;
  /** Staff review of the photo / public blessing; null = nothing to review. */
  review_status?: ReviewStatus | null;
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
  occasion?: string;
}

/** Public online booking: gated on a verified email, see requestBookingOtp/verifyBookingOtp. */
export interface SevaBookingOnlineInput extends SevaBookingInput {
  email: string;
  booking_token: string;
  turnstile_token?: string;
  /** From uploadBlessingPhoto - a private upload, published only if staff approve it. */
  photo_key?: string;
  show_publicly?: boolean;
}

export interface CounterTicketInput extends SevaBookingInput {
  seva_name?: string;
  payment_status?: 'FREE' | 'PAID';
  amount?: number;
  email?: string;
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
  pending_expenses: number;
  low_stock_items: number;
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
export type ExpenseCategory =
  | 'POOJA_SUPPLIES' | 'ANNADANAM' | 'FESTIVAL' | 'SALARY' | 'UTILITIES' | 'MAINTENANCE'
  | 'CONSTRUCTION' | 'ASSETS' | 'MATERIAL' | 'OTHER';
export type ExpenseStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'VOID';

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
  bill_key?: string | null;
  festival_id?: number | null;
}

export interface Expense {
  id: string;
  category: ExpenseCategory;
  description: string;
  amount: number;
  payment_mode: PaymentMode;
  paid_to: string;
  expense_date: string;
  notes: string | null;
  status: ExpenseStatus;
  submitted_by: number | null;
  approved_by: number | null;
  decided_at: string | null;
  rejection_reason: string | null;
  voided_at: string | null;
  void_reason: string | null;
  has_bill: boolean;
  festival_id: number | null;
  created_at: string | null;
  submitted_by_name?: string | null;
  approved_by_name?: string | null;
  festival_name?: string | null;
  /** Set when this expense was created by an inventory purchase. */
  inventory_item_id?: number | null;
}

export interface BudgetStatusLine {
  category: ExpenseCategory;
  budget: number | null;
  spent: number;
  pending: number;
  remaining: number | null;
  percent_used: number | null;
  over_budget: boolean;
}

export interface BudgetStatus {
  month: string;
  lines: BudgetStatusLine[];
  total_budget: number;
  total_spent: number;
  total_pending: number;
}

// ------------------------------------------------------------------------------ inventory
export type ItemKind = 'CONSUMABLE' | 'ASSET';
export type AssetCondition = 'GOOD' | 'NEEDS_REPAIR' | 'DAMAGED' | 'MISSING';
export type MovementType = 'PURCHASE' | 'DONATION_IN' | 'USAGE' | 'ADJUSTMENT' | 'WRITE_OFF';

/** Quantities are exact decimals sent as strings ("2.500"). */
export interface InventoryItem {
  id: number;
  name: string;
  kind: ItemKind;
  category: string;
  unit: string;
  quantity: string;
  reorder_level: string | null;
  avg_unit_cost: string;
  location: string | null;
  notes: string | null;
  is_active: boolean;
  material: string | null;
  weight_grams: string | null;
  estimated_value: number | null;
  acquired_on: string | null;
  identification: string | null;
  condition: AssetCondition | null;
  has_photo: boolean;
  last_verified_on: string | null;
  low_stock: boolean;
  stock_value: number;
}

export interface InventoryItemInput {
  name?: string;
  kind?: ItemKind;
  category?: string;
  unit?: string;
  reorder_level?: string | null;
  location?: string | null;
  notes?: string | null;
  material?: string | null;
  weight_grams?: string | null;
  estimated_value?: string | null;
  acquired_on?: string | null;
  identification?: string | null;
  condition?: AssetCondition | null;
  photo_key?: string | null;
  opening_quantity?: string;
  opening_unit_cost?: string | null;
  is_active?: boolean;
}

export interface StockMovement {
  id: number;
  item_id: number;
  item_name: string | null;
  unit: string | null;
  type: MovementType;
  quantity: string;
  balance_after: string;
  unit_cost: string | null;
  total_value: number | null;
  movement_date: string;
  notes: string | null;
  expense_id: string | null;
  expense_status: ExpenseStatus | null;
  vendor: string | null;
  donor_name: string | null;
  donor_phone: string | null;
  receipt_number: string | null;
  pooja_id: number | null;
  pooja_name: string | null;
  festival_id: number | null;
  festival_name: string | null;
  created_by_name: string | null;
  created_at: string;
}

export interface AssetVerification {
  id: number;
  item_id: number;
  verified_on: string;
  condition: AssetCondition;
  weight_grams: string | null;
  notes: string | null;
  verified_by_name: string | null;
  weight_mismatch: boolean;
}

export interface FestivalCost {
  festival_id: number;
  festival_name: string;
  festival_date: string | null;
  stock_used_value: number;
  expenses_total: number;
  total_cost: number;
  items: Array<{ item_name: string; unit: string; quantity: string; value: number }>;
}

export interface InventorySummary {
  consumables: number;
  valuables: number;
  low_stock: number;
  stock_value: number;
  valuables_value: number;
  valuables_unverified: number;
}

export interface VisitorStats {
  total_visitors: number;
  today_visitors: number;
}

// ------------------------------------------------------------ seva calendar & blessings
/** One day's bookings for a seva's public contribution-style grid. */
export interface SevaCalendarDay {
  date: string;
  slots_used: number;
  /** The seva's daily_slot_cap - null when it has no limit. */
  slots_total: number | null;
}

/** A booking the devotee chose to show publicly. Name + occasion always (the
 * public timeline); the photo only while that day's blessings are active. */
export interface BlessingEntry {
  devotee_name: string;
  occasion: string;
  photo_url: string | null;
}

/** upcoming: before the date. active: the date through visible_until
 * (photos shown). archived: after that (names + occasions only). */
export type BlessingStatus = 'upcoming' | 'active' | 'archived';

export interface SevaDay {
  date: string;
  slots_used: number;
  slots_total: number | null;
  blessing_status: BlessingStatus;
  visible_until: string;
  entries: BlessingEntry[];
}

/** pending: fee not paid yet. scheduled: paid, seva date still ahead.
 * active: the seva date through visible_until. expired: after that. */
export interface PersonalBlessing {
  status: 'pending' | 'scheduled' | 'active' | 'expired';
  seva_name: string;
  occasion: string;
  seva_date: string;
  devotee_name: string | null;
  photo_url: string | null;
  visible_until: string | null;
}

export type ReviewStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

/** A booking whose photo / public blessing waits for staff approval.
 * photo_preview_url is a short-lived private link. */
export interface BlessingReview {
  id: string;
  ticket_number: string;
  seva_name: string;
  devotee_name: string;
  occasion: string | null;
  seva_date: string;
  show_publicly: boolean;
  payment_status: PaymentStatus;
  review_status: ReviewStatus;
  photo_preview_url: string | null;
}

// ------------------------------------------------------------------------------ analytics
export interface NamedAmount { name: string; amount: number }
export interface NamedCount { name: string; count: number }

export interface FinanceAnalytics {
  months: Array<{ month: string; income: number; expenses: number; net: number }>;
  totals: { income: number; expenses: number; net: number };
  previous: { income: number; expenses: number; net: number };
  income_by_source: NamedAmount[];
  expense_by_category: NamedAmount[];
  payment_modes: Array<{ mode: string; count: number; amount: number }>;
  top_payees: Array<{ name: string; count: number; amount: number }>;
  donations: { count: number; total: number; donors: number; average: number };
}

export interface InventoryAnalytics {
  stock_by_category: NamedAmount[];
  consumption: Array<{ month: string; used: number; written_off: number; donated_in: number }>;
  top_used: Array<{ item_name: string; unit: string; quantity: string; value: number }>;
}

export interface AuditAnalytics {
  days: number;
  totals: { events: number; active_users: number; logins: number; failed_logins: number; deletions: number; off_hours: number };
  per_day: Array<{ date: string; count: number }>;
  by_hour: number[];
  by_actor: Array<{ name: string; count: number; deletions: number }>;
  by_action: NamedCount[];
  by_entity: NamedCount[];
  failed_login_ips: NamedCount[];
  sensitive: Array<{
    id: number; created_at: string; actor: string | null; action: string; entity_type: string;
    summary: string | null; ip_address: string | null; off_hours: boolean;
  }>;
}
