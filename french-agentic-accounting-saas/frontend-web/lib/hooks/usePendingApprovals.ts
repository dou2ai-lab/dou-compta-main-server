import useSWR from 'swr';
import { expensesAPI } from '@/lib/api';

async function fetcherPending(key: (string | number)[]) {
  const page = Number(key[1] ?? 1);
  const pageSize = Number(key[2] ?? 20);
  const res = await expensesAPI.pendingApprovals({ page, page_size: pageSize });
  const root = res ?? {};
  const data = Array.isArray(root.data) ? root.data : Array.isArray(root) ? root : [];
  const total = typeof root.total === 'number' ? root.total : data.length || 0;
  return { data, total };
}

export function usePendingApprovals(params?: { page?: number; page_size?: number }) {
  const page = params?.page ?? 1;
  const pageSize = params?.page_size ?? 20;
  const key = ['pending-approvals', page, pageSize];
  const { data, error, mutate, isLoading } = useSWR(key, fetcherPending, {
    revalidateOnFocus: true,
    dedupingInterval: 3000,
  });
  return {
    pending: data?.data ?? [],
    total: data?.total ?? 0,
    isLoading,
    error,
    mutate,
  };
}
