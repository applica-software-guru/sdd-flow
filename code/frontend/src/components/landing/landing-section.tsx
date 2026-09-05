import type { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';
import LandingContainer from './landing-container';

interface LandingSectionProps extends HTMLAttributes<HTMLElement> {
  muted?: boolean;
  containerClassName?: string;
}
export default function LandingSection({
  muted,
  className,
  containerClassName,
  children,
  ...props
}: LandingSectionProps) {
  return (
    <section
      className={cn('scroll-mt-14 py-20 sm:py-24 lg:py-28', muted && 'bg-muted/45', className)}
      {...props}
    >
      <LandingContainer className={containerClassName}>{children}</LandingContainer>
    </section>
  );
}
