'use client';

import Modal from '@/components/ui/Modal';
import { btnDanger, btnGhost, btnPrimary } from '@/components/ui/styles';

interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel?: string;
  danger?: boolean;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  title, message, confirmLabel = 'Confirm', danger, busy, onConfirm, onCancel,
}: ConfirmDialogProps) {
  return (
    <Modal title={title} onClose={onCancel}>
      <p className="text-sm text-gray-600">{message}</p>
      <div className="mt-6 flex justify-end gap-2">
        <button type="button" className={btnGhost} onClick={onCancel} disabled={busy}>
          Cancel
        </button>
        <button type="button" className={danger ? btnDanger : btnPrimary} onClick={onConfirm} disabled={busy}>
          {busy ? 'Please wait…' : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
