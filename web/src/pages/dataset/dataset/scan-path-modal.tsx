'use client';

import { ButtonLoading } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { DeleteOutlined } from '@ant-design/icons';
import { Alert, Form, Input, Select, Table, Tag } from 'antd';
import dayjs from 'dayjs';
import React from 'react';

interface ScannedDirectory {
  id: string;
  kb_id: string;
  directory_path: string;
  scan_interval_minutes: number;
  last_scan_time: string | null;
  created_at: string | null;
}

interface IProps {
  visible: boolean;
  hideModal: () => void;
  loading: boolean;
  onOk: (path: string, scanInterval?: number) => void;
  directories?: ScannedDirectory[];
  onDelete?: (id: string) => void;
  onUpdateInterval?: (id: string, interval: number) => void;
}

const ScanPathModal: React.FC<IProps> = ({
  visible,
  hideModal,
  onOk,
  loading: parentLoading,
  directories = [],
  onDelete,
  onUpdateInterval,
}) => {
  const [form] = Form.useForm();

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      onOk(values.path, values.scan_interval);
      form.resetFields();
    } catch (error) {
      console.log('Form validation failed:', error);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    hideModal();
  };

  const columns = [
    {
      title: 'Directory Path',
      dataIndex: 'directory_path',
      key: 'directory_path',
      ellipsis: true,
    },
    {
      title: 'Last Scan',
      dataIndex: 'last_scan_time',
      key: 'last_scan_time',
      render: (time: string | null) =>
        time ? dayjs(time).format('YYYY-MM-DD HH:mm') : 'Never',
    },
    {
      title: 'Interval',
      dataIndex: 'scan_interval_minutes',
      key: 'scan_interval_minutes',
      width: 100,
      render: (interval: number, record: ScannedDirectory) => (
        <Select
          value={interval}
          onChange={(val) => onUpdateInterval?.(record.id, val)}
          getPopupContainer={(trigger) => trigger.parentElement!}
          style={{ width: 90 }}
          size="small"
          options={[
            { label: '30m', value: 30 },
            { label: '1h', value: 60 },
            { label: '3h', value: 180 },
            { label: '1d', value: 1440 },
          ]}
        />
      ),
    },
    {
      title: '',
      key: 'actions',
      width: 60,
      render: (_: any, record: ScannedDirectory) => (
        <button
          type="button"
          onClick={() => onDelete?.(record.id)}
          className="text-red-500 hover:text-red-600 p-1 rounded"
          title="Delete"
        >
          <DeleteOutlined />
        </button>
      ),
    },
  ];

  return (
    <Dialog open={visible} onOpenChange={handleCancel}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Scan Local Directory</DialogTitle>
        </DialogHeader>

        {directories.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-sm">Previously Scanned</span>
              <Tag color="blue">{directories.length}</Tag>
            </div>
            <Table
              columns={columns}
              dataSource={directories}
              rowKey="id"
              size="small"
              pagination={false}
              locale={{
                emptyText: 'No directories scanned yet',
              }}
            />
          </div>
        )}

        <Alert
          message="Note: This feature scans files from the server's local filesystem."
          type="info"
          showIcon
          className="mb-4"
        />

        <Form form={form} name="scan_path" layout="vertical" autoComplete="off">
          <Form.Item
            label="Directory Path"
            name="path"
            rules={[
              { required: true, message: 'Please input directory path!' },
            ]}
          >
            <Input placeholder="/path/to/directory" />
          </Form.Item>

          <Form.Item
            label="Scan Interval"
            name="scan_interval"
            initialValue={60}
          >
            <Select
              style={{ width: '100%' }}
              options={[
                { label: 'Every 30 minutes', value: 30 },
                { label: 'Every 1 hour', value: 60 },
                { label: 'Every 3 hours', value: 180 },
                { label: 'Every day', value: 1440 },
              ]}
            />
          </Form.Item>
        </Form>

        <DialogFooter>
          <ButtonLoading variant="outline" onClick={handleCancel}>
            Cancel
          </ButtonLoading>
          <ButtonLoading loading={parentLoading} onClick={handleOk}>
            Scan
          </ButtonLoading>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ScanPathModal;
