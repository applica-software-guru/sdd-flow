import { useState, type FormEvent, type RefObject } from 'react';
import CommentHeader from '@/components/comment-header';
import MarkdownRenderer from '@/components/markdown-renderer';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import type { Comment as WorkItemComment, DocumentFile } from '@/types';
import { translate } from '@/i18n';

interface CommentsSectionProps {
  comments?: WorkItemComment[];
  basePath: string;
  docs: DocumentFile[];
  docsRouteBase: string;
  sectionRef: RefObject<HTMLDivElement>;
  inputRef: RefObject<HTMLTextAreaElement>;
  submitting: boolean;
  onSubmit: (body: string) => Promise<void>;
}

export default function CommentsSection(props: CommentsSectionProps) {
  const [body, setBody] = useState('');

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!body.trim()) return;
    await props.onSubmit(body);
    setBody('');
  }

  return (
    <Card id="comments" ref={props.sectionRef} className="scroll-mt-20">
      <div className="border-b px-6 py-4">
        <h2 className="font-semibold">
          {translate('common:auto.comments_2')}
          {props.comments?.length ?? 0})
        </h2>
      </div>
      {props.comments?.length ? (
        <div className="divide-y">
          {props.comments.map((comment) => (
            <div key={comment.id} className="px-6 py-4">
              <CommentHeader comment={comment} />
              <div className="mt-2 pl-9">
                <MarkdownRenderer
                  content={comment.body}
                  basePath={props.basePath}
                  docs={props.docs}
                  docsRouteBase={props.docsRouteBase}
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="px-6 py-8 text-center text-sm text-muted-foreground">
          {translate('common:auto.no_comments_yet')}
        </div>
      )}
      <form onSubmit={(event) => void handleSubmit(event)} className="border-t px-6 py-4">
        <Textarea
          ref={props.inputRef}
          value={body}
          onChange={(event) => setBody(event.target.value)}
          placeholder={translate('common:auto.write_a_comment')}
          rows={3}
          className="markdown-input"
        />
        <div className="mt-3 flex justify-end">
          <Button type="submit" disabled={props.submitting || !body.trim()}>
            {props.submitting
              ? translate('common:auto.posting')
              : translate('common:auto.add_comment')}
          </Button>
        </div>
      </form>
    </Card>
  );
}
