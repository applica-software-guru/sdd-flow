import { Bot, CircleCheck, Terminal } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { previewWorkers } from '../preview-data';
import { translate } from '@/i18n';

export default function WorkerPreview() {
  return (
    <Card
      role="img"
      aria-label={translate('landing:auto.remote_worker_orchestration_preview')}
      className="overflow-hidden shadow-xl"
    >
      <div aria-hidden="true">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div>
            <h3 className="font-semibold">{translate('landing:auto.remote_workers')}</h3>
            <p className="text-xs text-muted-foreground">
              {translate('landing:auto.agents_connected_to_this_project')}
            </p>
          </div>
          <Badge variant="secondary">
            <CircleCheck className="mr-1 h-3.5 w-3.5" />
            {translate('landing:auto.2_online')}
          </Badge>
        </div>
        <div className="divide-y">
          {previewWorkers.map((worker) => (
            <div key={worker.name} className="flex items-center gap-3 px-5 py-4">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Bot className="h-5 w-5" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">{worker.name}</p>
                <p className="truncate text-xs text-muted-foreground">
                  {worker.agent} · {worker.job}
                </p>
              </div>
              <Badge variant={worker.state === 'Busy' ? 'default' : 'outline'}>
                {translate(`common:status.${worker.state.toLowerCase()}`)}
              </Badge>
            </div>
          ))}
        </div>
        <div className="border-t bg-zinc-950 p-4 font-mono text-xs text-zinc-300">
          <p className="flex items-center gap-2 text-emerald-400">
            <Terminal className="h-4 w-4" />
            {translate('landing:auto.worker_apply_cr_038')}
          </p>
          <p className="mt-2 text-zinc-500">
            {translate('landing:auto.reading_synchronized_documentation')}
          </p>
          <p className="mt-1 text-zinc-500">
            {translate('landing:auto.updating_typed_preview_components')}
          </p>
        </div>
      </div>
    </Card>
  );
}
