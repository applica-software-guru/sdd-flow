import { translate } from '@/i18n';

export interface PreviewWorker {
  name: string;
  agent: string;
  state: 'Online' | 'Busy';
  job: string;
}

export const previewWorkers: PreviewWorker[] = [
  {
    get name() {
      return translate('landing:worker.frontend');
    },
    agent: 'Claude',
    state: 'Busy',
    get job() {
      return translate('landing:worker.applying');
    },
  },
  {
    get name() {
      return translate('landing:worker.quality');
    },
    agent: 'Codex',
    state: 'Online',
    get job() {
      return translate('landing:worker.ready');
    },
  },
];
