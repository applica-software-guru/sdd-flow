import { ArrowLeft } from 'lucide-react';
import { Link, type LinkProps } from 'react-router-dom';
import { cn } from '@/lib/utils';

export default function BackLink({ className, children, ...props }: LinkProps) {
  return (
    <Link
      className={cn(
        'inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground',
        className
      )}
      {...props}
    >
      <ArrowLeft className="h-4 w-4" aria-hidden="true" />
      {children}
    </Link>
  );
}
