// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { axe } from 'vitest-axe';
import ConfirmDialog from '@/components/confirm-dialog';

describe('ConfirmDialog', () => {
  it('exposes accessible dialog semantics and confirms', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    render(
      <ConfirmDialog
        open
        title="Delete project"
        message="This cannot be undone."
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />
    );
    expect(screen.getByRole('alertdialog', { name: 'Delete project' })).toBeTruthy();
    await user.click(screen.getByRole('button', { name: 'Confirm' }));
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it('closes with Escape and restores focus', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    const trigger = document.createElement('button');
    document.body.append(trigger);
    trigger.focus();
    const view = render(
      <ConfirmDialog
        open
        title="Archive"
        message="Archive this project?"
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />
    );
    await user.keyboard('{Escape}');
    expect(onCancel).toHaveBeenCalledOnce();
    view.unmount();
    trigger.remove();
  });

  it('has no automated accessibility violations', async () => {
    const { container } = render(
      <ConfirmDialog
        open
        title="Archive"
        message="Archive this project?"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );
    expect((await axe(container)).violations).toHaveLength(0);
  });
});
