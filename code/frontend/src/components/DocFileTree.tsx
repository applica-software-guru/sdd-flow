import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import type { DocumentFile, DocStatus } from '../types';

// ── Tree node types ──────────────────────────────────────────────────────────

type FolderNode = {
  kind: 'folder';
  name: string;
  fullPath: string;
  children: TreeNode[];
};

type DocNode = {
  kind: 'doc';
  name: string;
  doc: DocumentFile;
};

type TreeNode = FolderNode | DocNode;

// ── Build tree from flat doc list ─────────────────────────────────────────────

function buildTree(docs: DocumentFile[]): TreeNode[] {
  const root: TreeNode[] = [];
  const folderMap = new Map<string, FolderNode>();

  const getOrCreateFolder = (segments: string[], upTo: number): FolderNode => {
    const fullPath = segments.slice(0, upTo).join('/');
    if (folderMap.has(fullPath)) return folderMap.get(fullPath)!;

    const node: FolderNode = {
      kind: 'folder',
      name: segments[upTo - 1],
      fullPath,
      children: [],
    };
    folderMap.set(fullPath, node);

    if (upTo === 1) {
      root.push(node);
    } else {
      const parent = getOrCreateFolder(segments, upTo - 1);
      parent.children.push(node);
    }

    return node;
  };

  for (const doc of docs) {
    const parts = doc.path.split('/').filter(Boolean);
    if (parts.length <= 1) {
      root.push({ kind: 'doc', name: parts[0] ?? doc.path, doc });
    } else {
      const folder = getOrCreateFolder(parts, parts.length - 1);
      folder.children.push({ kind: 'doc', name: parts[parts.length - 1], doc });
    }
  }

  const sortNodes = (nodes: TreeNode[]) => {
    nodes.sort((a, b) => {
      if (a.kind !== b.kind) return a.kind === 'folder' ? -1 : 1;
      return a.name.localeCompare(b.name);
    });
    for (const n of nodes) {
      if (n.kind === 'folder') sortNodes(n.children);
    }
  };

  sortNodes(root);
  return root;
}

// ── Status dot ────────────────────────────────────────────────────────────────

const STATUS_COLORS: Record<DocStatus, string> = {
  draft: 'bg-purple-400',
  new: 'bg-cyan-400',
  changed: 'bg-amber-400',
  synced: 'bg-green-400',
  deleted: 'bg-red-400',
};

function StatusDot({ status }: { status: DocStatus }) {
  return (
    <span
      className={`inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full ${STATUS_COLORS[status] ?? 'bg-slate-400'}`}
      title={status}
    />
  );
}

// ── Create doc form (inline modal) ────────────────────────────────────────────

interface CreateFormProps {
  folderPrefix: string;
  onSubmit: (title: string, path: string) => Promise<void>;
  onCancel: () => void;
  isPending: boolean;
}

