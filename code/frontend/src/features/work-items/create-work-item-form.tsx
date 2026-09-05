import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import MarkdownEditor from '@/components/markdown-editor';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useEditableSlug } from '@/hooks/use-editable-slug';
import type { TenantMember } from '@/types';
import { translate } from '@/i18n';

export interface WorkItemCreateValues {
  title: string;
  body: string;
  slug?: string;
  assignee_id?: string;
  severity?: string;
}

interface CreateWorkItemFormProps {
  backTo: string;
  filenamePrefix: string;
  titlePlaceholder: string;
  submitLabel: string;
  pendingLabel: string;
  errorMessage: string;
  members?: TenantMember[];
  pending: boolean;
  failed: boolean;
  withSeverity?: boolean;
  onSubmit: (values: WorkItemCreateValues) => Promise<void>;
}

export default function CreateWorkItemForm(props: CreateWorkItemFormProps) {
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [assigneeId, setAssigneeId] = useState('unassigned');
  const [severity, setSeverity] = useState('minor');
  const slug = useEditableSlug();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    await props.onSubmit({
      title,
      body,
      slug: slug.slug || undefined,
      assignee_id: assigneeId === 'unassigned' ? undefined : assigneeId,
      severity: props.withSeverity ? severity : undefined,
    });
  }

  return (
    <Card>
      <CardContent className="p-6">
        <form onSubmit={(event) => void handleSubmit(event)} className="space-y-4">
          {props.failed && (
            <Alert variant="destructive">
              <AlertDescription>{props.errorMessage}</AlertDescription>
            </Alert>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="work-item-title">{translate('common:auto.title')}</Label>
            <Input
              id="work-item-title"
              required
              value={title}
              onChange={(event) => {
                setTitle(event.target.value);
                slug.onTitleChange(event.target.value);
              }}
              placeholder={props.titlePlaceholder}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="work-item-slug">
              {translate('common:auto.slug')}
              <span className="font-normal text-muted-foreground">
                {translate('common:auto.optional')}
              </span>
            </Label>
            <Input
              id="work-item-slug"
              value={slug.slug}
              onChange={(event) => slug.onSlugChange(event.target.value)}
              placeholder={translate('common:auto.auto_generated_from_title')}
            />
            {slug.slug && (
              <p className="text-xs text-muted-foreground">
                {translate('common:auto.filename')}{' '}
                <code>
                  {props.filenamePrefix}/NNN-{slug.slug}
                  {translate('common:auto.md')}
                </code>
              </p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label>{translate('common:auto.description')}</Label>
            <MarkdownEditor value={body} onChange={setBody} height={300} />
          </div>
          <div className={props.withSeverity ? 'grid gap-4 sm:grid-cols-2' : ''}>
            {props.withSeverity && (
              <div className="space-y-1.5">
                <Label htmlFor="work-item-severity">{translate('common:auto.severity')}</Label>
                <Select value={severity} onValueChange={setSeverity}>
                  <SelectTrigger id="work-item-severity">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {['trivial', 'minor', 'major', 'critical'].map((value) => (
                      <SelectItem key={value} value={value} className="capitalize">
                        {value}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            <div className="space-y-1.5">
              <Label htmlFor="work-item-assignee">{translate('common:auto.assignee')}</Label>
              <Select value={assigneeId} onValueChange={setAssigneeId}>
                <SelectTrigger id="work-item-assignee">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="unassigned">{translate('common:auto.unassigned')}</SelectItem>
                  {props.members?.map((member) => (
                    <SelectItem key={member.user_id} value={member.user_id}>
                      {member.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" asChild>
              <Link to={props.backTo}>{translate('common:auto.cancel')}</Link>
            </Button>
            <Button type="submit" disabled={props.pending}>
              {props.pending ? props.pendingLabel : props.submitLabel}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
