# Frontend Performance Optimizations

This document summarizes the performance optimizations applied to the Next.js frontend **without** rewriting the app or breaking existing features.

## 1. API & Data Fetching

### Before
- Multiple `useEffect` hooks per page (dashboard: 3 separate effects for expenses, user, pending).
- No caching: every navigation refetched all data.
- Sequential or duplicated requests (e.g. expenses fetched on dashboard and again on expenses list).

### After
- **SWR** for all main data: `useExpenses`, `useUser`, `usePendingApprovals`.
- **Single source of truth**: same cache key for expenses on dashboard and expenses page when params match.
- **Deduping**: `dedupingInterval: 2000` (expenses), so rapid navigations don’t refetch.
- **Background revalidation**: data stays fresh without blocking the UI.
- **No blocking awaits**: SWR returns cached data first, then revalidates.

**Files**
- `lib/hooks/useExpenses.ts` – expenses list with pagination, cached.
- `lib/hooks/useUser.ts` – current user, cached 10 min.
- `lib/hooks/usePendingApprovals.ts` – pending approvals, cached 3 s dedupe.

## 2. Routing & Rendering

### Before
- Chart (Plotly) loaded eagerly on dashboard, increasing initial JS.
- Heavy chart logic ran in `useEffect` on every `expenses` change.

### After
- **Dynamic import for Chart**: `dynamic(() => import('@/components/ui/Chart'), { ssr: false })` so Plotly loads only when the chart is visible (code-split).
- **useMemo for chart data and layout**: `chartData` and `chartLayout` derived from `expenses` in `useMemo`, so expensive work runs only when `expenses` changes.
- **useMemo for dashboard stats**: `pendingAmount`, `awaitingCount`, `thisMonthSpend`, `vatRecoverable`, `recentExpenses` computed in one `useMemo` to avoid recalculating on every render.

## 3. Bundle Size

### Before
- Full Font Awesome CSS + JS from CDN (blocking).
- Duplicate icon set (CDN + `@fortawesome/react-fontawesome`).
- `plotly.js` and `react-plotly.js` in dependencies while only `plotly.js-dist-min` is used.

### After
- **Removed** Font Awesome CDN (CSS + Script) from `app/layout.tsx`; icons come only from `@fortawesome/react-fontawesome` (tree-shaken).
- **Removed** `plotly.js` and `react-plotly.js` from `package.json`; only `plotly.js-dist-min` is used (Chart already uses dynamic import).
- **next.config.js**: `compress: true`, `compiler.removeConsole` in production. (On Next 14.1+, you can add `experimental.optimizePackageImports: ['@fortawesome/free-solid-svg-icons']` for better icon tree-shaking.)

## 4. Rendering Performance

### Before
- Dashboard: chart and stats recalculated on every render.
- Expenses page: `displayExpenses` recreated every render.

### After
- **useMemo** for all derived data (stats, chart series, `displayExpenses`).
- **Reusable skeletons**: `TableRowSkeleton` and `Skeleton` in `components/ui/Skeleton.tsx` used on dashboard and expenses list to avoid layout shift and show structure while loading.

## 5. Next.js & Build

- **compress: true** (default, explicit for clarity).
- **poweredByHeader: false** (minor).
- **compiler.removeConsole**: in production, strip `console.log` (keep `error` and `warn`) to reduce bundle and noise.

## 6. Bottlenecks Addressed

| Bottleneck | Change |
|------------|--------|
| Blocking API on every visit | SWR cache + dedupe; show cache first, revalidate in background |
| Heavy Plotly on initial load | Dynamic import with `ssr: false` for Chart |
| Re-runs of chart/stats logic | useMemo for chart data, layout, and dashboard stats |
| Duplicate FA + CDN | Single FA source (React), no CDN |
| Unused Plotly packages | Removed `plotly.js` and `react-plotly.js` |
| No loading structure | Skeleton components for tables and cards |

## 7. What Was Not Changed

- No UI/design changes.
- No API contract changes.
- No removal of features.
- No tech stack change (still Next.js 14, React, Tailwind).
- Approvals, reports, and other pages keep current behavior; they can be migrated to SWR and the same patterns later.

## 8. How to Measure

- **Bundle**: `npm run build` and check `.next` output or use `@next/bundle-analyzer` if added.
- **Lighthouse**: Run against production build (`npm run build && npm run start`) for LCP, FCP, TBT.
- **Perceived speed**: Navigate dashboard → expenses → dashboard; second visit to dashboard should feel instant (cache).

## 9. Optional Next Steps

- Add **react-window** (or similar) for expense tables with 50+ rows for virtualization.
- Extend SWR to **approvals** and **reports** for consistent caching.
- **Prefetch** `/expenses` and `/approvals` on dashboard hover (e.g. `router.prefetch`).
- **Debounce** search/filter inputs when wired to API.
