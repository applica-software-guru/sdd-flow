import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useCurrentUser } from '@/hooks/use-auth';
import { cn } from '@/lib/utils';

interface LandingCtaProps {
  anonymousLabel?: string;
  authenticatedLabel?: string;
  className?: string;
  size?: 'default' | 'lg';
  inverted?: boolean;
}
export default function LandingCta({
  anonymousLabel = 'Get Started Free',
  authenticatedLabel = 'Go to dashboard',
  className,
  size = 'lg',
  inverted,
}: LandingCtaProps) {
  const { data: user, isLoading } = useCurrentUser();
  if (isLoading)
    return (
      <div
        role="status"
        aria-label="Checking session"
        className={cn(
          'h-11 min-w-52 animate-pulse rounded-lg',
          inverted ? 'bg-white/35' : 'bg-primary/30',
          className
        )}
      />
    );
  return (
    <Button
      asChild
      size={size}
      variant={inverted ? 'secondary' : 'default'}
      className={cn(
        'min-w-52 gap-2 shadow-lg transition-transform hover:-translate-y-0.5',
        inverted && 'bg-white text-primary hover:bg-white/90',
        className
      )}
    >
      <Link to={user ? '/tenants' : '/register'}>
        {user ? authenticatedLabel : anonymousLabel}
        <ArrowRight className="h-4 w-4" aria-hidden="true" />
      </Link>
    </Button>
  );
}
