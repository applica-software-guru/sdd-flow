import { cn } from '@/lib/utils';

interface PreviewFrameProps {
  label: string;
  children: React.ReactNode;
  className?: string;
  address?: string;
}
export default function PreviewFrame({
  label,
  children,
  className,
  address = 'app.sddflow.com',
}: PreviewFrameProps) {
  return (
    <div
      role="img"
      aria-label={label}
      className={cn(
        'overflow-hidden rounded-2xl border bg-card text-card-foreground shadow-2xl ring-1 ring-foreground/5',
        className
      )}
    >
      <div aria-hidden="true">
        <div className="flex items-center gap-2 border-b bg-muted/50 px-4 py-3">
          <span className="h-2.5 w-2.5 rounded-full bg-red-400" />
          <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
          <span className="ml-2 flex-1 rounded-md bg-background/80 px-3 py-1 text-center text-[10px] text-muted-foreground">
            {address}
          </span>
        </div>
        {children}
      </div>
    </div>
  );
}
