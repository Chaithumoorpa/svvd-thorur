import { cloneElement, isValidElement, useId, type ReactElement, type ReactNode } from 'react';

interface FieldProps {
  label: string;
  children: ReactElement;
  hint?: string;
  required?: boolean;
  className?: string;
}

/** Label + control wired together with matching id / aria-describedby. */
export default function Field({ label, children, hint, required, className }: FieldProps) {
  const id = useId();
  const hintId = `${id}-hint`;
  const control = isValidElement(children)
    ? cloneElement(children as ReactElement<Record<string, unknown>>, {
        id,
        'aria-describedby': hint ? hintId : undefined,
        required,
      })
    : (children as ReactNode);
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-gray-700">
        {label}
        {required && <span className="text-red-600"> *</span>}
      </label>
      {control}
      {hint && (
        <p id={hintId} className="mt-1 text-xs text-gray-500">
          {hint}
        </p>
      )}
    </div>
  );
}
