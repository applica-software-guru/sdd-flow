// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LanguageSelector from '@/components/language-selector';
import i18n, { LANGUAGE_STORAGE_KEY, normalizedLanguage } from '@/i18n';
import { formatNumber } from '@/lib/format';

describe('internationalization', () => {
  afterEach(async () => {
    localStorage.clear();
    await i18n.changeLanguage('en');
  });

  it('normalizes supported locale variants and falls back to English', () => {
    expect(normalizedLanguage('it-IT')).toBe('it');
    expect(normalizedLanguage('en-GB')).toBe('en');
    expect(normalizedLanguage('fr-FR')).toBe('en');
  });

  it('changes language, updates the document language and persists the choice', async () => {
    const user = userEvent.setup();
    await i18n.changeLanguage('en');
    render(<LanguageSelector />);

    await user.click(screen.getByRole('button', { name: 'Language: English' }));
    await user.click(screen.getByRole('menuitem', { name: /itItaliano/i }));

    expect(i18n.resolvedLanguage).toBe('it');
    expect(document.documentElement.lang).toBe('it');
    expect(localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe('it');
    expect(screen.getByRole('button', { name: 'Lingua: Italiano' })).toBeTruthy();
  });

  it('formats numbers with an explicit locale', () => {
    expect(formatNumber(12345.5, 'en')).toBe('12,345.5');
    expect(formatNumber(12345.5, 'it')).toBe('12.345,5');
  });
});
