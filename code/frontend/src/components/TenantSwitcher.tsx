import { useState, useRef, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTenants } from '../hooks/useTenants';

export default function TenantSwitcher() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { tenantId } = useParams();
  const { data: tenants } = useTenants();

  const current = tenants?.find((t) => t.id === tenantId);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
      >
        <svg
          className="h-4 w-4 text-slate-500"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z"
          />
        </svg>
        {current?.name || 'Select tenant'}
        <svg
          className="h-4 w-4 text-slate-400"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M8.25 15L12 18.75 15.75 15m-7.5-6L12 5.25 15.75 9"
          />
        </svg>
      </button>
      {open && (
        <div className="absolute left-0 top-full z-50 mt-1 w-56 rounded-md border border-slate-200 bg-white py-1 shadow-lg">
          {tenants?.map((tenant) => (
            <button
              key={tenant.id}
              onClick={() => {
                navigate(`/tenants/${tenant.id}`);
                setOpen(false);
              }}
              className={`flex w-full items-center px-4 py-2 text-sm hover:bg-slate-50 ${
                tenant.id === tenantId
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-slate-700'
              }`}
            >
              {tenant.name}
            </button>
          ))}
          <div className="border-t border-slate-100 mt-1 pt-1">
            <button
              onClick={() => {
                navigate('/tenants/new');
                setOpen(false);
              }}
              className="flex w-full items-center gap-2 px-4 py-2 text-sm text-blue-600 hover:bg-slate-50"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 4.5v15m7.5-7.5h-15"
                />
              </svg>
              New tenant
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
