"""Pure slug utilities shared by the domain services.

Number/slug assignment (with uniqueness and insertion) lives in
`NumberingService` (app/services/numbering.py).
"""

import os
import re


def slugify(text: str) -> str:
    """Convert a string to a URL-friendly slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text or "untitled"


def parse_path_prefix(path: str) -> tuple[int | None, str | None]:
    """
    Given a file path like 'change-requests/001-fix-auth.md' or 'bugs/042-login-crash.md',
    return (number, slug) if the filename starts with a numeric prefix, else (None, None).

    Examples:
        'change-requests/001-fix-auth.md' -> (1, 'fix-auth')
        'bugs/042-login-crash.md'         -> (42, 'login-crash')
        'change-requests/my-cr.md'        -> (None, None)
    """
    filename = os.path.basename(path)
    stem = filename.removesuffix(".md")
    match = re.match(r"^(\d+)-(.+)$", stem)
    if match:
        number = int(match.group(1))
        slug = match.group(2)
        return number, slug
    return None, None
