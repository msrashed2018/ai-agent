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
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { SessionTemplateResponse } from '@/types/api';
import { useUpdateTemplateSharing } from '@/hooks/use-session-templates';
import { Loader2, Globe, Building2 } from 'lucide-react';

interface SharingDialogProps {
  template: SessionTemplateResponse;
  open: boolean;
  onClose: () => void;
}

export function SharingDialog({ template, open, onClose }: SharingDialogProps) {
  const updateSharing = useUpdateTemplateSharing();
  const [isPublic, setIsPublic] = useState(template.is_public);
  const [isOrgShared, setIsOrgShared] = useState(template.is_organization_shared);

  const handleSubmit = async () => {
    try {
      await updateSharing.mutateAsync({
        templateId: template.id,
        data: {
          is_public: isPublic,
          is_organization_shared: isOrgShared,
        },
      });
      onClose();
    } catch (error) {
      // Error handled by mutation hook
    }
  };

  const handleClose = () => {
    // Reset to original values
    setIsPublic(template.is_public);
    setIsOrgShared(template.is_organization_shared);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Sharing Settings</DialogTitle>
          <DialogDescription>
            Manage who can access and use this template
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Template Info */}
          <div className="bg-gray-50 p-3 rounded-md">
            <p className="font-medium text-sm">{template.name}</p>
            {template.description && (
              <p className="text-xs text-gray-600 mt-1">{template.description}</p>
            )}
          </div>

          {/* Public Sharing */}
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <Switch
                id="is_public"
                checked={isPublic}
                onCheckedChange={(checked: boolean) => setIsPublic(checked)}
              />
              <div className="flex-1">
                <Label htmlFor="is_public" className="cursor-pointer flex items-center gap-2">
                  <Globe className="h-4 w-4 text-blue-600" />
                  <span className="font-medium">Public</span>
                </Label>
                <p className="text-sm text-gray-500 mt-1">
                  Anyone can discover and use this template. It will appear in the public template gallery.
                </p>
              </div>
            </div>
          </div>

          {/* Organization Sharing */}
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <Switch
                id="is_organization_shared"
                checked={isOrgShared}
                onCheckedChange={(checked: boolean) => setIsOrgShared(checked)}
              />
              <div className="flex-1">
                <Label htmlFor="is_organization_shared" className="cursor-pointer flex items-center gap-2">
                  <Building2 className="h-4 w-4 text-purple-600" />
                  <span className="font-medium">Organization</span>
                </Label>
                <p className="text-sm text-gray-500 mt-1">
                  Members of your organization can discover and use this template.
                </p>
              </div>
            </div>
          </div>

          {/* Privacy Notice */}
          {!isPublic && !isOrgShared && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
              <p className="text-sm text-yellow-800">
                This template is private and only visible to you.
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={updateSharing.isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={updateSharing.isPending}>
            {updateSharing.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
