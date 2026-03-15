'use client';

import { useState, useEffect } from 'react';
import { Save, Loader2 } from 'lucide-react';
import StatusBadge from '@/components/StatusBadge';
import { getSettings, updateSettings, getStatus } from '@/lib/api';

interface Settings {
  ollama_url: string;
  llm_model: string;
  embedding_model: string;
  chromadb_host: string;
  chromadb_port: number;
}

interface ServiceStatus {
  ollama: boolean;
  chromadb: boolean;
  overall: boolean;
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({
    ollama_url: '',
    llm_model: '',
    embedding_model: '',
    chromadb_host: '',
    chromadb_port: 8000,
  });
  const [status, setStatus] = useState<ServiceStatus>({
    ollama: false,
    chromadb: false,
    overall: false,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadSettings = async () => {
    try {
      setError(null);
      const data = await getSettings();
      setSettings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings');
      console.error('Load settings error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadStatus = async () => {
    try {
      const data = await getStatus();
      setStatus(data);
    } catch (err) {
      console.error('Load status error:', err);
    }
  };

  useEffect(() => {
    loadSettings();
    loadStatus();

    // Refresh status every 30 seconds
    const interval = setInterval(loadStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await updateSettings(settings);
      setSuccessMessage('Settings saved successfully!');
      // Reload status after saving
      setTimeout(() => loadStatus(), 1000);
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings');
      console.error('Save settings error:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleChange = (field: keyof Settings, value: string | number) => {
    setSettings((prev) => ({ ...prev, [field]: value }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-slate-700 bg-slate-900 px-6 py-4">
        <h1 className="text-2xl font-semibold text-slate-100">Settings</h1>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <div className="max-w-3xl mx-auto space-y-8">
          {/* Messages */}
          {error && (
            <div className="bg-red-900/20 border border-red-700 text-red-400 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
          {successMessage && (
            <div className="bg-green-900/20 border border-green-700 text-green-400 px-4 py-3 rounded-lg">
              {successMessage}
            </div>
          )}

          {/* Service Status */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Service Status</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center justify-between p-4 bg-slate-900 rounded-lg border border-slate-700">
                <span className="text-slate-300">Ollama</span>
                <StatusBadge status={status.ollama} />
              </div>
              <div className="flex items-center justify-between p-4 bg-slate-900 rounded-lg border border-slate-700">
                <span className="text-slate-300">ChromaDB</span>
                <StatusBadge status={status.chromadb} />
              </div>
              <div className="flex items-center justify-between p-4 bg-slate-900 rounded-lg border border-slate-700">
                <span className="text-slate-300">Overall</span>
                <StatusBadge status={status.overall} />
              </div>
            </div>
          </div>

          {/* Settings Form */}
          <form onSubmit={handleSubmit} className="card space-y-6">
            <h2 className="text-xl font-semibold">Configuration</h2>

            {/* Ollama Settings */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-slate-200 border-b border-slate-700 pb-2">
                Ollama Configuration
              </h3>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Ollama URL
                </label>
                <input
                  type="text"
                  value={settings.ollama_url}
                  onChange={(e) => handleChange('ollama_url', e.target.value)}
                  placeholder="http://ollama:11434"
                  className="input-field"
                  required
                />
                <p className="text-xs text-slate-500 mt-1">
                  Base URL for the Ollama service
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  LLM Model
                </label>
                <input
                  type="text"
                  value={settings.llm_model}
                  onChange={(e) => handleChange('llm_model', e.target.value)}
                  placeholder="llama3.2"
                  className="input-field"
                  required
                />
                <p className="text-xs text-slate-500 mt-1">
                  Model to use for text generation
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Embedding Model
                </label>
                <input
                  type="text"
                  value={settings.embedding_model}
                  onChange={(e) => handleChange('embedding_model', e.target.value)}
                  placeholder="nomic-embed-text"
                  className="input-field"
                  required
                />
                <p className="text-xs text-slate-500 mt-1">
                  Model to use for generating embeddings
                </p>
              </div>
            </div>

            {/* ChromaDB Settings */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-slate-200 border-b border-slate-700 pb-2">
                ChromaDB Configuration
              </h3>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  ChromaDB Host
                </label>
                <input
                  type="text"
                  value={settings.chromadb_host}
                  onChange={(e) => handleChange('chromadb_host', e.target.value)}
                  placeholder="chromadb"
                  className="input-field"
                  required
                />
                <p className="text-xs text-slate-500 mt-1">
                  Hostname for the ChromaDB service
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  ChromaDB Port
                </label>
                <input
                  type="number"
                  value={settings.chromadb_port}
                  onChange={(e) => handleChange('chromadb_port', parseInt(e.target.value))}
                  placeholder="8000"
                  className="input-field"
                  required
                  min="1"
                  max="65535"
                />
                <p className="text-xs text-slate-500 mt-1">
                  Port number for the ChromaDB service
                </p>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end pt-4 border-t border-slate-700">
              <button
                type="submit"
                disabled={isSaving}
                className="btn-primary flex items-center gap-2 px-6"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-5 h-5" />
                    Save Settings
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
