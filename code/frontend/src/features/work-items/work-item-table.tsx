import { MessageSquare } from 'lucide-react';
import { Link } from 'react-router-dom';
import EmptyState from '@/components/empty-state';
import Pagination from '@/components/pagination';
import SeverityBadge from '@/components/severity-badge';
import LoadingState from '@/components/shared/loading-state';
import ResponsiveTable from '@/components/shared/responsive-table';
import StatusBadge from '@/components/status-badge';
import UserCell from '@/components/user-cell';
import { formatDateOnly } from '@/lib/format';
import type { Bug, ChangeRequest, PaginatedResponse } from '@/types';

type WorkItem = Bug | ChangeRequest;
interface WorkItemTableProps<T extends WorkItem> {
  data?: PaginatedResponse<T>;
  loading: boolean;
  baseUrl: string;
  emptyTitle: string;
  emptyDescription: string;
  onPageChange: (page: number) => void;
}

export default function WorkItemTable<T extends WorkItem>(props: WorkItemTableProps<T>) {
  if (props.loading)
    return (
      <ResponsiveTable>
        <LoadingState label="Loading work items" />
      </ResponsiveTable>
    );
  if (!props.data?.items.length)
    return (
      <ResponsiveTable>
        <EmptyState title={props.emptyTitle} description={props.emptyDescription} />
      </ResponsiveTable>
    );
  const hasSeverity = props.data.items.some((item) => 'severity' in item);

  return (
    <ResponsiveTable>
      <table className="min-w-full divide-y">
        <thead>
          <tr className="bg-muted/60">
            <Header>Title</Header>
            {hasSeverity && <Header>Severity</Header>}
            <Header>Status</Header>
            <Header className="hidden sm:table-cell">Author</Header>
            <Header className="hidden md:table-cell">Assignee</Header>
            <Header className="hidden lg:table-cell">Created</Header>
            <Header className="hidden text-center lg:table-cell">Comments</Header>
          </tr>
        </thead>
        <tbody className="divide-y">
          {props.data.items.map((item) => (
            <tr key={item.id} className="hover:bg-muted/40">
              <td className="px-6 py-4">
                <Link
                  to={`${props.baseUrl}/${item.id}`}
                  className="text-sm font-medium text-primary hover:underline"
                >
                  <span className="mr-1.5 font-mono text-muted-foreground">
                    #{item.formatted_number}
                  </span>
                  {item.title}
                </Link>
              </td>
              {hasSeverity && (
                <td className="px-6 py-4">
                  {'severity' in item ? <SeverityBadge severity={item.severity} /> : null}
                </td>
              )}
              <td className="px-6 py-4">
                <StatusBadge status={item.status} />
              </td>
              <td className="hidden px-6 py-4 sm:table-cell">
                <UserCell user={item.author} />
              </td>
              <td className="hidden px-6 py-4 md:table-cell">
                <UserCell user={item.assignee} fallback="Unassigned" />
              </td>
              <td className="hidden px-6 py-4 text-sm text-muted-foreground lg:table-cell">
                {formatDateOnly(item.created_at)}
              </td>
              <td className="hidden px-6 py-4 text-center text-sm text-muted-foreground lg:table-cell">
                {item.comments_count ? (
                  <span className="inline-flex items-center gap-1">
                    <MessageSquare aria-hidden="true" className="h-4 w-4" />
                    {item.comments_count}
                  </span>
                ) : (
                  '—'
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <Pagination
        page={props.data.page}
        totalPages={props.data.pages}
        onPageChange={props.onPageChange}
      />
    </ResponsiveTable>
  );
}

function Header({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <th
      scope="col"
      className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground ${className}`}
    >
      {children}
    </th>
  );
}
