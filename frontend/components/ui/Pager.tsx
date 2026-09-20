import { ChevronLeft, ChevronRight } from 'lucide-react';
import { btnGhost } from './styles';

interface PagerProps {
  page: number;
  pageSize: number;
  total: number;
  onPage: (page: number) => void;
}

export default function Pager({ page, pageSize, total, onPage }: PagerProps) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (total <= pageSize) return null;
  const from = (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);
  return (
    <nav aria-label="Pagination" className="mt-4 flex items-center justify-between gap-3 text-sm text-gray-600">
      <span>
        {from}–{to} of {total}
      </span>
      <div className="flex items-center gap-2">
        <button type="button" className={btnGhost} disabled={page <= 1} onClick={() => onPage(page - 1)}>
          <ChevronLeft className="h-4 w-4" aria-hidden="true" /> Prev
        </button>
        <span aria-current="page">
          {page} / {pages}
        </span>
        <button type="button" className={btnGhost} disabled={page >= pages} onClick={() => onPage(page + 1)}>
          Next <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </nav>
  );
}
