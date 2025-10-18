'use client';

import { useState } from 'react';
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
import { useExportConfig } from '@/hooks/use-mcp-servers';
import { Download, Copy, Loader2, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

interface ExportConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ExportConfigDialog({ open, onOpenChange }: ExportConfigDialogProps) {
  const [includeGlobal, setIncludeGlobal] = useState(true);
  const [copied, setCopied] = useState(false);

  const exportMutation = useExportConfig();

  const handleClose = () => {
    setIncludeGlobal(true);
    setCopied(false);
    onOpenChange(false);
  };

  const handleExport = async () => {
    await exportMutation.mutateAsync(includeGlobal);
  };

  const handleCopyToClipboard = async () => {
    try {
      const config = await exportMutation.mutateAsync(includeGlobal);
      const jsonString = JSON.stringify(config, null, 2);
      await navigator.clipboard.writeText(jsonString);
      setCopied(true);
      toast.success('Configuration copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy to clipboard');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Export MCP Configuration</DialogTitle>
          <DialogDescription>
            Download your MCP server configuration in Claude Desktop format
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div>
              <Label>Include Global Servers</Label>
              <p className="text-xs text-gray-500">
                Include system-wide servers in the export
              </p>
            </div>
            <Switch checked={includeGlobal} onCheckedChange={setIncludeGlobal} />
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex gap-3">
              <div className="text-blue-600 mt-0.5">
                <svg
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">Compatible with:</p>
                <ul className="list-disc list-inside space-y-0.5 text-xs">
                  <li>Claude Desktop</li>
                  <li>Cursor IDE</li>
                  <li>Other MCP-compatible applications</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter>
          <div className="flex items-center gap-2 w-full">
            <Button
              type="button"
              variant="outline"
              onClick={handleCopyToClipboard}
              className="flex-1"
              disabled={exportMutation.isPending}
            >
              {copied ? (
                <>
                  <CheckCircle2 className="h-4 w-4 mr-2 text-green-600" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-2" />
                  Copy to Clipboard
                </>
              )}
            </Button>
            <Button
              type="button"
              onClick={handleExport}
              className="flex-1"
              disabled={exportMutation.isPending}
            >
              {exportMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              Download File
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
