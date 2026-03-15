'use client';

import { useState, useCallback } from 'react';
import { Upload, File, X, Loader2, CheckCircle2 } from 'lucide-react';
import { uploadDocument } from '@/lib/api';

interface FileUploadProps {
  onUploadComplete: () => void;
}

interface UploadingFile {
  file: File;
  progress: number;
  status: 'uploading' | 'success' | 'error';
  error?: string;
}

export default function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);

  const acceptedTypes = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain',
  ];

  const isValidFile = (file: File) => {
    return acceptedTypes.includes(file.type);
  };

  const uploadFile = async (file: File) => {
    const uploadingFile: UploadingFile = {
      file,
      progress: 0,
      status: 'uploading',
    };

    setUploadingFiles((prev) => [...prev, uploadingFile]);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadingFiles((prev) =>
          prev.map((f) =>
            f.file === file && f.progress < 90
              ? { ...f, progress: f.progress + 10 }
              : f
          )
        );
      }, 200);

      await uploadDocument(file);

      clearInterval(progressInterval);

      setUploadingFiles((prev) =>
        prev.map((f) =>
          f.file === file ? { ...f, progress: 100, status: 'success' as const } : f
        )
      );

      // Remove from list after 2 seconds
      setTimeout(() => {
        setUploadingFiles((prev) => prev.filter((f) => f.file !== file));
        onUploadComplete();
      }, 2000);
    } catch (error) {
      setUploadingFiles((prev) =>
        prev.map((f) =>
          f.file === file
            ? {
                ...f,
                status: 'error' as const,
                error: error instanceof Error ? error.message : 'Upload failed',
              }
            : f
        )
      );
    }
  };

  const handleFiles = useCallback((files: FileList) => {
    const validFiles = Array.from(files).filter(isValidFile);
    validFiles.forEach(uploadFile);

    if (validFiles.length < files.length) {
      alert('Some files were skipped. Only PDF, DOCX, XLSX, and TXT files are supported.');
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files) {
        handleFiles(e.dataTransfer.files);
      }
    },
    [handleFiles]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  };

  const removeFile = (file: File) => {
    setUploadingFiles((prev) => prev.filter((f) => f.file !== file));
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-500/10'
            : 'border-slate-700 hover:border-slate-600'
        }`}
      >
        <Upload className={`w-12 h-12 mx-auto mb-4 ${isDragging ? 'text-blue-400' : 'text-slate-500'}`} />
        <p className="text-slate-300 mb-2">
          Drag and drop files here, or{' '}
          <label className="text-blue-400 hover:text-blue-300 cursor-pointer underline">
            browse
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.xlsx,.txt"
              onChange={handleFileInput}
              className="hidden"
            />
          </label>
        </p>
        <p className="text-sm text-slate-500">
          Supported formats: PDF, DOCX, XLSX, TXT
        </p>
      </div>

      {/* Uploading Files List */}
      {uploadingFiles.length > 0 && (
        <div className="space-y-2">
          {uploadingFiles.map((uploadingFile, index) => (
            <div
              key={index}
              className="flex items-center gap-3 p-3 bg-slate-900 border border-slate-700 rounded-lg"
            >
              <File className="w-5 h-5 text-blue-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-300 truncate">
                  {uploadingFile.file.name}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  {uploadingFile.status === 'uploading' && (
                    <>
                      <div className="flex-1 bg-slate-800 rounded-full h-1.5">
                        <div
                          className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${uploadingFile.progress}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate-500">
                        {uploadingFile.progress}%
                      </span>
                    </>
                  )}
                  {uploadingFile.status === 'success' && (
                    <div className="flex items-center gap-1 text-green-400 text-xs">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Uploaded</span>
                    </div>
                  )}
                  {uploadingFile.status === 'error' && (
                    <p className="text-xs text-red-400">{uploadingFile.error}</p>
                  )}
                </div>
              </div>
              {uploadingFile.status === 'uploading' && (
                <Loader2 className="w-5 h-5 text-blue-400 animate-spin flex-shrink-0" />
              )}
              {uploadingFile.status === 'success' && (
                <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
              )}
              {uploadingFile.status === 'error' && (
                <button
                  onClick={() => removeFile(uploadingFile.file)}
                  className="text-red-400 hover:text-red-300 flex-shrink-0"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
