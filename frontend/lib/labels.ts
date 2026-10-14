/** Display names for enum values the admin pages show. */
import type {
  AssetCondition, ExpenseCategory, ExpenseStatus, LetterKind, LetterStatus, MovementType, SignatoryStatus,
} from './types';

export const EXPENSE_CATEGORIES: Record<ExpenseCategory, string> = {
  POOJA_SUPPLIES: 'Pooja supplies',
  ANNADANAM: 'Annadanam / prasadam',
  FESTIVAL: 'Festival',
  SALARY: 'Salaries',
  UTILITIES: 'Utilities (power, water, phone)',
  MAINTENANCE: 'Maintenance & repairs',
  CONSTRUCTION: 'Construction',
  ASSETS: 'Assets (vessels, ornaments, equipment)',
  MATERIAL: 'Materials',
  OTHER: 'Other',
};
export const EXPENSE_CATEGORY_KEYS = Object.keys(EXPENSE_CATEGORIES) as ExpenseCategory[];

/** Short name for tables and charts. */
export const shortCategory = (c: string) =>
  (EXPENSE_CATEGORIES[c as ExpenseCategory] ?? c.charAt(0) + c.slice(1).toLowerCase()).split(' (')[0];

export const EXPENSE_STATUS: Record<ExpenseStatus, { label: string; cls: string }> = {
  PENDING: { label: 'Awaiting approval', cls: 'bg-amber-100 text-amber-800' },
  APPROVED: { label: 'Approved', cls: 'bg-green-100 text-green-800' },
  REJECTED: { label: 'Rejected', cls: 'bg-red-100 text-red-800' },
  VOID: { label: 'Void', cls: 'bg-gray-200 text-gray-600' },
};

export const MOVEMENT_TYPES: Record<MovementType, string> = {
  PURCHASE: 'Purchase',
  DONATION_IN: 'Donation in kind',
  USAGE: 'Used',
  ADJUSTMENT: 'Stock count',
  WRITE_OFF: 'Write-off',
};

export const CONDITIONS: Record<AssetCondition, string> = {
  GOOD: 'Good',
  NEEDS_REPAIR: 'Needs repair',
  DAMAGED: 'Damaged',
  MISSING: 'Missing',
};

/** "2.500" -> "2.5", "3.000" -> "3" */
export const formatQty = (q: string | number | null | undefined) => {
  if (q === null || q === undefined || q === '') return '-';
  const n = Number(q);
  return Number.isFinite(n) ? n.toLocaleString('en-IN', { maximumFractionDigits: 3 }) : String(q);
};

export const LETTER_KIND_LABELS: Record<LetterKind, string> = {
  GENERAL: 'General letter',
  APPOINTMENT: 'Appointment letter',
  MEMBERSHIP_CERTIFICATE: 'Membership certificate',
  SERVICE_CERTIFICATE: 'Service certificate',
  TO_WHOM_IT_MAY_CONCERN: 'To whom it may concern',
  DONATION_ACKNOWLEDGEMENT: 'Donation acknowledgement',
  NOC: 'No objection certificate',
  INVITATION: 'Invitation',
  POWER_OF_ATTORNEY: 'Power of attorney (authorised signatory)',
  RESOLUTION: 'Resolution (authorised signatory)',
  AUTHORISATION: 'Letter of authorisation',
};
export const LETTER_KINDS = Object.keys(LETTER_KIND_LABELS) as LetterKind[];
/** Certificates print a centred title instead of the To / Subject / Dear block. */
export const CERTIFICATE_KINDS = new Set<LetterKind>([
  'MEMBERSHIP_CERTIFICATE', 'SERVICE_CERTIFICATE', 'TO_WHOM_IT_MAY_CONCERN', 'NOC', 'POWER_OF_ATTORNEY', 'RESOLUTION',
]);

export const LETTER_STATUS: Record<LetterStatus, { label: string; cls: string }> = {
  DRAFT: { label: 'Draft', cls: 'bg-gray-100 text-gray-700' },
  AWAITING_SIGNATURES: { label: 'Awaiting signatures', cls: 'bg-amber-100 text-amber-800' },
  ISSUED: { label: 'Issued', cls: 'bg-green-100 text-green-800' },
  REVOKED: { label: 'Revoked', cls: 'bg-red-100 text-red-800' },
};

export const SIGNATORY_STATUS: Record<SignatoryStatus, { label: string; cls: string }> = {
  PENDING: { label: 'Waiting', cls: 'text-amber-700' },
  SIGNED: { label: 'Signed', cls: 'text-green-700' },
  PAPER: { label: 'Signs in ink', cls: 'text-gray-600' },
  DECLINED: { label: 'Declined', cls: 'text-red-700' },
};
