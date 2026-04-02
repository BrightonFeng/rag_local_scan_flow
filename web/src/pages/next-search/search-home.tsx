import { Input } from '@/components/originui/input';
import Spotlight from '@/components/spotlight';
import message from '@/components/ui/message';
import { IUserInfo } from '@/interfaces/database/user-setting';
import { Search } from 'lucide-react';
import { Dispatch, SetStateAction } from 'react';
import { useTranslation } from 'react-i18next';
import './index.less';

export default function SearchPage({
  isSearching,
  setIsSearching,
  searchText,
  setSearchText,
  userInfo,
  canSearch,
}: {
  isSearching: boolean;
  setIsSearching: Dispatch<SetStateAction<boolean>>;
  searchText: string;
  setSearchText: Dispatch<SetStateAction<string>>;
  userInfo?: IUserInfo;
  canSearch?: boolean;
}) {
  // const { data: userInfo } = useFetchUserInfo();
  const { t } = useTranslation();
  return (
    <section className="relative w-full flex transition-all justify-center items-center mt-8">
      <div className="relative z-10 px-8 pt-8 flex text-transparent flex-col justify-center items-center w-[780px]">
        <div className="rounded-lg text-primary text-xl sticky flex justify-center w-full transform scale-100 p-6">
          {!isSearching && <Spotlight className="z-0" />}
          <div className="flex flex-col justify-center items-center w-full">
            {!isSearching && <></>}

            <div className="relative w-full">
              <Input
                placeholder={t('search.searchGreeting')}
                className="w-full rounded-full py-7 px-4 pr-10 text-text-primary text-lg bg-bg-base delay-700"
                value={searchText}
                onKeyUp={(e) => {
                  if (e.key === 'Enter') {
                    if (canSearch === false) {
                      message.warning(t('search.chooseDataset'));
                      return;
                    }
                    setIsSearching(!isSearching);
                  }
                }}
                onChange={(e) => {
                  if (canSearch === false) {
                    message.warning(t('search.chooseDataset'));
                    return;
                  }
                  setSearchText(e.target.value || '');
                }}
              />
              <button
                type="button"
                className="absolute right-2 top-1/2 -translate-y-1/2 transform rounded-full bg-text-primary p-2 text-bg-base shadow w-12"
                onClick={() => {
                  if (canSearch === false) {
                    message.warning(t('search.chooseDataset'));
                    return;
                  }
                  setIsSearching(!isSearching);
                }}
              >
                <Search size={22} className="m-auto" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
