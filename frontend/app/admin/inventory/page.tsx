'use client';

import React, { useMemo, useState } from 'react';
import {
  AlertTriangle, BadgeCheck, Camera, ClipboardCheck, Download, FileText, Gift, History, Minus, Pencil, Plus,
  Scale, ShoppingCart, Trash2,
} from 'lucide-react';
import AdminPage from '@/components/admin/AdminPage';
import { useAuth } from '@/components/admin/AuthContext';
import Field from '@/components/ui/Field';
import Modal from '@/components/ui/Modal';
import Pager from '@/components/ui/Pager';
import { EmptyBlock, ErrorBlock, LoadingBlock, Notice } from '@/components/ui/States';
import { btnDanger, btnGhost, btnPrimary, cardCls, inputCls } from '@/components/ui/styles';
import { useAction } from '@/hooks/useAction';
import { useLoad } from '@/hooks/useLoad';
import {
  createInventoryItem, deleteInventoryItem, downloadInKindReceipt, getFestivalCosts, getFestivals, getInventoryPhoto,
  getInventorySummary, getPoojas, listAssetVerifications, listInventoryCategories, listInventoryItems,
  listStockMovements, recordAdjustment, recordDonationInKind, recordPurchase, recordUsage, recordWriteOff, saveBlob,
  updateInventoryItem, uploadExpenseBill, uploadInventoryPhoto, verifyAsset,
} from '@/lib/api';
import { photoUploadErrorMessage } from '@/lib/imageUpload';
import { emptyToNull, formatDate, formatMoney, todayISO } from '@/lib/format';
import { CONDITIONS, EXPENSE_STATUS, MOVEMENT_TYPES, formatQty } from '@/lib/labels';
import type { AssetCondition, InventoryItem, InventoryItemInput, ItemKind, MovementType, PaymentMode } from '@/lib/types';

type Tab = 'stock' | 'valuables' | 'donations' | 'history' | 'festivals';
type MoveKind = 'purchase' | 'usage' | 'donation' | 'count' | 'writeoff';

const UNITS = ['kg', 'g', 'L', 'ml', 'pcs', 'packets', 'bundles', 'boxes', 'metres', 'sets'];
const CATEGORY_SUGGESTIONS = ['Oils & ghee', 'Pooja materials', 'Flowers', 'Grains & provisions', 'Clothes',
  'Vessels', 'Lamps', 'Ornaments', 'Electrical', 'Furniture', 'Other'];
const MATERIALS = ['GOLD', 'SILVER', 'BRASS', 'COPPER', 'PANCHALOHA', 'BRONZE', 'WOOD', 'STONE', 'OTHER'];
const MODES: PaymentMode[] = ['CASH', 'UPI', 'BANK', 'CHEQUE'];
const MOVE_TITLES: Record<MoveKind, string> = {
  purchase: 'Record a purchase', usage: 'Record usage', donation: 'Record a donation in kind',
  count: 'Stock count', writeoff: 'Write off stock',
};

/** Start of the Indian financial year (1 April) - valuables are verified once per year. */
const fyStart = () => {
  const d = new Date();
  return `${d.getMonth() >= 3 ? d.getFullYear() : d.getFullYear() - 1}-04-01`;
};

