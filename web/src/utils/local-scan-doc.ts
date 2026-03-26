import { api_host } from '@/utils/api';
import { getAuthorization } from '@/utils/authorization-util';

export function buildLocalScanDocUrl(docId: string): string {
  const auth = getAuthorization();
  const docUrl = `${api_host}/document/get/${docId}`;
  return auth ? `${docUrl}?jwt_auth=${encodeURIComponent(auth)}` : docUrl;
}
