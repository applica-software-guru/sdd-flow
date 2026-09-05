import { formatDateOnly } from '@/lib/format';
import { Fragment, useDeferredValue, useState } from 'react';
import { ChevronDown, Search, X } from 'lucide-react';
import { useParams } from 'react-router-dom';
import { DetailsCell } from '@/components/audit-details-cell';
import EmptyState from '@/components/empty-state';
import Pagination from '@/components/pagination';
import LoadingState from '@/components/shared/loading-state';
import PageHeader from '@/components/shared/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import UserName from '@/components/user-name';
import { useAuditLog } from '@/hooks/use-audit-log';
import { useTenantMembers } from '@/hooks/use-tenants';
import { describeAction } from '@/lib/audit-details';
import type { AuditLogEntry } from '@/types';
import { translate } from '@/i18n';
import { compactUserDisplayLabel } from '@/utils/user';

const entityTypes = () =>
  [
    ['project', translate('audit:auto.project')],
    ['change_request', translate('audit:auto.change_request')],
    ['bug', translate('audit:auto.bug')],
    ['document', translate('audit:auto.document')],
    ['member', translate('audit:auto.member')],
    ['api_key', translate('audit:auto.api_key')],
    ['worker', translate('audit:auto.worker')],
    ['worker_job', translate('audit:auto.worker_job')],
    ['user', translate('audit:auto.user')],
  ] as const;

function entityTypeLabel(entityType?: string | null): string {
  if (!entityType) return translate('audit:system');
  return (
    entityTypes().find(([value]) => value === entityType)?.[1] ?? entityType.replace(/_/g, ' ')
  );
}