export default function InventoryAdmin() {
  const { can } = useAuth();
  const canWrite = can('inventory:write');
  const canManage = can('inventory:manage');
  const [tab, setTab] = useState<Tab>('stock');
  const summary = useLoad(getInventorySummary, []);
  const items = useLoad(() => listInventoryItems(), []);
  const action = useAction();

  const [itemModal, setItemModal] = useState<{ item: InventoryItem | null; kind: ItemKind } | null>(null);
  const [move, setMove] = useState<{ kind: MoveKind; itemId: number | null } | null>(null);
  const [verifying, setVerifying] = useState<InventoryItem | null>(null);
  const [historyItem, setHistoryItem] = useState<number | null>(null);
  const [historyKey, setHistoryKey] = useState(0);

  /** Shows a success message in the page's banner. */
  const notify = (msg: string) => void action.run(async () => undefined, msg);
  const refresh = () => {
    summary.reload();
    items.reload();
    setHistoryKey((k) => k + 1);
  };
  const consumables = (items.data ?? []).filter((i) => i.kind === 'CONSUMABLE');
  const valuables = (items.data ?? []).filter((i) => i.kind === 'ASSET');
  const showHistory = (itemId: number) => { setHistoryItem(itemId); setTab('history'); };

  async function viewPhoto(item: InventoryItem) {
    const link = await action.run(() => getInventoryPhoto(item.id));
    if (link) window.open(link.url, '_blank', 'noopener');
  }

  async function remove(item: InventoryItem) {
    if (!window.confirm(`Delete "${item.name}"? Only items entered by mistake, with no stock history, can be deleted.`)) return;
    if (await action.run(() => deleteInventoryItem(item.id), `Deleted ${item.name}.`)) refresh();
  }

  function downloadRegister() {
    const rows = [['Name', 'Category', 'Material', 'Weight (g)', 'Estimated value (Rs)', 'Quantity', 'Condition',
      'Location', 'Identification', 'Acquired on', 'Last verified']];
    valuables.forEach((v) => rows.push([v.name, v.category, v.material ?? '', v.weight_grams ?? '',
      v.estimated_value != null ? String(v.estimated_value) : '', formatQty(v.quantity), v.condition ? CONDITIONS[v.condition] : '',
      v.location ?? '', v.identification ?? '', v.acquired_on ?? '', v.last_verified_on ?? 'never']));
    const csv = rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
    saveBlob(new Blob([`﻿${csv}`], { type: 'text/csv;charset=utf-8' }), `valuables_register_${todayISO()}.csv`);
  }

  const s = summary.data;
  const tabs: Array<[Tab, string]> = [
    ['stock', 'Stock'], ['valuables', 'Valuables register'], ['donations', 'Donations in kind'], ['history', 'History'],
    ['festivals', 'Festival costs'],
  ];

  return (
    <AdminPage
      title="Inventory"
      description="Pooja stock, the temple's valuables, donations in kind and what each festival used. Buying stock records the expense automatically."
      actions={(
        <>
          {canWrite && (
            <button type="button" className={btnGhost} onClick={() => { action.clear(); setMove({ kind: 'donation', itemId: null }); }}>
              <Gift className="h-4 w-4" aria-hidden="true" /> Donation in kind
            </button>
          )}
          {canManage && (
            <button type="button" className={btnPrimary} onClick={() => { action.clear(); setItemModal({ item: null, kind: tab === 'valuables' ? 'ASSET' : 'CONSUMABLE' }); }}>
              <Plus className="h-4 w-4" aria-hidden="true" /> {tab === 'valuables' ? 'Add valuable' : 'Add item'}
            </button>
          )}
        </>
      )}
    >
      {s && (
        <section aria-label="Inventory overview" className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
          <div className={`${cardCls} p-4`}><p className="text-sm text-gray-500">Stock value</p><p className="text-xl font-bold">{formatMoney(s.stock_value)}</p><p className="text-xs text-gray-400">{s.consumables} items at average cost</p></div>
          <button type="button" onClick={() => setTab('stock')} className={`${cardCls} p-4 text-left ${s.low_stock ? 'border-amber-300 bg-amber-50' : ''}`}>
            <p className="text-sm text-gray-500">Low stock</p><p className={`text-xl font-bold ${s.low_stock ? 'text-amber-700' : ''}`}>{s.low_stock}</p><p className="text-xs text-gray-400">at or below reorder level</p>
          </button>
          <div className={`${cardCls} p-4`}><p className="text-sm text-gray-500">Valuables</p><p className="text-xl font-bold">{formatMoney(s.valuables_value)}</p><p className="text-xs text-gray-400">{s.valuables} items, estimated</p></div>
          <button type="button" onClick={() => setTab('valuables')} className={`${cardCls} p-4 text-left ${s.valuables_unverified ? 'border-red-200 bg-red-50' : ''}`}>
            <p className="text-sm text-gray-500">Not verified this year</p><p className={`text-xl font-bold ${s.valuables_unverified ? 'text-red-700' : ''}`}>{s.valuables_unverified}</p><p className="text-xs text-gray-400">since 1 April</p>
          </button>
        </section>
      )}

      <div role="tablist" className="mb-4 flex flex-wrap gap-1 border-b border-gray-200">
        {tabs.map(([t, label]) => (
          <button key={t} type="button" role="tab" aria-selected={tab === t} onClick={() => { setTab(t); if (t !== 'history') setHistoryItem(null); }}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${tab === t ? 'border-red-900 text-red-900' : 'border-transparent text-gray-500 hover:text-gray-800'}`}>
            {label}
          </button>
        ))}
      </div>

      {action.success && <div className="mb-3"><Notice kind="success">{action.success}</Notice></div>}
      {action.error && !itemModal && !move && !verifying && <div className="mb-3"><Notice kind="error">{action.error}</Notice></div>}

      {(tab === 'stock' || tab === 'valuables') && (items.loading ? <LoadingBlock /> : items.error ? <ErrorBlock message={items.error} onRetry={items.reload} /> : null)}

      {tab === 'stock' && items.data && (
        consumables.length === 0 ? (
          <EmptyBlock title="No stock items yet" hint={canManage ? 'Add ghee, oil, camphor, rice… with what is on the shelf today.' : 'An admin adds the items first.'} />
        ) : (
          <div className={`${cardCls} overflow-x-auto`}>
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th scope="col" className="px-4 py-3">Item</th>
                  <th scope="col" className="px-4 py-3 text-right">In stock</th>
                  <th scope="col" className="px-4 py-3 text-right">Avg cost</th>
                  <th scope="col" className="px-4 py-3 text-right">Value</th>
                  <th scope="col" className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {consumables.map((i) => (
                  <tr key={i.id} className={i.low_stock ? 'bg-amber-50/60' : ''}>
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900">{i.name}</p>
                      <p className="text-xs text-gray-500">{i.category}{i.location && ` · ${i.location}`}</p>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right">
                      <span className={`font-semibold ${i.low_stock ? 'text-amber-800' : 'text-gray-900'}`}>{formatQty(i.quantity)} {i.unit}</span>
                      {i.low_stock && <span className="ml-1 inline-flex items-center gap-0.5 rounded bg-amber-200 px-1 text-xs text-amber-900"><AlertTriangle className="h-3 w-3" aria-hidden="true" />low</span>}
                      {i.reorder_level !== null && <p className="text-xs text-gray-400">reorder at {formatQty(i.reorder_level)}</p>}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right text-gray-600">{Number(i.avg_unit_cost) ? `${formatMoney(Number(i.avg_unit_cost))}/${i.unit}` : '-'}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-right">{formatMoney(i.stock_value)}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap justify-end gap-1">
                        {canWrite && (
                          <>
                            <button type="button" className={btnGhost} onClick={() => { action.clear(); setMove({ kind: 'usage', itemId: i.id }); }} title="Record usage">
                              <Minus className="h-4 w-4" aria-hidden="true" /> Use
                            </button>
                            <button type="button" className={btnGhost} onClick={() => { action.clear(); setMove({ kind: 'purchase', itemId: i.id }); }} title="Record a purchase">
                              <ShoppingCart className="h-4 w-4" aria-hidden="true" /> Buy
                            </button>
                          </>
                        )}
                        {canManage && (
                          <>
                            <button type="button" className={btnGhost} onClick={() => { action.clear(); setMove({ kind: 'count', itemId: i.id }); }} title="Stock count">
                              <ClipboardCheck className="h-4 w-4" aria-hidden="true" /><span className="sr-only">Stock count</span>
                            </button>
                            <button type="button" className={btnGhost} onClick={() => { action.clear(); setItemModal({ item: i, kind: i.kind }); }} title="Edit">
                              <Pencil className="h-4 w-4" aria-hidden="true" /><span className="sr-only">Edit</span>
                            </button>
                          </>
                        )}
                        <button type="button" className={btnGhost} onClick={() => showHistory(i.id)} title="History">
                          <History className="h-4 w-4" aria-hidden="true" /><span className="sr-only">History</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}

      {tab === 'valuables' && items.data && (
        valuables.length === 0 ? (
          <EmptyBlock title="No valuables registered" hint={canManage ? 'Register ornaments, vessels, lamps and vahanams with weight, value and a photo.' : 'An admin registers valuables.'} />
        ) : (
          <>
            <div className="mb-2 flex justify-end">
              <button type="button" className={btnGhost} onClick={downloadRegister}><Download className="h-4 w-4" aria-hidden="true" /> Download register (CSV)</button>
            </div>
            <div className={`${cardCls} overflow-x-auto`}>
              <table className="w-full min-w-[820px] text-left text-sm">
                <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
                  <tr>
                    <th scope="col" className="px-4 py-3">Valuable</th>
                    <th scope="col" className="px-4 py-3">Material / weight</th>
                    <th scope="col" className="px-4 py-3 text-right">Est. value</th>
                    <th scope="col" className="px-4 py-3">Condition</th>
                    <th scope="col" className="px-4 py-3">Last verified</th>
                    <th scope="col" className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {valuables.map((v) => {
                    const overdue = !v.last_verified_on || v.last_verified_on < fyStart();
                    return (
                      <tr key={v.id}>
                        <td className="px-4 py-3">
                          <p className="font-medium text-gray-900">{v.name}{Number(v.quantity) !== 1 && <span className="text-gray-500"> × {formatQty(v.quantity)}</span>}</p>
                          <p className="text-xs text-gray-500">{v.category}{v.location && ` · ${v.location}`}</p>
                          {v.identification && <p className="text-xs text-gray-400">{v.identification}</p>}
                        </td>
                        <td className="px-4 py-3 text-gray-700">{v.material ? v.material.charAt(0) + v.material.slice(1).toLowerCase() : '-'}{v.weight_grams && <span className="text-gray-500"> · {formatQty(v.weight_grams)} g</span>}</td>
                        <td className="whitespace-nowrap px-4 py-3 text-right">{v.estimated_value != null ? formatMoney(v.estimated_value) : '-'}</td>
                        <td className="px-4 py-3">
                          {v.condition && <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${v.condition === 'GOOD' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{CONDITIONS[v.condition]}</span>}
                        </td>
                        <td className={`whitespace-nowrap px-4 py-3 ${overdue ? 'font-medium text-red-700' : 'text-gray-600'}`}>
                          {v.last_verified_on ? formatDate(v.last_verified_on) : 'Never'}{overdue && <span className="block text-xs">due this year</span>}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap justify-end gap-1">
                            {v.has_photo && (
                              <button type="button" className={btnGhost} onClick={() => viewPhoto(v)} title="Photo"><Camera className="h-4 w-4" aria-hidden="true" /><span className="sr-only">Photo</span></button>
                            )}
                            {canManage && (
                              <>
                                <button type="button" className={btnPrimary} onClick={() => { action.clear(); setVerifying(v); }}>
                                  <BadgeCheck className="h-4 w-4" aria-hidden="true" /> Verify
                                </button>
                                <button type="button" className={btnGhost} onClick={() => { action.clear(); setItemModal({ item: v, kind: 'ASSET' }); }} title="Edit"><Pencil className="h-4 w-4" aria-hidden="true" /><span className="sr-only">Edit</span></button>
                              </>
                            )}
                            <button type="button" className={btnGhost} onClick={() => showHistory(v.id)} title="History"><History className="h-4 w-4" aria-hidden="true" /><span className="sr-only">History</span></button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )
      )}

      {tab === 'donations' && <Movements key={`d${historyKey}`} type="DONATION_IN" onError={action.setError} />}
      {tab === 'history' && (
        <Movements key={`h${historyKey}-${historyItem}`} itemId={historyItem} items={items.data ?? []}
          onItem={setHistoryItem} onError={action.setError} />
      )}
      {tab === 'festivals' && <FestivalCosts />}

      {itemModal && (
        <ItemForm item={itemModal.item} kind={itemModal.kind} onClose={() => setItemModal(null)}
          onSaved={(msg) => { setItemModal(null); refresh(); notify(msg); }}
          onDelete={itemModal.item ? () => { const it = itemModal.item!; setItemModal(null); void remove(it); } : undefined} />
      )}
      {move && (
        <MovementForm kind={move.kind} itemId={move.itemId} items={items.data ?? []} canManage={canManage}
          onClose={() => setMove(null)}
          onKind={(kind) => setMove({ ...move, kind })}
          onSaved={(msg) => { setMove(null); refresh(); notify(msg); }} />
      )}
      {verifying && (
        <VerifyForm item={verifying} onClose={() => setVerifying(null)}
          onSaved={(msg) => { setVerifying(null); refresh(); notify(msg); }} />
      )}
    </AdminPage>
  );
}

// ------------------------------------------------------------------------- item form
function ItemForm({ item, kind: initialKind, onClose, onSaved, onDelete }: {
  item: InventoryItem | null; kind: ItemKind; onClose: () => void; onSaved: (msg: string) => void; onDelete?: () => void;
}) {
  const action = useAction();
  const categories = useLoad(listInventoryCategories, []);
  const [kind, setKind] = useState<ItemKind>(item?.kind ?? initialKind);
  const [f, setF] = useState({
    name: item?.name ?? '', category: item?.category ?? '', unit: item?.unit ?? (initialKind === 'ASSET' ? 'pcs' : 'kg'),
    reorder_level: item?.reorder_level ? formatQty(item.reorder_level).replace(/,/g, '') : '', location: item?.location ?? '',
    notes: item?.notes ?? '', material: item?.material ?? '', weight_grams: item?.weight_grams ? String(Number(item.weight_grams)) : '',
    estimated_value: item?.estimated_value != null ? String(item.estimated_value) : '', acquired_on: item?.acquired_on ?? '',
    identification: item?.identification ?? '', condition: (item?.condition ?? 'GOOD') as AssetCondition,
    opening_quantity: initialKind === 'ASSET' ? '1' : '', opening_unit_cost: '', is_active: item?.is_active ?? true,
  });
  const [photoKey, setPhotoKey] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const asset = kind === 'ASSET';
  const allCategories = useMemo(() => Array.from(new Set([...(categories.data ?? []), ...CATEGORY_SUGGESTIONS])), [categories.data]);

  async function pickPhoto(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setUploading(true);
    try {
      setPhotoKey(await uploadInventoryPhoto(file));
    } catch (err) {
      action.setError(photoUploadErrorMessage(err, 'Photo uploads are not set up yet.'));
    } finally {
      setUploading(false);
    }
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    const data: InventoryItemInput = {
      name: f.name.trim(), category: f.category.trim(), unit: f.unit.trim(), location: emptyToNull(f.location), notes: emptyToNull(f.notes),
      reorder_level: asset ? null : emptyToNull(f.reorder_level),
      ...(asset ? {
        material: emptyToNull(f.material), weight_grams: emptyToNull(f.weight_grams), estimated_value: emptyToNull(f.estimated_value),
        acquired_on: emptyToNull(f.acquired_on), identification: emptyToNull(f.identification), condition: f.condition,
      } : {}),
      ...(photoKey ? { photo_key: photoKey } : {}),
    };
    const saved = item
      ? await action.run(() => updateInventoryItem(item.id, { ...data, is_active: f.is_active }))
      : await action.run(() => createInventoryItem({
          ...data, kind, opening_quantity: f.opening_quantity || '0', opening_unit_cost: emptyToNull(f.opening_unit_cost),
        }));
    if (saved) onSaved(item ? `Saved ${saved.name}.` : `Added ${saved.name}.`);
  }

  const valid = f.name.trim().length >= 2 && f.category.trim() && f.unit.trim();
  return (
    <Modal title={item ? `Edit ${item.name}` : asset ? 'Register a valuable' : 'Add a stock item'} onClose={onClose} wide>
      <form onSubmit={save} className="space-y-4">
        {action.error && <Notice kind="error">{action.error}</Notice>}
        {!item && (
          <div className="flex gap-2" role="radiogroup" aria-label="Kind of item">
            {(['CONSUMABLE', 'ASSET'] as ItemKind[]).map((k) => (
              <button key={k} type="button" role="radio" aria-checked={kind === k} onClick={() => { setKind(k); setF({ ...f, unit: k === 'ASSET' ? 'pcs' : f.unit, opening_quantity: k === 'ASSET' ? '1' : '' }); }}
                className={`flex-1 rounded-lg border px-3 py-2 text-sm ${kind === k ? 'border-red-900 bg-red-50 font-semibold text-red-900' : 'border-gray-300 text-gray-600'}`}>
                {k === 'CONSUMABLE' ? 'Stock (used up)' : 'Valuable (kept)'}
              </button>
            ))}
          </div>
        )}
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Name" required className="sm:col-span-2">
            <input className={inputCls} maxLength={150} placeholder={asset ? 'e.g. Silver kireetam' : 'e.g. Cow ghee'} value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />
          </Field>
          <Field label="Category" required>
            <input className={inputCls} list="inv-categories" maxLength={60} value={f.category} onChange={(e) => setF({ ...f, category: e.target.value })} />
          </Field>
          <Field label="Unit" required>
            <input className={inputCls} list="inv-units" maxLength={20} value={f.unit} onChange={(e) => setF({ ...f, unit: e.target.value })} />
          </Field>
          {!item && (
            <>
              <Field label={asset ? 'How many' : 'In stock today'} hint={asset ? undefined : 'What is on the shelf now (0 if none).'}>
                <input type="number" min="0" step="0.001" inputMode="decimal" className={inputCls} value={f.opening_quantity} onChange={(e) => setF({ ...f, opening_quantity: e.target.value })} />
              </Field>
              {!asset && (
                <Field label={`Cost per ${f.unit || 'unit'} (₹)`} hint="So stock used is valued correctly.">
                  <input type="number" min="0" step="0.01" inputMode="decimal" className={inputCls} value={f.opening_unit_cost} onChange={(e) => setF({ ...f, opening_unit_cost: e.target.value })} />
                </Field>
              )}
            </>
          )}
          {!asset && (
            <Field label="Reorder level" hint={`Warn when stock falls to this many ${f.unit || 'units'}.`}>
              <input type="number" min="0" step="0.001" inputMode="decimal" className={inputCls} value={f.reorder_level} onChange={(e) => setF({ ...f, reorder_level: e.target.value })} />
            </Field>
          )}
          <Field label="Location"><input className={inputCls} maxLength={150} placeholder="e.g. Store room, Garbhagudi locker" value={f.location} onChange={(e) => setF({ ...f, location: e.target.value })} /></Field>
          {asset && (
            <>
              <Field label="Material">
                <select className={inputCls} value={f.material} onChange={(e) => setF({ ...f, material: e.target.value })}>
                  <option value="">-</option>
                  {MATERIALS.map((m) => <option key={m} value={m}>{m.charAt(0) + m.slice(1).toLowerCase()}</option>)}
                </select>
              </Field>
              <Field label="Weight (grams)"><input type="number" min="0" step="0.001" inputMode="decimal" className={inputCls} value={f.weight_grams} onChange={(e) => setF({ ...f, weight_grams: e.target.value })} /></Field>
              <Field label="Estimated value (₹)"><input type="number" min="0" step="1" inputMode="decimal" className={inputCls} value={f.estimated_value} onChange={(e) => setF({ ...f, estimated_value: e.target.value })} /></Field>
              <Field label="Acquired on"><input type="date" max={todayISO()} className={inputCls} value={f.acquired_on} onChange={(e) => setF({ ...f, acquired_on: e.target.value })} /></Field>
              <Field label="Condition">
                <select className={inputCls} value={f.condition} onChange={(e) => setF({ ...f, condition: e.target.value as AssetCondition })}>
                  {(Object.keys(CONDITIONS) as AssetCondition[]).map((c) => <option key={c} value={c}>{CONDITIONS[c]}</option>)}
                </select>
              </Field>
              <Field label="Identification marks" className="sm:col-span-2" hint="Hallmark, engraving, donor's inscription - anything that identifies it.">
                <input className={inputCls} maxLength={500} value={f.identification} onChange={(e) => setF({ ...f, identification: e.target.value })} />
              </Field>
              <div className="flex items-center gap-3 sm:col-span-2">
                <label className={`${btnGhost} cursor-pointer`}>
                  <Camera className="h-4 w-4" aria-hidden="true" /> {uploading ? 'Uploading…' : photoKey ? 'Replace photo' : item?.has_photo ? 'Replace photo' : 'Add photo'}
                  <input type="file" accept="image/*" className="sr-only" onChange={pickPhoto} disabled={uploading} />
                </label>
                <span className="text-sm text-gray-500">{photoKey ? 'New photo ready' : item?.has_photo ? 'Photo on file (private)' : 'No photo yet'}</span>
              </div>
            </>
          )}
          <Field label="Notes" className="sm:col-span-2"><input className={inputCls} maxLength={2000} value={f.notes} onChange={(e) => setF({ ...f, notes: e.target.value })} /></Field>
          {item && (
            <label className="flex items-center gap-2 text-sm text-gray-700 sm:col-span-2">
              <input type="checkbox" checked={f.is_active} onChange={(e) => setF({ ...f, is_active: e.target.checked })} /> Active (untick to hide an item no longer kept)
            </label>
          )}
        </div>
        <datalist id="inv-categories">{allCategories.map((c) => <option key={c} value={c} />)}</datalist>
        <datalist id="inv-units">{UNITS.map((u) => <option key={u} value={u} />)}</datalist>
        <div className="flex flex-wrap justify-between gap-2">
          {onDelete ? <button type="button" className={btnDanger} onClick={onDelete}><Trash2 className="h-4 w-4" aria-hidden="true" /> Delete</button> : <span />}
          <div className="flex gap-2">
            <button type="button" className={btnGhost} onClick={onClose}>Cancel</button>
            <button type="submit" className={btnPrimary} disabled={action.busy || uploading || !valid}>{action.busy ? 'Saving…' : 'Save'}</button>
          </div>
        </div>
      </form>
    </Modal>
  );
}

// --------------------------------------------------------------------- movement form
function MovementForm({ kind, itemId, items, canManage, onClose, onKind, onSaved }: {
  kind: MoveKind; itemId: number | null; items: InventoryItem[]; canManage: boolean;
  onClose: () => void; onKind: (k: MoveKind) => void; onSaved: (msg: string) => void;
}) {
  const { can } = useAuth();
  const action = useAction();
  const poojas = useLoad(() => (kind === 'usage' ? getPoojas() : Promise.resolve([])), [kind]);
  const festivals = useLoad(() => (kind === 'usage' ? getFestivals() : Promise.resolve([])), [kind]);
  const [f, setF] = useState({
    item_id: itemId ? String(itemId) : '', quantity: '', total_cost: '', vendor: '', payment_mode: 'CASH' as PaymentMode,
    date: todayISO(), notes: '', donor_name: '', donor_phone: '', donor_address: '', estimated_value: '',
    pooja_id: '', festival_id: '', counted: '', reason: '', bill_key: null as string | null, bill_name: '',
  });
  const [uploading, setUploading] = useState(false);
  const item = items.find((i) => i.id === Number(f.item_id));
  const unit = item?.unit ?? '';
  const choices = items.filter((i) => i.is_active && (kind === 'usage' ? i.kind === 'CONSUMABLE' : true));

  async function attachBill(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setUploading(true);
    try {
      const key = await uploadExpenseBill(file);
      setF((x) => ({ ...x, bill_key: key, bill_name: file.name }));
    } catch (err) {
      action.setError(photoUploadErrorMessage(err, 'Bill uploads are not set up yet. You can save without one.'));
    } finally {
      setUploading(false);
    }
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!item) return;
    const base = { item_id: item.id, movement_date: f.date, notes: emptyToNull(f.notes) };
    const q = `${formatQty(f.quantity)} ${unit} ${item.name}`;
    let done;
    if (kind === 'purchase') {
      done = await action.run(() => recordPurchase({ ...base, quantity: f.quantity, total_cost: f.total_cost, vendor: f.vendor.trim(), payment_mode: f.payment_mode, bill_key: f.bill_key }));
      if (done) onSaved(`Bought ${q}. ${done.expense_status === 'PENDING' ? 'The expense is waiting for an admin to approve it.' : 'The expense has been recorded.'}`);
    } else if (kind === 'usage') {
      done = await action.run(() => recordUsage({ ...base, quantity: f.quantity, pooja_id: f.pooja_id ? Number(f.pooja_id) : null, festival_id: f.festival_id ? Number(f.festival_id) : null }));
      if (done) onSaved(`Recorded ${q} used.`);
    } else if (kind === 'donation') {
      done = await action.run(() => recordDonationInKind({ ...base, quantity: f.quantity, donor_name: f.donor_name.trim(), donor_phone: emptyToNull(f.donor_phone), donor_address: emptyToNull(f.donor_address), estimated_value: emptyToNull(f.estimated_value) }));
      if (done) {
        onSaved(`Received ${q} from ${f.donor_name.trim()} - acknowledgement ${done.receipt_number}.`);
        const pdf = await downloadInKindReceipt(done.id).catch(() => null);
        if (pdf) saveBlob(pdf, `${done.receipt_number}.pdf`);
      }
    } else if (kind === 'count') {
      done = await action.run(() => recordAdjustment({ ...base, counted_quantity: f.counted, reason: f.reason.trim() }));
      if (done) onSaved(`Stock of ${item.name} set to ${formatQty(f.counted)} ${unit}.`);
    } else {
      done = await action.run(() => recordWriteOff({ ...base, quantity: f.quantity, reason: f.reason.trim() }));
      if (done) onSaved(`Wrote off ${q}.`);
    }
  }

  const qtyOk = Number(f.quantity) > 0;
  const valid = !!item && !!f.date && (
    kind === 'purchase' ? qtyOk && Number(f.total_cost) > 0 && f.vendor.trim().length >= 2
      : kind === 'donation' ? qtyOk && f.donor_name.trim().length >= 2
        : kind === 'count' ? f.counted !== '' && Number(f.counted) >= 0 && f.reason.trim().length >= 3
          : kind === 'writeoff' ? qtyOk && f.reason.trim().length >= 3
            : qtyOk);
  const tooMuch = (kind === 'usage' || kind === 'writeoff') && item && Number(f.quantity) > Number(item.quantity);
  const kinds: MoveKind[] = ['usage', 'purchase', 'donation', ...(canManage ? ['count', 'writeoff'] as MoveKind[] : [])];

  return (
    <Modal title={MOVE_TITLES[kind]} onClose={onClose} wide>
      <form onSubmit={save} className="space-y-4">
        {action.error && <Notice kind="error">{action.error}</Notice>}
        <div className="flex flex-wrap gap-1" role="radiogroup" aria-label="What happened">
          {kinds.map((k) => (
            <button key={k} type="button" role="radio" aria-checked={kind === k} onClick={() => onKind(k)}
              className={`rounded-full border px-3 py-1 text-xs ${kind === k ? 'border-red-900 bg-red-50 font-semibold text-red-900' : 'border-gray-300 text-gray-600'}`}>
              {MOVE_TITLES[k].replace('Record a ', '').replace('Record ', '')}
            </button>
          ))}
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Item" required className="sm:col-span-2">
            <select className={inputCls} value={f.item_id} onChange={(e) => setF({ ...f, item_id: e.target.value })}>
              <option value="">Choose…</option>
              {choices.map((i) => <option key={i.id} value={i.id}>{i.name} ({formatQty(i.quantity)} {i.unit} in stock)</option>)}
            </select>
          </Field>
          {kind === 'count' ? (
            <Field label={`Counted on the shelf (${unit || 'units'})`} required hint={item ? `Books say ${formatQty(item.quantity)} ${unit}.` : undefined}>
              <input type="number" min="0" step="0.001" inputMode="decimal" className={inputCls} value={f.counted} onChange={(e) => setF({ ...f, counted: e.target.value })} />
            </Field>
          ) : (
            <Field label={`Quantity (${unit || 'units'})`} required>
              <input type="number" min="0.001" step="0.001" inputMode="decimal" className={inputCls} value={f.quantity} onChange={(e) => setF({ ...f, quantity: e.target.value })} />
            </Field>
          )}
          <Field label="Date" required><input type="date" max={todayISO()} className={inputCls} value={f.date} onChange={(e) => setF({ ...f, date: e.target.value })} /></Field>

          {kind === 'purchase' && (
            <>
              <Field label="Total paid (₹)" required hint={qtyOk && Number(f.total_cost) > 0 ? `${formatMoney(Number(f.total_cost) / Number(f.quantity))} per ${unit}` : undefined}>
                <input type="number" min="0.01" step="0.01" inputMode="decimal" className={inputCls} value={f.total_cost} onChange={(e) => setF({ ...f, total_cost: e.target.value })} />
              </Field>
              <Field label="Paid by">
                <select className={inputCls} value={f.payment_mode} onChange={(e) => setF({ ...f, payment_mode: e.target.value as PaymentMode })}>{MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select>
              </Field>
              <Field label="Bought from" required className="sm:col-span-2"><input className={inputCls} maxLength={255} placeholder="Shop / vendor" value={f.vendor} onChange={(e) => setF({ ...f, vendor: e.target.value })} /></Field>
              <div className="flex flex-wrap items-center gap-3 sm:col-span-2">
                <label className={`${btnGhost} cursor-pointer`}>
                  <FileText className="h-4 w-4" aria-hidden="true" /> {uploading ? 'Uploading…' : f.bill_name ? 'Replace bill' : 'Attach bill'}
                  <input type="file" accept="image/*,application/pdf" className="sr-only" onChange={attachBill} disabled={uploading} />
                </label>
                <span className="text-sm text-gray-500">{f.bill_name || 'No bill attached'}</span>
              </div>
              <p className="text-xs text-gray-500 sm:col-span-2">
                The expense is recorded for you{can('finance:write') ? '.' : ' and waits for an admin to approve it.'} Cost a festival by recording <em>usage</em> for it, not here.
              </p>
            </>
          )}

          {kind === 'usage' && (
            <>
              <Field label="For a seva (optional)">
                <select className={inputCls} value={f.pooja_id} onChange={(e) => setF({ ...f, pooja_id: e.target.value })}>
                  <option value="">-</option>{poojas.data?.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </Field>
              <Field label="For a festival (optional)" hint="Adds to that festival's cost.">
                <select className={inputCls} value={f.festival_id} onChange={(e) => setF({ ...f, festival_id: e.target.value })}>
                  <option value="">-</option>{festivals.data?.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
                </select>
              </Field>
            </>
          )}

          {kind === 'donation' && (
            <>
              <Field label="Donor's name" required><input className={inputCls} maxLength={150} value={f.donor_name} onChange={(e) => setF({ ...f, donor_name: e.target.value })} /></Field>
              <Field label="Phone"><input type="tel" className={inputCls} maxLength={20} value={f.donor_phone} onChange={(e) => setF({ ...f, donor_phone: e.target.value })} /></Field>
              <Field label="Address" className="sm:col-span-2"><input className={inputCls} maxLength={300} value={f.donor_address} onChange={(e) => setF({ ...f, donor_address: e.target.value })} /></Field>
              <Field label="Estimated value (₹, optional)" hint="Your estimate, for the records - not certified on the receipt.">
                <input type="number" min="0" step="1" inputMode="decimal" className={inputCls} value={f.estimated_value} onChange={(e) => setF({ ...f, estimated_value: e.target.value })} />
              </Field>
            </>
          )}

          {(kind === 'count' || kind === 'writeoff') && (
            <Field label="Reason" required className="sm:col-span-2">
              <input className={inputCls} maxLength={500} placeholder={kind === 'count' ? 'e.g. Monthly stock count' : 'e.g. Spoiled, damaged, expired'} value={f.reason} onChange={(e) => setF({ ...f, reason: e.target.value })} />
            </Field>
          )}
          <Field label="Notes" className="sm:col-span-2"><input className={inputCls} maxLength={500} value={f.notes} onChange={(e) => setF({ ...f, notes: e.target.value })} /></Field>
        </div>
        {tooMuch && <Notice kind="error">Only {formatQty(item!.quantity)} {unit} in stock.</Notice>}
        {kind === 'donation' && <p className="text-xs text-gray-500">An acknowledgement receipt (IK-…) downloads when you save, to print or send to the donor.</p>}
        <div className="flex justify-end gap-2">
          <button type="button" className={btnGhost} onClick={onClose}>Cancel</button>
          <button type="submit" className={btnPrimary} disabled={action.busy || uploading || !valid || !!tooMuch}>{action.busy ? 'Saving…' : 'Save'}</button>
        </div>
      </form>
    </Modal>
  );
}

// ---------------------------------------------------------------------- verification
function VerifyForm({ item, onClose, onSaved }: { item: InventoryItem; onClose: () => void; onSaved: (msg: string) => void }) {
  const action = useAction();
  const past = useLoad(() => listAssetVerifications(item.id), [item.id]);
  const [f, setF] = useState({ verified_on: todayISO(), condition: (item.condition ?? 'GOOD') as AssetCondition, weight_grams: '', notes: '' });

  async function save(e: React.FormEvent) {
    e.preventDefault();
    const out = await action.run(() => verifyAsset(item.id, {
      verified_on: f.verified_on, condition: f.condition, weight_grams: emptyToNull(f.weight_grams), notes: emptyToNull(f.notes),
    }));
    if (out) onSaved(out.weight_mismatch
      ? `Verified ${item.name} - but the weight differs from the register (${formatQty(item.weight_grams)} g). Please check.`
      : `Verified ${item.name}.`);
  }

  return (
    <Modal title={`Verify: ${item.name}`} onClose={onClose}>
      <form onSubmit={save} className="space-y-4">
        {action.error && <Notice kind="error">{action.error}</Notice>}
        <p className="text-sm text-gray-600">
          Seen it, checked it{item.weight_grams ? `, weighed it (register: ${formatQty(item.weight_grams)} g)` : ''}.
          {item.identification && <> Look for: {item.identification}.</>}
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Verified on" required><input type="date" max={todayISO()} className={inputCls} value={f.verified_on} onChange={(e) => setF({ ...f, verified_on: e.target.value })} /></Field>
          <Field label="Condition" required>
            <select className={inputCls} value={f.condition} onChange={(e) => setF({ ...f, condition: e.target.value as AssetCondition })}>
              {(Object.keys(CONDITIONS) as AssetCondition[]).map((c) => <option key={c} value={c}>{CONDITIONS[c]}</option>)}
            </select>
          </Field>
          <Field label="Weight today (grams)"><input type="number" min="0" step="0.001" inputMode="decimal" className={inputCls} value={f.weight_grams} onChange={(e) => setF({ ...f, weight_grams: e.target.value })} /></Field>
          <Field label="Notes"><input className={inputCls} maxLength={500} value={f.notes} onChange={(e) => setF({ ...f, notes: e.target.value })} /></Field>
        </div>
        {!!past.data?.length && (
          <div>
            <h3 className="mb-1 text-sm font-semibold text-gray-700">Earlier checks</h3>
            <ul className="max-h-40 divide-y divide-gray-100 overflow-y-auto text-sm">
              {past.data.map((v) => (
                <li key={v.id} className="flex flex-wrap justify-between gap-2 py-1">
                  <span>{formatDate(v.verified_on)} · {CONDITIONS[v.condition]}{v.weight_grams && ` · ${formatQty(v.weight_grams)} g`}{v.weight_mismatch && <span className="ml-1 text-red-700"><Scale className="inline h-3 w-3" aria-hidden="true" /> weight differs</span>}</span>
                  <span className="text-xs text-gray-500">{v.verified_by_name}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        <div className="flex justify-end gap-2">
          <button type="button" className={btnGhost} onClick={onClose}>Cancel</button>
          <button type="submit" className={btnPrimary} disabled={action.busy || !f.verified_on}><BadgeCheck className="h-4 w-4" aria-hidden="true" /> {action.busy ? 'Saving…' : 'Mark verified'}</button>
        </div>
      </form>
    </Modal>
  );
}

// ----------------------------------------------------------------- movement history
function Movements({ type, itemId, items, onItem, onError }: {
  type?: MovementType; itemId?: number | null; items?: InventoryItem[]; onItem?: (id: number | null) => void;
  onError: (msg: string) => void;
}) {
  const [page, setPage] = useState(1);
  const [filterType, setFilterType] = useState<MovementType | ''>(type ?? '');
  const PAGE = 25;
  const list = useLoad(
    () => listStockMovements(page, { item_id: itemId ?? undefined, type: (type ?? filterType) || undefined }, PAGE),
    [page, itemId, filterType, type],
  );

  async function receipt(id: number, number: string | null) {
    try {
      saveBlob(await downloadInKindReceipt(id), `${number ?? 'receipt'}.pdf`);
    } catch {
      onError('Could not download the acknowledgement.');
    }
  }

  return (
    <section>
      {!type && items && onItem && (
        <div className="mb-3 flex flex-wrap items-end gap-3">
          <Field label="Item">
            <select className={inputCls} value={itemId ?? ''} onChange={(e) => { setPage(1); onItem(e.target.value ? Number(e.target.value) : null); }}>
              <option value="">All items</option>
              {items.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
            </select>
          </Field>
          <Field label="Type">
            <select className={inputCls} value={filterType} onChange={(e) => { setPage(1); setFilterType(e.target.value as MovementType | ''); }}>
              <option value="">All</option>
              {(Object.keys(MOVEMENT_TYPES) as MovementType[]).map((t) => <option key={t} value={t}>{MOVEMENT_TYPES[t]}</option>)}
            </select>
          </Field>
        </div>
      )}
      {list.loading ? <LoadingBlock /> : list.error ? <ErrorBlock message={list.error} onRetry={list.reload} /> : !list.data?.items.length ? (
        <EmptyBlock title={type === 'DONATION_IN' ? 'No donations in kind yet' : 'No stock history yet'} hint={type === 'DONATION_IN' ? 'Rice, oil, cloth or a silver lamp a devotee gives - record it to issue an acknowledgement.' : 'Purchases, usage and counts appear here.'} />
      ) : (
        <>
          <div className={`${cardCls} overflow-x-auto`}>
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th scope="col" className="px-4 py-3">Date</th>
                  <th scope="col" className="px-4 py-3">What</th>
                  <th scope="col" className="px-4 py-3 text-right">Change</th>
                  <th scope="col" className="px-4 py-3 text-right">Balance</th>
                  <th scope="col" className="px-4 py-3 text-right">Value</th>
                  <th scope="col" className="px-4 py-3"><span className="sr-only">Receipt</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {list.data.items.map((m) => {
                  const plus = Number(m.quantity) > 0;
                  return (
                    <tr key={m.id}>
                      <td className="whitespace-nowrap px-4 py-3 align-top text-gray-600">{formatDate(m.movement_date)}</td>
                      <td className="px-4 py-3 align-top">
                        <p className="font-medium text-gray-900">{MOVEMENT_TYPES[m.type]} · {m.item_name}</p>
                        <p className="text-xs text-gray-500">
                          {m.vendor && <>from {m.vendor}</>}
                          {m.donor_name && <>from {m.donor_name}{m.donor_phone && ` (${m.donor_phone})`}</>}
                          {m.pooja_name && <>for {m.pooja_name}</>}
                          {m.festival_name && <>{m.pooja_name ? ', ' : 'for '}{m.festival_name}</>}
                          {m.notes && <>{(m.vendor || m.donor_name || m.pooja_name || m.festival_name) ? ' · ' : ''}{m.notes}</>}
                        </p>
                        <p className="text-xs text-gray-400">
                          by {m.created_by_name ?? '?'}
                          {m.expense_status && <> · expense <span className={`rounded px-1 ${EXPENSE_STATUS[m.expense_status].cls}`}>{EXPENSE_STATUS[m.expense_status].label.toLowerCase()}</span></>}
                        </p>
                      </td>
                      <td className={`whitespace-nowrap px-4 py-3 text-right align-top font-semibold ${plus ? 'text-green-700' : 'text-red-700'}`}>{plus ? '+' : '−'}{formatQty(Math.abs(Number(m.quantity)))} {m.unit}</td>
                      <td className="whitespace-nowrap px-4 py-3 text-right align-top text-gray-600">{formatQty(m.balance_after)} {m.unit}</td>
                      <td className="whitespace-nowrap px-4 py-3 text-right align-top text-gray-600">{m.total_value != null ? formatMoney(Math.abs(m.total_value)) : '-'}</td>
                      <td className="px-4 py-3 text-right align-top">
                        {m.receipt_number && (
                          <button type="button" className={btnGhost} onClick={() => receipt(m.id, m.receipt_number)} title="Acknowledgement PDF">
                            <FileText className="h-4 w-4" aria-hidden="true" /> {m.receipt_number}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <Pager page={page} pageSize={PAGE} total={list.data.total} onPage={setPage} />
        </>
      )}
    </section>
  );
}

// ------------------------------------------------------------------- festival costs
function FestivalCosts() {
  const costs = useLoad(getFestivalCosts, []);
  if (costs.loading) return <LoadingBlock />;
  if (costs.error) return <ErrorBlock message={costs.error} onRetry={costs.reload} />;
  if (!costs.data?.length) {
    return <EmptyBlock title="No festival costs yet" hint="Record stock used for a festival, or tag an expense with the festival, and its cost appears here." />;
  }
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {costs.data.map((c) => (
        <article key={c.festival_id} className={`${cardCls} p-4`}>
          <header className="flex items-baseline justify-between gap-2">
            <h3 className="font-semibold text-gray-900">{c.festival_name}</h3>
            {c.festival_date && <span className="text-xs text-gray-500">{formatDate(c.festival_date)}</span>}
          </header>
          <p className="mt-1 text-2xl font-bold text-red-900">{formatMoney(c.total_cost)}</p>
          <p className="text-xs text-gray-500">{formatMoney(c.stock_used_value)} stock used + {formatMoney(c.expenses_total)} other expenses</p>
          {c.items.length > 0 && (
            <ul className="mt-3 divide-y divide-gray-100 text-sm">
              {c.items.map((l) => (
                <li key={l.item_name} className="flex justify-between py-1">
                  <span className="text-gray-700">{l.item_name} <span className="text-gray-400">· {formatQty(l.quantity)} {l.unit}</span></span>
                  <span className="text-gray-900">{formatMoney(l.value)}</span>
                </li>
              ))}
            </ul>
          )}
        </article>
      ))}
    </div>
  );
}
