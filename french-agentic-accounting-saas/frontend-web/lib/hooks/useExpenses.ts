import useSWR from 'swr';
import { expensesAPI } from '@/lib/api';

const STALE_TIME = 5 * 60 * 1000; // 5 min

function getExpensesKey(params?: { page?: number; page_size?: number; status?: string }) {
  return params ? ['expenses', params.page, params.page_size, params.status] : ['expenses', 1, 50];
}

async function fetcherExpenses(key: (string | number | undefined)[]) {
  const page = Number(key[1] ?? 1);
  const pageSize = Number(key[2] ?? 50);
  const status = key[3] as string | undefined;
  const res = await expensesAPI.list({ page, page_size: pageSize, status: status || undefined });
  const data = res?.data ?? res;
  const items = Array.isArray(data) ? data : (data?.items ?? []);
  return { items, total: res?.total ?? items.length };
}

export function useExpenses(params?: { page?: number; page_size?: number; status?: string }) {
  const key = getExpensesKey(params ?? { page: 1, page_size: 50 });
  const { data, error, mutate, isLoading, isValidating } = useSWR(key, fetcherExpenses, {
    revalidateOnFocus: false,
    dedupingInterval: 2000,
    keepPreviousData: true,
  });
  return {
    expenses: data?.items ?? [],
    total: data?.total ?? 0,
    isLoading,
    isValidating,
    error,
    mutate,
  };
}
