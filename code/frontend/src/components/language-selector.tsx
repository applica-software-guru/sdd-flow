import { Check, Languages } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { normalizedLanguage, type SupportedLanguage } from '@/i18n';

const languages = ['en', 'it'] as const;

export default function LanguageSelector() {
  const { i18n, t } = useTranslation('common');
  const current = normalizedLanguage(i18n.resolvedLanguage ?? i18n.language);

  const label = (language: SupportedLanguage) =>
    language === 'en' ? t('language.english') : t('language.italian');

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5 px-2"
          aria-label={`${t('language.label')}: ${label(current)}`}
        >
          <Languages aria-hidden="true" />
          <span className="text-xs font-semibold uppercase">{current}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-36">
        {languages.map((language) => (
          <DropdownMenuItem
            key={language}
            onSelect={() => void i18n.changeLanguage(language)}
            aria-current={current === language ? 'true' : undefined}
          >
            <span className="w-5 text-xs font-semibold uppercase">{language}</span>
            {label(language)}
            {current === language && <Check className="ml-auto" aria-hidden="true" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
