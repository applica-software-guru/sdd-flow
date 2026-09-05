import { ChevronDown, FileText, History } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';

export default function SupportingPreview() {
  return (
    <div className="grid gap-4 sm:grid-cols-2" aria-hidden="true">
      <Card className="p-4">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />
          <div>
            <p className="text-sm font-semibold">product/features/theme.md</p>
            <p className="text-xs text-muted-foreground">Documentation · version 1.2</p>
          </div>
          <Badge className="ml-auto" variant="secondary">
            Synced
          </Badge>
        </div>
        <div className="mt-4 space-y-2">
          <span className="block h-2 w-2/3 rounded bg-muted" />
          <span className="block h-2 w-full rounded bg-muted" />
          <span className="block h-2 w-5/6 rounded bg-muted" />
        </div>
      </Card>
      <Card className="overflow-hidden">
        <div className="flex items-center gap-2 border-b p-4">
          <History className="h-5 w-5 text-primary" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold">Status changed</p>
            <p className="text-xs text-muted-foreground">bug.transitioned · BUG-011</p>
          </div>
          <ChevronDown className="h-4 w-4" />
        </div>
        <div className="bg-muted/30 p-4 text-xs">
          <p>
            <span className="text-muted-foreground">Previous status:</span> draft
          </p>
          <p className="mt-1">
            <span className="text-muted-foreground">New status:</span> open
          </p>
        </div>
      </Card>
    </div>
  );
}
