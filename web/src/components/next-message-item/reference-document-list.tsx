import { Card, CardContent } from '@/components/ui/card';
import { useSetModalState } from '@/hooks/common-hooks';
import { Docagg } from '@/interfaces/database/chat';
import { middleEllipsis } from '@/utils/common-util';
import { buildLocalScanDocUrl } from '@/utils/local-scan-doc';
import { useState } from 'react';
import FileIcon from '../file-icon';

export function ReferenceDocumentList({ list }: { list: Docagg[] }) {
  const { visible, showModal, hideModal } = useSetModalState();
  const [selectedDocument, setSelectedDocument] = useState<Docagg>();

  const handleDocumentClick = (item: Docagg) => {
    window.open(buildLocalScanDocUrl(item.doc_id), '_blank');
  };

  return (
    <section className="flex gap-3 flex-wrap">
      {list.map((item) => (
        <Card key={item.doc_id}>
          <CardContent
            className="flex items-center p-2 space-x-2 cursor-pointer"
            onClick={() => handleDocumentClick(item)}
          >
            <FileIcon id={item.doc_id} name={item.doc_name}></FileIcon>
            <div className="text-text-sub-title-invert">
              {item.source_type === 'local_scan' && item.location
                ? item.location
                : middleEllipsis(item.doc_name)}
            </div>
          </CardContent>
        </Card>
      ))}
    </section>
  );
}
