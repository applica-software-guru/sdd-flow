import type { PropsWithChildren } from 'react';

type Props = PropsWithChildren<{
  className?: string;
}>;

export default function PageContainer({ className, children }: Props) {
  const base = 'mx-auto w-full max-w-5xl';
  return <div className={className ? `${base} ${className}` : base}>{children}</div>;
}
