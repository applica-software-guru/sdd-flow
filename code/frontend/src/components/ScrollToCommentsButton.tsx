import { useEffect, useState, type RefObject } from 'react';

interface ScrollToCommentsButtonProps {
  /** Container of the comments section to scroll to (must render id="comments"). */
  targetRef: RefObject<HTMLElement | null>;
  commentCount: number;
  /** Focus target (the comment textarea) after scrolling. */
  inputRef?: RefObject<HTMLTextAreaElement | null>;
}

/**
 * Floating action button that smooth-scrolls to the comments section of a
 * CR/bug detail page. Visible only while the comments section is below the
 * fold; hides automatically once the section is (partially) in view.
 */
export default function ScrollToCommentsButton({
  targetRef,
  commentCount,
  inputRef,
}: ScrollToCommentsButtonProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const target = targetRef.current;
    if (!target || typeof IntersectionObserver === 'undefined') {
      // Graceful degradation: keep the button available.
      setVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        // Visible only when the comments section is completely out of view.
        setVisible(entries.every((e) => e.intersectionRatio === 0));
      },
      { threshold: 0 },
    );
    observer.observe(target);
    return () => observer.disconnect();
  }, [targetRef]);

  if (commentCount === undefined) return null;

  const handleClick = () => {
    const target = targetRef.current;
    if (!target) return;
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    // Focus the comment input after the scroll settles.
    window.setTimeout(() => inputRef?.current?.focus(), 450);
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label="Scroll to comments"
      className={`fixed bottom-6 right-6 z-40 flex items-center gap-2 rounded-full bg-blue-600 py-3 pl-4 pr-5 text-sm font-medium text-white shadow-lg transition-all duration-200 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:bg-blue-500 dark:hover:bg-blue-600 dark:focus:ring-offset-slate-900 ${
        visible
          ? 'translate-y-0 opacity-100'
          : 'pointer-events-none translate-y-4 opacity-0'
      }`}
    >
      {/* chat bubble icon */}
      <svg
        className="h-5 w-5"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.8}
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155"
        />
      </svg>
      Comments
      <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-white/20 px-1.5 text-xs font-semibold">
        {commentCount}
      </span>
    </button>
  );
}