export default function AuditLogPage() {
  const { tenantId } = useParams();
  const [action, setAction] = useState('');
  const deferredAction = useDeferredValue(action);
  const [entityType, setEntityType] = useState('all');
  const [userId, setUserId] = useState('all');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [page, setPage] = useState(1);
  const [expandedEntries, setExpandedEntries] = useState<Set<string>>(() => new Set());
  const { data: members } = useTenantMembers(tenantId);
  const { data, isLoading } = useAuditLog(tenantId, {
    action: deferredAction || undefined,
    entity_type: entityType === 'all' ? undefined : entityType,
    user_id: userId === 'all' ? undefined : userId,
    from: from ? `${from}T00:00:00.000Z` : undefined,
    to: to ? `${to}T23:59:59.999Z` : undefined,
    page,
    page_size: 25,
  });
  const hasFilters = Boolean(action || entityType !== 'all' || userId !== 'all' || from || to);
  const resetPage = () => setPage(1);
  const clearFilters = () => {
    setAction('');
    setEntityType('all');
    setUserId('all');
    setFrom('');
    setTo('');
    resetPage();
  };

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        title={translate('audit:auto.audit_log')}
        description={translate(
          'audit:auto.review_activity_status_changes_and_administrative_actions'
        )}
      />

      <section
        aria-label={translate('audit:auto.audit_log_filters')}
        className="mb-5 rounded-lg border bg-card p-4 shadow-sm"
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-[minmax(15rem,1.5fr)_repeat(4,minmax(9rem,1fr))_auto] xl:items-end">
          <div className="space-y-1.5">
            <Label htmlFor="audit-action">{translate('audit:auto.search_activity')}</Label>
            <div className="relative">
              <Search
                className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground"
                aria-hidden="true"
              />
              <Input
                id="audit-action"
                value={action}
                onChange={(event) => {
                  setAction(event.target.value);
                  resetPage();
                }}
                placeholder={translate('audit:auto.action_or_event_type')}
                className="pl-9"
              />
            </div>
          </div>
          <FilterSelect
            label={translate('audit:auto.entity_type')}
            value={entityType}
            onChange={(value) => {
              setEntityType(value);
              resetPage();
            }}
          >
            <SelectItem value="all">{translate('audit:auto.all_entities')}</SelectItem>
            {entityTypes().map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </FilterSelect>
          <FilterSelect
            label={translate('audit:auto.actor')}
            value={userId}
            onChange={(value) => {
              setUserId(value);
              resetPage();
            }}
          >
            <SelectItem value="all">{translate('audit:auto.all_actors')}</SelectItem>
            {members?.map((member) => (
              <SelectItem key={member.user_id} value={member.user_id} title={member.display_name}>
                {compactUserDisplayLabel({ display_name: member.display_name }, 40)}
              </SelectItem>
            ))}
          </FilterSelect>
          <DateFilter
            id="audit-from"
            label={translate('audit:auto.from')}
            value={from}
            onChange={(value) => {
              setFrom(value);
              resetPage();
            }}
          />
          <DateFilter
            id="audit-to"
            label={translate('audit:auto.to')}
            value={to}
            onChange={(value) => {
              setTo(value);
              resetPage();
            }}
          />
          <Button type="button" variant="ghost" onClick={clearFilters} disabled={!hasFilters}>
            <X aria-hidden="true" />
            {translate('audit:auto.clear')}
          </Button>
        </div>
        <div className="mt-3 flex items-center justify-between border-t pt-3 text-sm text-muted-foreground">
          <span>
            {isLoading
              ? translate('audit:auto.loading_entries')
              : `${data?.total ?? 0} ${data?.total === 1 ? translate('audit:auto.entry') : translate('audit:auto.entries')}`}
          </span>
          {hasFilters && (
            <Badge variant="secondary">{translate('audit:auto.filters_active')}</Badge>
          )}
        </div>
      </section>

      <div className="overflow-hidden rounded-lg border bg-card shadow-sm">
        {isLoading ? (
          <LoadingState label={translate('audit:auto.loading_audit_log')} />
        ) : !data?.items.length ? (
          <EmptyState
            title={
              hasFilters
                ? translate('audit:auto.no_matching_entries')
                : translate('audit:auto.no_audit_log_entries')
            }
            description={
              hasFilters
                ? translate('audit:auto.try_changing_or_clearing_the_active_filters')
                : translate('audit:auto.actions_performed_in_this_tenant_will_appear')
            }
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[52rem]">
                <thead className="bg-muted/60">
                  <tr>
                    <Header className="w-40">{translate('audit:auto.time')}</Header>
                    <Header className="w-48">{translate('audit:auto.actor')}</Header>
                    <Header className="w-44">{translate('audit:auto.activity')}</Header>
                    <Header>{translate('audit:auto.target')}</Header>
                    <Header className="w-16">
                      <span className="sr-only">{translate('audit:auto.details')}</span>
                    </Header>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((entry) => (
                    <AuditRow
                      key={entry.id}
                      entry={entry}
                      expanded={expandedEntries.has(entry.id)}
                      onToggle={() =>
                        setExpandedEntries((current) => {
                          const next = new Set(current);
                          if (next.has(entry.id)) next.delete(entry.id);
                          else next.add(entry.id);
                          return next;
                        })
                      }
                    />
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={data.page} totalPages={data.pages} onPageChange={setPage} />
          </>
        )}
      </div>
    </div>
  );
}

function AuditRow({
  entry,
  expanded,
  onToggle,
}: {
  entry: AuditLogEntry;
  expanded: boolean;
  onToggle: () => void;
}) {
  const action = entry.action || entry.event_type;
  const date = new Date(entry.created_at);
  const hasDetails = Object.keys(entry.details ?? {}).length > 0;
  const detailsId = `audit-details-${entry.id}`;
  return (
    <Fragment>
      <tr className="border-t align-top first:border-t-0 hover:bg-muted/40">
        <td className="whitespace-nowrap px-5 py-4">
          <time dateTime={entry.created_at} className="text-sm font-medium">
            {formatDateOnly(date)}
          </time>
          <span className="block text-xs text-muted-foreground">
            {date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </span>
        </td>
        <td className="px-5 py-4">
          {entry.user ? (
            <UserName
              name={entry.user.display_name}
              email={entry.user.email}
              avatarUrl={entry.user.avatar_url}
            />
          ) : (
            <Badge variant="outline" className="italic">
              {translate('audit:auto.system')}
            </Badge>
          )}
        </td>
        <td className="px-5 py-4">
          <span className="text-sm font-medium">{describeAction(action)}</span>
          <code className="mt-1 block text-xs text-muted-foreground">{action}</code>
        </td>
        <td className="px-5 py-4">
          <span
            className="block max-w-72 truncate text-sm font-medium"
            title={entry.entity_label || entry.entity_id || undefined}
          >
            {entry.entity_label || (entry.entity_id ? `${entry.entity_id.slice(0, 8)}…` : '—')}
          </span>
          <span className="block text-xs capitalize text-muted-foreground">
            {entityTypeLabel(entry.entity_type)}
          </span>
        </td>
        <td className="px-3 py-3">
          {hasDetails && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={onToggle}
              aria-expanded={expanded}
              aria-controls={detailsId}
              aria-label={translate('audit:expandDetailsFor', {
                action,
                state: expanded ? translate('audit:auto.collapse') : translate('audit:auto.expand'),
              })}
            >
              <ChevronDown
                aria-hidden="true"
                className={`transition-transform ${expanded ? translate('audit:auto.rotate_180') : ''}`}
              />
            </Button>
          )}
        </td>
      </tr>
      {hasDetails && expanded && (
        <tr className="bg-muted/35">
          <td colSpan={5} className="border-t px-5 py-4">
            <div
              id={detailsId}
              role="region"
              aria-label={translate('audit:detailsFor', { action })}
              className="rounded-md border bg-background p-4 text-sm"
            >
              <DetailsCell entry={entry} />
            </div>
          </td>
        </tr>
      )}
    </Fragment>
  );
}

function Header({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <th
      scope="col"
      className={`px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground ${className}`}
    >
      {children}
    </th>
  );
}
function FilterSelect({
  label,
  value,
  onChange,
  children,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  children: React.ReactNode;
}) {
  const id = `audit-${label.toLowerCase().replace(' ', '-')}`;
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger id={id}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>{children}</SelectContent>
      </Select>
    </div>
  );
}
function DateFilter({
  id,
  label,
  value,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Input id={id} type="date" value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}
