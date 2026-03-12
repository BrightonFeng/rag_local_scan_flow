import { useSetModalState } from '@/hooks/common-hooks';
import { DocumentApiAction } from '@/hooks/use-document-request';
import {
  deleteScannedDirectory,
  getScannedDirectories,
  scanPath,
  updateScannedDirectory,
} from '@/services/knowledge-service';
import { useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import { useCallback, useEffect, useState } from 'react';

interface ScannedDirectory {
  id: string;
  kb_id: string;
  directory_path: string;
  scan_interval_minutes: number;
  last_scan_time: string | null;
  created_at: string | null;
}

export const useScanPath = (kbId: string) => {
  const {
    visible: scanPathVisible,
    hideModal: hideScanPathModal,
    showModal: showScanPathModal,
  } = useSetModalState();

  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);
  const [directories, setDirectories] = useState<ScannedDirectory[]>([]);

  const loadDirectories = useCallback(async () => {
    if (!kbId) {
      return;
    }

    try {
      const res = await getScannedDirectories(kbId);
      if (res.data && res.data.code === 0) {
        setDirectories(res.data.data || []);
      }
    } catch (error) {
      console.error('Failed to load directories:', error);
    }
  }, [kbId]);

  useEffect(() => {
    if (scanPathVisible && kbId) {
      loadDirectories();
    }
  }, [scanPathVisible, kbId, loadDirectories]);

  const onScanPathOk = useCallback(
    async (path: string, scanInterval?: number) => {
      if (!kbId) {
        message.error('Knowledge base ID is missing');
        return;
      }

      setLoading(true);
      try {
        const ret = await scanPath(kbId, path, scanInterval);

        const innerData = ret.data;
        if (innerData && innerData.code === 0) {
          const imported = innerData.data?.imported || [];
          if (imported.length > 0) {
            message.success(`Successfully scanned ${imported.length} files`);
          } else {
            message.info(
              innerData.message || 'No files found in the specified path',
            );
          }
          loadDirectories();
          queryClient.invalidateQueries({
            queryKey: [DocumentApiAction.FetchDocumentList],
          });
          hideScanPathModal();
        } else {
          const errMsg = innerData?.message || 'Failed to scan path';
          message.error(errMsg);
        }
      } catch (error: any) {
        const errMsg =
          error?.response?.data?.message ||
          error?.message ||
          'Failed to scan path';
        message.error(errMsg);
      } finally {
        setLoading(false);
      }
    },
    [kbId, hideScanPathModal, loadDirectories],
  );

  const onDelete = useCallback(
    async (id: string) => {
      try {
        const res = await deleteScannedDirectory(id);
        if (res.data && res.data.code === 0) {
          message.success('Directory removed from scan list');
          loadDirectories();
        } else {
          message.error(res.data?.message || 'Failed to delete');
        }
      } catch (error: any) {
        message.error(error?.response?.data?.message || 'Failed to delete');
      }
    },
    [loadDirectories],
  );

  const onUpdateInterval = useCallback(
    async (id: string, interval: number) => {
      try {
        const res = await updateScannedDirectory(id, interval);
        if (res.data && res.data.code === 0) {
          message.success('Scan interval updated');
          loadDirectories();
        } else {
          message.error(res.data?.message || 'Failed to update');
        }
      } catch (error: any) {
        message.error(error?.response?.data?.message || 'Failed to update');
      }
    },
    [loadDirectories],
  );

  return {
    scanPathLoading: loading,
    onScanPathOk,
    scanPathVisible,
    hideScanPathModal,
    showScanPathModal,
    directories,
    onDelete,
    onUpdateInterval,
  };
};
