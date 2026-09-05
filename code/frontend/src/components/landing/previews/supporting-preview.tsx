import { ChevronDown, FileText, History } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { translate } from '@/i18n';

export default function SupportingPreview() {
  return (
    <div className="grid gap-4 sm:grid-cols-2" aria-hidden="true">
      <Card className="p-4">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />
          <div>
            <p className="text-sm font-semibold">
              {translate('landing:auto.product_features_theme_md')}
            </p>
            <p className="text-xs text-muted-foreground">
              {translate('landing:auto.documentation_version_1_2')}
            </p>
          </div>
          <Badge className="ml-auto" variant="secondary">
            {translate('landing:auto.synced')}
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
            <p className="truncate text-sm font-semibold">
              {translate('landing:auto.status_changed')}
            </p>
            <p className="text-xs text-muted-foreground">
              {translate('landing:auto.bug_transitioned_bug_011')}
            </p>
          </div>
          <ChevronDown className="h-4 w-4" />
        </div>
        <div className="bg-muted/30 p-4 text-xs">
          <p>
            <span className="text-muted-foreground">
              {translate('landing:auto.previous_status')}
            </span>{' '}
            {'draft'}
          </p>
          <p className="mt-1">
            <span className="text-muted-foreground">{translate('landing:auto.new_status')}</span>{' '}
            {'open'}
          </p>
        </div>
      </Card>
    </div>
  );
}
