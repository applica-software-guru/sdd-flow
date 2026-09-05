import { useState } from 'react';
import { slugify } from '@/lib/slug';

export function useEditableSlug() {
  const [slug, setSlug] = useState('');
  const [edited, setEdited] = useState(false);

  return {
    slug,
    onTitleChange(title: string) {
      if (!edited) setSlug(slugify(title));
    },
    onSlugChange(value: string) {
      setEdited(true);
      setSlug(value);
    },
  };
}
