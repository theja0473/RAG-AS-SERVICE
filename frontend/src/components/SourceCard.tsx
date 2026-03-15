'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, FileText } from 'lucide-react';

interface Source {
  source: string;
  content: string;
  relevance_score: number;
}

interface SourceCardProps {
  source: Source;
  index: number;
}

export default function SourceCard({ source, index }: SourceCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getRelevanceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-400 bg-green-900/30';
    if (score >= 0.6) return 'text-yellow-400 bg-yellow-900/30';
    return 'text-orange-400 bg-orange-900/30';
  };

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 hover:bg-slate-800 transition-colors"
      >
        <div className="flex items-center gap-3 flex-1">
          <div className="flex items-center gap-2">
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-400" />
            )}
            <FileText className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-left flex-1">
            <p className="text-sm font-medium text-slate-300 truncate">
              {source.source}
            </p>
          </div>
        </div>
        <div className={`px-2 py-1 rounded text-xs font-medium ${getRelevanceColor(source.relevance_score)}`}>
          {(source.relevance_score * 100).toFixed(0)}%
        </div>
      </button>

      {isExpanded && (
        <div className="px-3 pb-3 border-t border-slate-700 bg-slate-950/50">
          <p className="text-sm text-slate-400 mt-3 leading-relaxed">
            {source.content}
          </p>
        </div>
      )}
    </div>
  );
}
