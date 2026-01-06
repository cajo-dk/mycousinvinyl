import { PreferencesResponse } from '@/types/api';

export type ItemsPerPageView = 'collection' | 'artists' | 'albums' | 'pressings';

export const DEFAULT_ITEMS_PER_PAGE = 10;

export const resolveItemsPerPage = (
  preferences: PreferencesResponse | null | undefined,
  view: ItemsPerPageView,
  fallback: number = DEFAULT_ITEMS_PER_PAGE
) => {
  const display = preferences?.display_settings;
  const byView = display?.items_per_page_by_view as Record<string, unknown> | undefined;
  const viewValue = typeof byView?.[view] === 'number' ? (byView[view] as number) : undefined;
  const globalValue = typeof display?.items_per_page === 'number' ? display.items_per_page : undefined;
  return viewValue ?? globalValue ?? fallback;
};
