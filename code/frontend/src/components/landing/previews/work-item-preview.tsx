import { MessageSquare, Sparkles, UserRound } from 'lucide-react';
import SeverityBadge from '@/components/severity-badge';
import StatusBadge from '@/components/status-badge';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { translate } from '@/i18n';

export default function WorkItemPreview() {
  return (
    <Card
      role="img"
      aria-label={translate('landing:auto.shared_work_item_collaboration_preview')}
      className="overflow-hidden shadow-xl"
    >
      <div aria-hidden="true">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b p-5">
          <div>
            <p className="font-mono text-xs text-muted-foreground">BUG-011</p>
            <h3 className="mt-1 font-bold">
              {translate('landing:auto.keep_the_landing_page_public')}
            </h3>
            <p className="mt-1 text-xs text-muted-foreground">
              {translate('landing:auto.created_by_alex_sep_5_3_comments')}
            </p>
          </div>
          <div className="flex gap-2">
            <SeverityBadge severity="major" />
            <StatusBadge status="open" />
          </div>
        </div>
        <div className="p-5">
          <p className="text-sm leading-6 text-muted-foreground">
            {translate('landing:auto.authenticated_visitors_should_be_able_to_review')}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button size="sm">{translate('landing:auto.start_review')}</Button>
            <Button size="sm" variant="outline">
              <Sparkles className="h-4 w-4" />
              {translate('landing:auto.enrich')}
            </Button>
          </div>
        </div>
        <div className="grid gap-4 border-t bg-muted/25 p-5 sm:grid-cols-2">
          <div>
            <p className="text-xs font-semibold">{translate('landing:auto.assignment')}</p>
            <div className="mt-2 flex items-center gap-2 text-sm">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-primary">
                <UserRound className="h-4 w-4" />
              </span>
              {translate('landing:auto.maya_chen')}
              <Badge variant="secondary">{translate('landing:auto.assignee')}</Badge>
            </div>
          </div>
          <div className="sm:border-l sm:pl-4">
            <p className="flex items-center gap-1.5 text-xs font-semibold">
              <MessageSquare className="h-3.5 w-3.5" />
              {translate('landing:auto.latest_discussion')}
            </p>
            <p className="mt-2 text-xs text-muted-foreground">
              {translate('landing:auto.use_an_explicit_open_app_action_without')}
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}
