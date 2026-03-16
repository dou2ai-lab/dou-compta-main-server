import useSWR from 'swr';
import { authAPI } from '@/lib/api';

const STALE_TIME = 10 * 60 * 1000; // 10 min

async function fetcherUser() {
  const me = await authAPI.me();
  return me;
}

export function useUser(enabled = true) {
  const { data, error, mutate, isLoading } = useSWR(enabled ? 'user' : null, fetcherUser, {
    revalidateOnFocus: false,
    dedupingInterval: STALE_TIME,
    revalidateIfStale: true,
  });
  const userName = data
    ? [data.first_name, data.last_name].filter(Boolean).join(' ') || (data.email ?? '')
    : '';
  return { user: data, userName, error, mutate, isLoading };
}
