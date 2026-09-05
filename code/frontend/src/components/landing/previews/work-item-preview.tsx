import { MessageSquare, Sparkles, UserRound } from 'lucide-react';
import SeverityBadge from '@/components/severity-badge';
import StatusBadge from '@/components/status-badge';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export default function WorkItemPreview() {
  return (
    <Card
      role="img"
      aria-label="Shared work-item collaboration preview"
      className="overflow-hidden shadow-xl"
    >
      <div aria-hidden="true">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b p-5">
          <div>
            <p className="font-mono text-xs text-muted-foreground">BUG-011</p>
            <h3 className="mt-1 font-bold">Keep the landing page public</h3>
            <p className="mt-1 text-xs text-muted-foreground">
              Created by Alex · Sep 5 · 3 comments
            </p>
          </div>
          <div className="flex gap-2">
            <SeverityBadge severity="major" />
            <StatusBadge status="open" />
          </div>
        </div>
        <div className="p-5">
          <p className="text-sm leading-6 text-muted-foreground">
            Authenticated visitors should be able to review the public product site and deliberately
            choose when to enter the platform.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button size="sm">Start review</Button>
            <Button size="sm" variant="outline">
              <Sparkles className="h-4 w-4" />
              Enrich
            </Button>
          </div>
        </div>
        <div className="grid gap-4 border-t bg-muted/25 p-5 sm:grid-cols-2">
          <div>
            <p className="text-xs font-semibold">Assignment</p>
            <div className="mt-2 flex items-center gap-2 text-sm">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-primary">
                <UserRound className="h-4 w-4" />
              </span>
              Maya Chen <Badge variant="secondary">Assignee</Badge>
            </div>
          </div>
          <div className="sm:border-l sm:pl-4">
            <p className="flex items-center gap-1.5 text-xs font-semibold">
              <MessageSquare className="h-3.5 w-3.5" />
              Latest discussion
            </p>
            <p className="mt-2 text-xs text-muted-foreground">
              “Use an explicit Open app action without redirecting the page.”
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}
