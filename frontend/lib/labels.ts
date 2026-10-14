/** Display names for enum values the admin pages show. */
import type { AssetCondition, ExpenseCategory, ExpenseStatus, MovementType } from './types';

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
