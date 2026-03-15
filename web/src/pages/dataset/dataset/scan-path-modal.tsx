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
import { useTranslation } from 'react-i18next';

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
  const { t } = useTranslation();
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
      title: t('scanDirectory.directoryPath'),
      dataIndex: 'directory_path',
      key: 'directory_path',
      ellipsis: true,
    },
    {
      title: t('scanDirectory.lastScan'),
      dataIndex: 'last_scan_time',
      key: 'last_scan_time',
      render: (time: string | null) =>
        time
          ? dayjs(time).format('YYYY-MM-DD HH:mm:ss')
          : t('scanDirectory.never'),
    },
    {
      title: t('scanDirectory.interval'),
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
            { label: '10m', value: 10 },
            { label: '30m', value: 30 },
            { label: '1h', value: 60 },
            { label: '3h', value: 180 },
            { label: '1d', value: 1440 },
            { label: '1w', value: 10080 },
            { label: '4w', value: 40320 },
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
          title={t('scanDirectory.delete')}
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
          <DialogTitle>{t('scanDirectory.title')}</DialogTitle>
        </DialogHeader>

        {directories.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-sm">
                {t('scanDirectory.previouslyScanned')}
              </span>
              <Tag color="blue">{directories.length}</Tag>
            </div>
            <Table
              columns={columns}
              dataSource={directories}
              rowKey="id"
              size="small"
              pagination={false}
              locale={{
                emptyText: t('scanDirectory.noDirectoriesScanned'),
              }}
            />
          </div>
        )}

        <Alert
          message={t('scanDirectory.note')}
          type="info"
          showIcon
          className="mb-4"
        />

        <Form form={form} name="scan_path" layout="vertical" autoComplete="off">
          <Form.Item
            label={t('scanDirectory.directoryPath')}
            name="path"
            rules={[
              { required: true, message: t('scanDirectory.pathPlaceholder') },
            ]}
          >
            <Input placeholder={t('scanDirectory.pathPlaceholder')} />
          </Form.Item>

          <Form.Item
            label={t('scanDirectory.scanInterval')}
            name="scan_interval"
            initialValue={40320}
          >
            <Select
              style={{ width: '100%' }}
              getPopupContainer={(trigger) => trigger.parentElement!}
              options={[
                { label: t('scanDirectory.every10Minutes'), value: 10 },
                { label: t('scanDirectory.every30Minutes'), value: 30 },
                { label: t('scanDirectory.every1Hour'), value: 60 },
                { label: t('scanDirectory.every3Hours'), value: 180 },
                { label: t('scanDirectory.everyDay'), value: 1440 },
                { label: t('scanDirectory.everyWeek'), value: 10080 },
                { label: t('scanDirectory.every4Weeks'), value: 40320 },
              ]}
            />
          </Form.Item>
        </Form>

        <DialogFooter>
          <ButtonLoading variant="outline" onClick={handleCancel}>
            {t('scanDirectory.cancel')}
          </ButtonLoading>
          <ButtonLoading loading={parentLoading} onClick={handleOk}>
            {t('scanDirectory.scan')}
          </ButtonLoading>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ScanPathModal;
