'use client';

import { useState, useEffect } from 'react';
import { Trash2, Loader2, Link as LinkIcon, RefreshCw } from 'lucide-react';
import FileUpload from '@/components/FileUpload';
import { fetchDocuments, deleteDocument, ingestUrl } from '@/lib/api';

interface Document {
  id: string;
  filename: string;
  file_type: string;
  status: 'processing' | 'ready' | 'error';
  chunk_count: number;
  uploaded_at: string;
  error_message?: string;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [urlInput, setUrlInput] = useState('');
  const [isIngestingUrl, setIsIngestingUrl] = useState(false);

  const loadDocuments = async () => {
    try {
      setError(null);
      const docs = await fetchDocuments();
      setDocuments(docs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
      console.error('Load documents error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((doc) => doc.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document');
      console.error('Delete error:', err);
    }
  };

  const handleUrlIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim() || isIngestingUrl) return;

    setIsIngestingUrl(true);
    setError(null);

    try {
      await ingestUrl(urlInput.trim());
      setUrlInput('');
      // Reload documents after a short delay to allow processing to start
      setTimeout(() => loadDocuments(), 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to ingest URL');
      console.error('URL ingest error:', err);
    } finally {
      setIsIngestingUrl(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      processing: 'bg-yellow-900/30 text-yellow-400 border-yellow-700',
      ready: 'bg-green-900/30 text-green-400 border-green-700',
      error: 'bg-red-900/30 text-red-400 border-red-700',
    };
    return badges[status as keyof typeof badges] || badges.processing;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-slate-700 bg-slate-900 px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-slate-100">Documents</h1>
          <button
            onClick={loadDocuments}
            className="flex items-center gap-2 btn-secondary text-sm"
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <div className="max-w-6xl mx-auto space-y-8">
          {/* Error Message */}
          {error && (
            <div className="bg-red-900/20 border border-red-700 text-red-400 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {/* File Upload Section */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Upload Documents</h2>
            <FileUpload onUploadComplete={loadDocuments} />
          </div>

          {/* URL Ingest Section */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Ingest from URL</h2>
            <form onSubmit={handleUrlIngest} className="flex gap-3">
              <div className="flex-1">
                <input
                  type="url"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://example.com/document.pdf"
                  className="input-field"
                  disabled={isIngestingUrl}
                />
              </div>
              <button
                type="submit"
                disabled={!urlInput.trim() || isIngestingUrl}
                className="btn-primary flex items-center gap-2 px-6"
              >
                {isIngestingUrl ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Ingesting...
                  </>
                ) : (
                  <>
                    <LinkIcon className="w-5 h-5" />
                    Ingest URL
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Documents Table */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">
              Uploaded Documents ({documents.length})
            </h2>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                <p>No documents uploaded yet.</p>
                <p className="text-sm mt-2">Upload your first document above to get started.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left py-3 px-4 font-medium text-slate-300">Filename</th>
                      <th className="text-left py-3 px-4 font-medium text-slate-300">Type</th>
                      <th className="text-left py-3 px-4 font-medium text-slate-300">Status</th>
                      <th className="text-left py-3 px-4 font-medium text-slate-300">Chunks</th>
                      <th className="text-left py-3 px-4 font-medium text-slate-300">Uploaded</th>
                      <th className="text-left py-3 px-4 font-medium text-slate-300">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map((doc) => (
                      <tr key={doc.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                        <td className="py-3 px-4">
                          <div className="font-medium">{doc.filename}</div>
                          {doc.error_message && (
                            <div className="text-xs text-red-400 mt-1">{doc.error_message}</div>
                          )}
                        </td>
                        <td className="py-3 px-4 text-slate-400 uppercase text-sm">
                          {doc.file_type}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusBadge(
                              doc.status
                            )}`}
                          >
                            {doc.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-400">{doc.chunk_count}</td>
                        <td className="py-3 px-4 text-slate-400 text-sm">
                          {new Date(doc.uploaded_at).toLocaleDateString()}
                        </td>
                        <td className="py-3 px-4">
                          <button
                            onClick={() => handleDelete(doc.id)}
                            className="text-red-400 hover:text-red-300 p-2 rounded hover:bg-red-900/20 transition-colors"
                            title="Delete document"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
