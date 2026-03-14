import { Card, CardContent } from '@/components/ui/card';
import { useSetModalState } from '@/hooks/common-hooks';
import { Docagg } from '@/interfaces/database/chat';
import { api_host } from '@/utils/api';
import { getAuthorization } from '@/utils/authorization-util';
import { middleEllipsis } from '@/utils/common-util';
import { useState } from 'react';
import FileIcon from '../file-icon';

export function ReferenceDocumentList({ list }: { list: Docagg[] }) {
  const { visible, showModal, hideModal } = useSetModalState();
  const [selectedDocument, setSelectedDocument] = useState<Docagg>();

  const handleDocumentClick = (item: Docagg) => {
    const auth = getAuthorization();
    const docUrl = `${api_host}/document/get/${item.doc_id}`;
    const urlWithAuth = auth
      ? `${docUrl}?jwt_auth=${encodeURIComponent(auth)}`
      : docUrl;
    window.open(urlWithAuth, '_blank');
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
              {middleEllipsis(item.doc_name)}
            </div>
          </CardContent>
        </Card>
      ))}
    </section>
  );
}