function toSlug(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function CreateForm({ folderPrefix, onSubmit, onCancel, isPending }: CreateFormProps) {
  const [title, setTitle] = useState('');
  const [filename, setFilename] = useState('');
  const [filenameEdited, setFilenameEdited] = useState(false);

  const handleTitleChange = (value: string) => {
    setTitle(value);
    if (!filenameEdited) setFilename(toSlug(value));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const path = folderPrefix ? `${folderPrefix}/${filename}` : filename;
    await onSubmit(title, path);
  };

  const fullPath = folderPrefix ? `${folderPrefix}/${filename || '…'}` : (filename || '…');

  return (
    <div className="mx-2 mt-1 mb-2 rounded-md border border-blue-200 bg-blue-50 p-3 dark:border-blue-800 dark:bg-blue-950/40">
      <form onSubmit={handleSubmit} className="space-y-2">
        <input
          autoFocus
          type="text"
          placeholder="Title"
          value={title}
          onChange={(e) => handleTitleChange(e.target.value)}
          className="w-full rounded border border-slate-300 px-2 py-1 text-xs focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        />
        <input
          type="text"
          placeholder="filename"
          value={filename}
          onChange={(e) => { setFilename(e.target.value); setFilenameEdited(true); }}
          className="w-full rounded border border-slate-300 px-2 py-1 font-mono text-xs focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        />
        <p className="text-[10px] text-slate-400">path: <span className="font-mono">{fullPath}</span></p>
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={isPending || !title.trim() || !filename.trim()}
            className="rounded bg-blue-600 px-2 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {isPending ? '…' : 'Create'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="rounded px-2 py-1 text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

// ── Tree node renderer ────────────────────────────────────────────────────────

interface TreeNodeProps {
  node: TreeNode;
  depth: number;
  activeDocId?: string;
  activeFolderPath?: string;
  docUrl: (docId: string) => string;
  onCreateDoc: (title: string, path: string) => Promise<void>;
  onFolderClick?: (folderPath: string) => void;
  isCreating: boolean;
}

function TreeNodeView({ node, depth, activeDocId, activeFolderPath, docUrl, onCreateDoc, onFolderClick, isCreating }: TreeNodeProps) {
  const navigate = useNavigate();
  const [open, setOpen] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [hovered, setHovered] = useState(false);

  const indent = depth * 12;

  if (node.kind === 'doc') {
    const isActive = node.doc.id === activeDocId;
    return (
      <button
        type="button"
        onClick={() => navigate(docUrl(node.doc.id))}
        style={{ paddingLeft: `${indent + 8}px` }}
        className={`group flex w-full items-center gap-1.5 rounded py-1 pr-2 text-left text-xs transition-colors ${
          isActive
            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
            : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-700/50'
        }`}
      >
        <svg className="h-3.5 w-3.5 flex-shrink-0 text-slate-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
        </svg>
        <span className="min-w-0 flex-1 truncate">{node.doc.title || node.name}</span>
        <StatusDot status={node.doc.status} />
      </button>
    );
  }

  // Folder node
  const isFolderActive = activeFolderPath === node.fullPath;
  return (
    <div>
      <div
        style={{ paddingLeft: `${indent}px` }}
        className="group flex items-center"
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        <button
          type="button"
          onClick={() => {
            setOpen((o) => !o);
            onFolderClick?.(node.fullPath);
          }}
          className={`flex flex-1 items-center gap-1 rounded py-1 pr-1 text-left text-xs font-medium transition-colors ${
            isFolderActive
              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
              : 'text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700/50'
          }`}
        >
          <svg
            className={`h-3 w-3 flex-shrink-0 text-slate-400 transition-transform ${open ? 'rotate-90' : ''}`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
          </svg>
          <svg className="h-3.5 w-3.5 flex-shrink-0 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
          </svg>
          <span className="min-w-0 flex-1 truncate">{node.name}</span>
        </button>
        {hovered && (
          <button
            type="button"
            title="New document here"
            onClick={(e) => { e.stopPropagation(); setOpen(true); setShowCreate(true); }}
            className="mr-1 flex-shrink-0 rounded p-0.5 text-slate-400 hover:bg-slate-200 hover:text-blue-600 dark:hover:bg-slate-700 dark:hover:text-blue-400"
          >
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
          </button>
        )}
      </div>

      {open && (
        <div>
          {showCreate && (
            <CreateForm
              folderPrefix={node.fullPath}
              onSubmit={async (title, path) => {
                await onCreateDoc(title, path);
                setShowCreate(false);
              }}
              onCancel={() => setShowCreate(false)}
              isPending={isCreating}
            />
          )}
          {node.children.map((child) => (
            <TreeNodeView
              key={child.kind === 'doc' ? child.doc.id : child.fullPath}
              node={child}
              depth={depth + 1}
              activeDocId={activeDocId}
              activeFolderPath={activeFolderPath}
              docUrl={docUrl}
              onCreateDoc={onCreateDoc}
              onFolderClick={onFolderClick}
              isCreating={isCreating}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Public component ──────────────────────────────────────────────────────────

export interface DocFileTreeProps {
  docs: DocumentFile[];
  activeDocId?: string;
  activeFolderPath?: string;
  docUrl: (docId: string) => string;
  onCreateDoc: (title: string, path: string) => Promise<void>;
  onFolderClick?: (folderPath: string) => void;
  isCreating?: boolean;
}

export default function DocFileTree({ docs, activeDocId, activeFolderPath, docUrl, onCreateDoc, onFolderClick, isCreating = false }: DocFileTreeProps) {
  const [showRootCreate, setShowRootCreate] = useState(false);
  const tree = buildTree(docs);

  const handleRootCreate = useCallback(async (title: string, path: string) => {
    await onCreateDoc(title, path);
    setShowRootCreate(false);
  }, [onCreateDoc]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto py-1">
        {tree.length === 0 && (
          <p className="px-3 py-4 text-xs text-slate-400 text-center">No documents yet</p>
        )}
        {tree.map((node) => (
          <TreeNodeView
            key={node.kind === 'doc' ? node.doc.id : node.fullPath}
            node={node}
            depth={0}
            activeDocId={activeDocId}
            activeFolderPath={activeFolderPath}
            docUrl={docUrl}
            onCreateDoc={onCreateDoc}
            onFolderClick={onFolderClick}
            isCreating={isCreating}
          />
        ))}
      </div>

      <div className="border-t border-slate-200 pt-2 pb-1 dark:border-slate-700">
        {showRootCreate ? (
          <CreateForm
            folderPrefix=""
            onSubmit={handleRootCreate}
            onCancel={() => setShowRootCreate(false)}
            isPending={isCreating}
          />
        ) : (
          <button
            type="button"
            onClick={() => setShowRootCreate(true)}
            className="flex w-full items-center gap-1.5 rounded px-2 py-1.5 text-xs text-slate-500 hover:bg-slate-100 hover:text-blue-600 dark:hover:bg-slate-700/50 dark:hover:text-blue-400"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            New document
          </button>
        )}
      </div>
    </div>
  );
}
