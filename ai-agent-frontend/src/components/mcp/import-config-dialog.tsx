'use client';

import { useState, useRef } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { useImportConfig } from '@/hooks/use-mcp-servers';
import { Upload, FileJson, Loader2, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ImportConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ImportConfigDialog({ open, onOpenChange }: ImportConfigDialogProps) {
  const [file, setFile] = useState<File | null>(null);
  const [overrideExisting, setOverrideExisting] = useState(false);
  const [preview, setPreview] = useState<any>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const importMutation = useImportConfig();

  const handleClose = () => {
    setFile(null);
    setOverrideExisting(false);
    setPreview(null);
    onOpenChange(false);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = async (selectedFile: File) => {
    if (!selectedFile.name.endsWith('.json')) {
      return;
    }

    setFile(selectedFile);

    // Try to parse and preview
    try {
      const text = await selectedFile.text();
      const json = JSON.parse(text);
      setPreview(json);
    } catch (error) {
      console.error('Failed to parse JSON:', error);
      setPreview({ error: 'Invalid JSON file' });
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleImport = async () => {
    if (!file) return;

    await importMutation.mutateAsync({
      file,
      overrideExisting,
    });

    handleClose();
  };

  const serversCount = preview?.mcpServers ? Object.keys(preview.mcpServers).length : 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Import MCP Configuration</DialogTitle>
          <DialogDescription>
            Upload a Claude Desktop config file to import MCP servers
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* File Upload */}
          <div
            className={cn(
              'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
              dragActive ? 'border-primary bg-primary/5' : 'border-gray-300',
              file && 'border-green-500 bg-green-50'
            )}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              onChange={handleFileInputChange}
              className="hidden"
            />

            {!file ? (
              <div className="space-y-4">
                <div className="flex justify-center">
                  <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center">
                    <Upload className="h-8 w-8 text-gray-400" />
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium">
                    Drag and drop your config file here, or
                  </p>
                  <Button
                    type="button"
                    variant="link"
                    onClick={() => fileInputRef.current?.click()}
                    className="p-0 h-auto"
                  >
                    browse files
                  </Button>
                </div>
                <p className="text-xs text-gray-500">Accepts .json files only</p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex justify-center">
                  <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
                    <FileJson className="h-8 w-8 text-green-600" />
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium">{file.name}</p>
                  <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(2)} KB</p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setFile(null);
                    setPreview(null);
                  }}
                >
                  Change File
                </Button>
              </div>
            )}
          </div>

          {/* Preview */}
          {preview && !preview.error && (
            <div className="border rounded-lg p-4 bg-gray-50">
              <h4 className="text-sm font-medium mb-2">Preview</h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Servers found:</span>
                  <span className="font-medium">{serversCount}</span>
                </div>
                {serversCount > 0 && (
                  <div className="text-xs space-y-1">
                    {Object.keys(preview.mcpServers).slice(0, 5).map((serverName) => (
                      <div key={serverName} className="flex items-center gap-2">
                        <CheckCircle2 className="h-3 w-3 text-green-600" />
                        <span>{serverName}</span>
                      </div>
                    ))}
                    {serversCount > 5 && (
                      <div className="text-gray-500">...and {serversCount - 5} more</div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {preview?.error && (
            <div className="border border-red-200 rounded-lg p-4 bg-red-50">
              <div className="flex items-center gap-2 text-red-800">
                <XCircle className="h-4 w-4" />
                <span className="text-sm font-medium">{preview.error}</span>
              </div>
            </div>
          )}

          {/* Options */}
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div>
              <Label>Override Existing Servers</Label>
              <p className="text-xs text-gray-500">
                Replace servers with the same name
              </p>
            </div>
            <Switch checked={overrideExisting} onCheckedChange={setOverrideExisting} />
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleImport}
            disabled={!file || !!preview?.error || importMutation.isPending}
          >
            {importMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            Import Configuration
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
