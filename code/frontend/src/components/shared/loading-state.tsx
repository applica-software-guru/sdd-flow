import { LoaderCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LoadingStateProps {
  label?: string;
  className?: string;
  compact?: boolean;
}

export default function LoadingState({
  label = 'Loading',
  className,
  compact = false,
}: LoadingStateProps) {
  return (
    <div
      role="status"
      className={cn('flex items-center justify-center', compact ? 'py-8' : 'py-16', className)}
    >
      <LoaderCircle
        className={cn('animate-spin text-primary', compact ? 'h-5 w-5' : 'h-8 w-8')}
        aria-hidden="true"
      />
      <span className="sr-only">{label}</span>
    </div>
  );
}
