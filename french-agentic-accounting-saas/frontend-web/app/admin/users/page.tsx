'use client'

import { useEffect, useState, useCallback, useRef, Fragment } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faUsers,
  faCheckCircle,
  faShieldAlt,
  faClock,
  faDownload,
  faUpload,
  faPlus,
  faFilter,
  faTimes,
  faEye,
  faEdit,
  faBan,
  faCheck,
  faCrown,
  faUserTie,
  faCalculator,
  faClipboardCheck,
  faUser,
  faBuilding,
  faCircleDot,
  faReceipt,
  faCheckSquare,
  faCog,
  faInfoCircle,
  faTimes as faClose,
  faChevronLeft,
  faChevronRight,
  faChevronDown,
} from '@fortawesome/free-solid-svg-icons'
import { adminAPI, type AdminRole, type AdminPermission, type AdminActivityItem } from '@/lib/api'

type TabId = 'users' | 'roles' | 'activity'

type UserRow = {
  id: string
  email: string
  first_name: string | null
  last_name: string | null
  status: string
  role?: string
  roles?: { id: string; name: string }[]
  department?: string
  last_active?: string
}

const DEPARTMENT_OPTIONS = ['All Departments', 'Sales', 'Engineering', 'Marketing', 'Finance', 'Operations', 'HR']
const STATUS_OPTIONS = ['All Status', 'Active', 'Inactive', 'Suspended']

const AVATAR_BASE = 'https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-'

function getAvatarUrl(index: number) {
  const n = (index % 9) + 1
  return `${AVATAR_BASE}${n}.jpg`
}

function roleBadgeClass(role: string) {
  const r = (role || '').toLowerCase()
  if (r === 'admin') return 'text-purple-600 bg-purple-50'
  if (r === 'approver' || r === 'manager') return 'text-blue-600 bg-blue-50'
  if (r === 'finance') return 'text-green-600 bg-green-50'
  if (r === 'employee') return 'text-gray-600 bg-gray-100'
  return 'text-orange-600 bg-orange-50'
}

function roleIcon(role: string) {
  const r = (role || '').toLowerCase()
  if (r === 'admin') return faCrown
  if (r === 'approver' || r === 'manager') return faUserTie
  if (r === 'finance') return faCalculator
  if (r === 'employee') return faUser
  return faClipboardCheck
}

function roleDisplayName(name: string) {
  return name ? name.charAt(0).toUpperCase() + name.slice(1) : name
}

/** Turn API error (FastAPI detail array/object or string) into a string safe to render. */
function apiErrorMessage(err: any, fallback: string): string {
  const detail = err?.response?.data?.detail
  if (detail == null) return err?.message || fallback
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const msg = detail.map((d: any) => (d?.msg != null ? String(d.msg) : JSON.stringify(d))).join('; ')
    return msg || fallback
  }
  if (typeof detail === 'object' && detail?.msg != null) return String(detail.msg)
  return fallback
}

export default function UsersAndRolesPage() {
  const [activeTab, setActiveTab] = useState<TabId>('users')
  const [users, setUsers] = useState<UserRow[]>([])
  const [roles, setRoles] = useState<AdminRole[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(8)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [roleFilter, setRoleFilter] = useState<string>('')
  const [departmentFilter, setDepartmentFilter] = useState('All Departments')
  const [statusFilter, setStatusFilter] = useState('All Status')
  const [modalMode, setModalMode] = useState<'add' | 'edit' | 'view' | null>(null)
  const [modalUser, setModalUser] = useState<UserRow | null>(null)
  const [formFirst, setFormFirst] = useState('')
  const [formLast, setFormLast] = useState('')
  const [formEmail, setFormEmail] = useState('')
  const [formPassword, setFormPassword] = useState('')
  const [formStatus, setFormStatus] = useState('active')
  const [formRoleIds, setFormRoleIds] = useState<string[]>([])
  const [saving, setSaving] = useState(false)
  const [bulkActionLoading, setBulkActionLoading] = useState(false)
  const [showBulkRoleModal, setShowBulkRoleModal] = useState(false)
  const [bulkRoleId, setBulkRoleId] = useState('')
  const [permissions, setPermissions] = useState<AdminPermission[]>([])
  const [permissionsLoading, setPermissionsLoading] = useState(false)
  const [permissionsSaving, setPermissionsSaving] = useState(false)
  const [permissionsSaveSuccess, setPermissionsSaveSuccess] = useState(false)
  const [rolePermissionMatrix, setRolePermissionMatrix] = useState<Record<string, Set<string>>>({})
  const [activities, setActivities] = useState<AdminActivityItem[]>([])
  const [exporting, setExporting] = useState(false)
  const [importing, setImporting] = useState(false)
  const [importSuccess, setImportSuccess] = useState<string | null>(null)
  const importInputRef = useRef<HTMLInputElement>(null)
  const [activityPage, setActivityPage] = useState(1)
  const [activityTotal, setActivityTotal] = useState(0)
  const [activityPageSize] = useState(10)
  const [activityLoading, setActivityLoading] = useState(false)
  const [activityError, setActivityError] = useState<string | null>(null)

  const loadRoles = useCallback(async () => {
    try {
      const data = await adminAPI.roles()
      setRoles(data?.roles ?? [])
    } catch {
      setRoles([])
    }
  }, [])

  const mapUserWithRoles = useCallback((u: any, rolesList: any[]) => {
    const firstRoleName =
      rolesList.length > 0
        ? typeof rolesList[0] === 'string'
          ? rolesList[0]
          : rolesList[0]?.name
        : u?.role ?? ''
    return {
      id: u.id,
      email: u.email ?? '',
      first_name: u.first_name ?? null,
      last_name: u.last_name ?? null,
      status: u.status ?? 'active',
      role: firstRoleName || '',
      roles: rolesList.map((r: any) => (typeof r === 'string' ? { id: '', name: r } : { id: r?.id ?? '', name: r?.name ?? '' })),
      department: u.department ?? '—',
      last_active: u.last_active ?? '—',
    }
  }, [])

  const loadUsers = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const statusParam =
        statusFilter === 'Active' ? 'active' : statusFilter === 'Inactive' ? 'inactive' : statusFilter === 'Suspended' ? 'suspended' : undefined
      const res = await adminAPI.users({
        page,
        page_size: pageSize,
        role_id: roleFilter || undefined,
        status: statusParam,
      })
      const data = res?.data ?? res
      let list = Array.isArray(data?.users) ? data.users : []

      // If backend did not include roles (e.g. old admin container), fetch per user
      const needsRoleFetch = list.length > 0 && list.every((u: any) => !Array.isArray(u?.roles) || u.roles.length === 0)
      if (needsRoleFetch) {
        const withRoles = await Promise.all(
          list.map(async (u: any) => {
            try {
              const full = await adminAPI.getUser(u.id)
              const r = Array.isArray(full?.roles) ? full.roles : []
              return mapUserWithRoles(u, r)
            } catch {
              return mapUserWithRoles(u, [])
            }
          })
        )
        list = withRoles
      } else {
        list = list.map((u: any) => {
          const rolesList = Array.isArray(u?.roles) ? u.roles : []
          return mapUserWithRoles(u, rolesList)
        })
      }

      setUsers(list)
      setTotal(typeof data?.total === 'number' ? data.total : list.length)
    } catch (err: any) {
      setError(apiErrorMessage(err, 'Failed to load users'))
      setUsers([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, roleFilter, statusFilter, mapUserWithRoles])

  useEffect(() => {
    if (activeTab === 'users' || activeTab === 'roles') {
      void loadRoles()
    }
  }, [activeTab, loadRoles])

  const loadPermissionsForMatrix = useCallback(async () => {
    setPermissionsLoading(true)
    setError(null)
    try {
      const data = await adminAPI.permissions()
      setPermissions(data?.permissions ?? [])
      const roleData = await adminAPI.roles()
      const roleList = roleData?.roles ?? []
      setRoles(roleList)
      const matrix: Record<string, Set<string>> = {}
      for (const r of roleList) {
        matrix[r.id] = new Set((r.permission_ids ?? []) as string[])
      }
      setRolePermissionMatrix(matrix)
    } catch (err: any) {
      setError(apiErrorMessage(err, 'Failed to load permissions'))
    } finally {
      setPermissionsLoading(false)
    }
  }, [])

  const loadActivity = useCallback(async () => {
    setActivityLoading(true)
    setActivityError(null)
    try {
      const res = await adminAPI.activity({ page: activityPage, page_size: activityPageSize })
      setActivities(res.activities ?? [])
      setActivityTotal(res.total ?? 0)
    } catch {
      setActivities([])
      setActivityTotal(0)
      setActivityError('Could not load activity. If you added users or changed roles but nothing appears here, the activity log table may be missing. Run database setup (create_tables or full bootstrap) — see docs/SETUP_FOR_TEAMMATES.md.')
    } finally {
      setActivityLoading(false)
    }
  }, [activityPage, activityPageSize])

  useEffect(() => {
    if (activeTab === 'roles') {
      void loadPermissionsForMatrix()
    }
  }, [activeTab, loadPermissionsForMatrix])

  useEffect(() => {
    if (activeTab === 'activity') {
      void loadActivity()
    }
  }, [activeTab, loadActivity])

  useEffect(() => {
    if (activeTab === 'users') {
      void loadUsers()
    }
  }, [activeTab, page, roleFilter, statusFilter, loadUsers])

  const handleClearFilters = () => {
    setRoleFilter('')
    setStatusFilter('All Status')
    setDepartmentFilter('All Departments')
    setPage(1)
  }

  const activeCount = users.filter((u) => u.status === 'active').length
  const inactiveCount = users.filter((u) => u.status !== 'active').length
  const hasRole = (u: UserRow, roleName: string) => {
    const r = (u.role || '').toLowerCase()
    if (r === roleName.toLowerCase()) return true
    const list = u.roles ?? []
    return list.some((x) => (x?.name || '').toLowerCase() === roleName.toLowerCase())
  }
  const adminCount = users.filter((u) => hasRole(u, 'admin')).length

  // Role card count: prefer API user_count when > 0; otherwise use counts from visible users so cards match the table
  const roleCount = (name: string) => {
    const r = roles.find((x) => (x.name || '').toLowerCase() === name.toLowerCase())
    const fromApi = r != null && typeof r.user_count === 'number' ? r.user_count : null
    const fromPage = users.filter((u) => hasRole(u, name)).length
    if (fromApi != null && fromApi > 0) return fromApi
    return fromPage
  }

  const openAddModal = () => {
    setModalMode('add')
    setModalUser(null)
    setFormFirst('')
    setFormLast('')
    setFormEmail('')
    setFormPassword('password')
    setFormStatus('active')
    setFormRoleIds([])
  }

  const openViewModal = (user: UserRow) => {
    setModalMode('view')
    setModalUser(user)
    setFormFirst(user.first_name ?? '')
    setFormLast(user.last_name ?? '')
    setFormEmail(user.email ?? '')
    setFormStatus(user.status ?? 'active')
    setFormRoleIds((user.roles ?? []).map((r) => r.id).filter(Boolean))
  }

  const openEditModal = (user: UserRow) => {
    setModalMode('edit')
    setModalUser(user)
    setFormFirst(user.first_name ?? '')
    setFormLast(user.last_name ?? '')
    setFormEmail(user.email ?? '')
    setFormStatus(user.status ?? 'active')
    setFormRoleIds((user.roles ?? []).map((r) => r.id).filter(Boolean))
  }

  const closeModal = () => {
    setModalMode(null)
    setModalUser(null)
  }

  const handleSaveUser = async () => {
    if (modalMode === 'add') {
      setSaving(true)
      try {
        await adminAPI.createUser({
          email: formEmail,
          first_name: formFirst,
          last_name: formLast,
          password: formPassword || 'password',
          status: formStatus,
          role_ids: formRoleIds.length ? formRoleIds : undefined,
        })
        closeModal()
        await loadUsers()
      } catch (err: any) {
        setError(apiErrorMessage(err, 'Failed to create user'))
      } finally {
        setSaving(false)
      }
    } else if (modalMode === 'edit' && modalUser) {
      setSaving(true)
      try {
        await adminAPI.updateUser(modalUser.id, {
          first_name: formFirst,
          last_name: formLast,
          status: formStatus,
          role_ids: formRoleIds,
        })
        closeModal()
        await loadUsers()
      } catch (err: any) {
        setError(apiErrorMessage(err, 'Failed to update user'))
      } finally {
        setSaving(false)
      }
    }
  }

  const handleExportUsers = async () => {
    setExporting(true)
    setError(null)
    try {
      const pageSizeExport = 100
      let list: UserRow[] = []
      let page = 1
      let hasMore = true
      while (hasMore) {
        const res = await adminAPI.users({ page, page_size: pageSizeExport })
        const data = res?.data
        const chunk = (Array.isArray(data?.users) ? data.users : []) as UserRow[]
        list = list.concat(chunk)
        const total = data?.total ?? 0
        hasMore = list.length < total
        page += 1
      }
      const headers = ['Email', 'First Name', 'Last Name', 'Status', 'Roles']
      const escape = (v: string) => {
        const s = String(v ?? '')
        if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`
        return s
      }
      const rows = list.map((u) =>
        [u.email, u.first_name ?? '', u.last_name ?? '', u.status, (u.roles ?? []).map((r) => r.name).join('; ')].map(escape).join(',')
      )
      const csv = [headers.join(','), ...rows].join('\r\n')
      const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `users-export-${new Date().toISOString().slice(0, 10)}.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err: any) {
      setError(apiErrorMessage(err, 'Export failed'))
    } finally {
      setExporting(false)
    }
  }

  const handleImportUsers = () => {
    importInputRef.current?.click()
  }

  const onImportFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    setImporting(true)
    setError(null)
    let created = 0
    let failed = 0
    const defaultPassword = 'password'
    try {
      const text = await file.text()
      const lines = text.split(/\r?\n/).filter((line) => line.trim())
      const header = lines[0]?.toLowerCase() ?? ''
      const hasHeader = /email|first_name|last_name/.test(header)
      const start = hasHeader ? 1 : 0
      for (let i = start; i < lines.length; i++) {
        const line = lines[i]
        const parsed = parseCsvLine(line)
        const email = (parsed[0] ?? '').trim()
        if (!email) continue
        const first_name = (parsed[1] ?? '').trim()
        const last_name = (parsed[2] ?? '').trim()
        const password = (parsed[3] ?? defaultPassword).trim() || defaultPassword
        try {
          await adminAPI.createUser({
            email,
            first_name: first_name || '',
            last_name: last_name || '',
            password,
            status: 'active',
          })
          created++
        } catch {
          failed++
        }
      }
      if (created > 0) await loadUsers()
      if (failed > 0) {
        setError(`Imported ${created} user(s), ${failed} failed (e.g. duplicate email).`)
        setImportSuccess(null)
      } else if (created > 0) {
        setError(null)
        setImportSuccess(`Imported ${created} user(s).`)
        setTimeout(() => setImportSuccess(null), 5000)
      } else {
        setError(null)
        setImportSuccess(null)
      }
    } catch (err: any) {
      setError(err?.message || 'Import failed. Use CSV with columns: email, first_name, last_name, password (optional).')
    } finally {
      setImporting(false)
    }
  }

  function parseCsvLine(line: string): string[] {
    const out: string[] = []
    let cur = ''
    let inQuotes = false
    for (let i = 0; i < line.length; i++) {
      const c = line[i]
      if (c === '"') {
        if (inQuotes && line[i + 1] === '"') {
          cur += '"'
          i++
        } else {
          inQuotes = !inQuotes
        }
      } else if ((c === ',' && !inQuotes) || c === '\r') {
        out.push(cur.trim())
        cur = ''
      } else if (c !== '\r') {
        cur += c
      }
    }
    out.push(cur.trim())
    return out
  }

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleSelectAll = () => {
    if (selectedIds.size === users.length) setSelectedIds(new Set())
    else setSelectedIds(new Set(users.map((u) => u.id)))
  }

  const toggleFormRole = (roleId: string) => {
    setFormRoleIds((prev) =>
      prev.includes(roleId) ? prev.filter((id) => id !== roleId) : [...prev, roleId]
    )
  }

  const handleToggleStatus = async (user: UserRow) => {
    const newStatus = user.status === 'active' ? 'inactive' : 'active'
    if (newStatus === 'inactive' && !window.confirm(`Deactivate ${user.email}? They will not be able to log in.`)) return
    try {
      setError(null)
      await adminAPI.updateUser(user.id, { status: newStatus })
      await loadUsers()
    } catch (err: any) {
      setError(apiErrorMessage(err, 'Failed to update status'))
    }
  }

  const selectedUserList = users.filter((u) => selectedIds.has(u.id))

  const handleBulkActivate = async () => {
    const toActivate = selectedUserList.filter((u) => u.status !== 'active')
    if (toActivate.length === 0) return
    setBulkActionLoading(true)
    setError(null)
    try {
      for (const u of toActivate) {
        await adminAPI.updateUser(u.id, { status: 'active' })
      }
      await loadUsers()
      setSelectedIds(new Set())
    } catch (err: any) {
      setError(apiErrorMessage(err, 'Failed to activate users'))
    } finally {
      setBulkActionLoading(false)
    }
  }

  const handleBulkDeactivate = async () => {
    if (!window.confirm(`Deactivate ${selectedIds.size} user(s)? They will not be able to log in.`)) return
    setBulkActionLoading(true)
    setError(null)
    try {
      for (const id of selectedIds) {
        await adminAPI.updateUser(id, { status: 'inactive' })
      }
      await loadUsers()
      setSelectedIds(new Set())
    } catch (err: any) {
      setError(apiErrorMessage(err, 'Failed to deactivate users'))
    } finally {
      setBulkActionLoading(false)
    }
  }

  const handleBulkChangeRoleOpen = () => {
    setBulkRoleId(roles[0]?.id ?? '')
    setShowBulkRoleModal(true)
  }

  const roleOrder = ['admin', 'approver', 'finance', 'employee']
  const rolesForMatrix = roleOrder
    .map((name) => roles.find((r) => (r.name || '').toLowerCase() === name))
    .filter(Boolean) as AdminRole[]

  const toggleRolePermission = (roleId: string, permissionId: string) => {
    setRolePermissionMatrix((prev) => {
      const next = { ...prev }
      const set = new Set(next[roleId] ?? [])
      if (set.has(permissionId)) set.delete(permissionId)
      else set.add(permissionId)
      next[roleId] = set
      return next
    })
  }

  const handleSaveRolePermissions = async () => {
    setPermissionsSaving(true)
    setError(null)
    setPermissionsSaveSuccess(false)
    try {
      for (const role of rolesForMatrix) {
        const current = Array.from(rolePermissionMatrix[role.id] ?? [])
        const initial = (role.permission_ids ?? []) as string[]
        const same = current.length === initial.length && current.every((id) => initial.includes(id))
        if (!same) {
          await adminAPI.updateRolePermissions(role.id, current)
        }
      }
      await loadPermissionsForMatrix()
      setPermissionsSaveSuccess(true)
      setTimeout(() => setPermissionsSaveSuccess(false), 4000)
    } catch (err: any) {
      setError(apiErrorMessage(err, 'Failed to save permissions'))
    } finally {
      setPermissionsSaving(false)
    }
  }

  const handleBulkChangeRoleApply = async () => {
    if (!bulkRoleId) return
    setBulkActionLoading(true)
    setError(null)
    try {
      for (const id of selectedIds) {
        await adminAPI.updateUser(id, { role_ids: [bulkRoleId] })
      }
      await loadUsers()
      setSelectedIds(new Set())
      setShowBulkRoleModal(false)
    } catch (err: any) {
      setError(apiErrorMessage(err, 'Failed to change role'))
    } finally {
      setBulkActionLoading(false)
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">
              Users & Roles Management
            </h1>
            <p className="text-textSecondary">
              Manage user accounts, roles, and permissions across the organization
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <input
              ref={importInputRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={onImportFileChange}
            />
            <button
              type="button"
              disabled={exporting}
              onClick={handleExportUsers}
              className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 hover:text-textPrimary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FontAwesomeIcon icon={faDownload} />
              <span>{exporting ? 'Exporting…' : 'Export Users'}</span>
            </button>
            <button
              type="button"
              disabled={importing}
              onClick={handleImportUsers}
              className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 hover:text-textPrimary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FontAwesomeIcon icon={faUpload} />
              <span>{importing ? 'Importing…' : 'Import Users'}</span>
            </button>
            <button type="button" onClick={openAddModal} className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2">
              <FontAwesomeIcon icon={faPlus} />
              <span>Add User</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-6 mb-6">
          <div className="bg-surface rounded-xl p-5 border border-borderColor shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faUsers} className="text-primary text-xl" />
              </div>
              <span className="text-xs font-medium text-successGreen bg-green-50 px-2 py-1 rounded-full">+{total > 0 ? Math.min(total, 8) : 0}</span>
            </div>
            <div className="text-2xl font-bold text-textPrimary mb-1">{total}</div>
            <div className="text-sm text-textSecondary">Total Users</div>
          </div>
          <div className="bg-surface rounded-xl p-5 border border-borderColor shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faCheckCircle} className="text-successGreen text-xl" />
              </div>
              <span className="text-xs font-medium text-successGreen bg-green-50 px-2 py-1 rounded-full">Active</span>
            </div>
            <div className="text-2xl font-bold text-textPrimary mb-1">{activeCount}</div>
            <div className="text-sm text-textSecondary">Active Users</div>
          </div>
          <div className="bg-surface rounded-xl p-5 border border-borderColor shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="w-12 h-12 bg-purple-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faShieldAlt} className="text-purple-600 text-xl" />
              </div>
              <span className="text-xs font-medium text-infoBlue bg-blue-50 px-2 py-1 rounded-full">{roles.length} Roles</span>
            </div>
            <div className="text-2xl font-bold text-textPrimary mb-1">{adminCount}</div>
            <div className="text-sm text-textSecondary">Administrators</div>
          </div>
          <div className="bg-surface rounded-xl p-5 border border-borderColor shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="w-12 h-12 bg-amber-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faClock} className="text-warningAmber text-xl" />
              </div>
              <span className="text-xs font-medium text-warningAmber bg-amber-50 px-2 py-1 rounded-full">Pending</span>
            </div>
            <div className="text-2xl font-bold text-textPrimary mb-1">{inactiveCount}</div>
            <div className="text-sm text-textSecondary">Inactive Users</div>
          </div>
        </div>
      </section>

      <section className="mb-8">
        <div className="bg-surface rounded-xl border border-borderColor shadow-sm">
          <div className="border-b border-borderColor px-6">
            <div className="flex items-center space-x-6">
              <button
                type="button"
                onClick={() => setActiveTab('users')}
                className={`py-4 px-2 border-b-2 text-sm font-medium ${activeTab === 'users' ? 'border-primary text-primary' : 'border-transparent text-textSecondary hover:text-textPrimary hover:border-gray-300'}`}
              >
                User List
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('roles')}
                className={`py-4 px-2 border-b-2 text-sm font-medium ${activeTab === 'roles' ? 'border-primary text-primary' : 'border-transparent text-textSecondary hover:text-textPrimary hover:border-gray-300'}`}
              >
                Roles & Permissions
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('activity')}
                className={`py-4 px-2 border-b-2 text-sm font-medium ${activeTab === 'activity' ? 'border-primary text-primary' : 'border-transparent text-textSecondary hover:text-textPrimary hover:border-gray-300'}`}
              >
                Activity Log
              </button>
            </div>
          </div>

          {activeTab === 'users' && (
            <div className="p-6">
              {error && (
                <div className="mb-4 p-3 bg-highRisk/30 border border-errorRed/50 rounded-lg text-sm text-errorRed">
                  {error}
                </div>
              )}
              {importSuccess && (
                <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800">
                  {importSuccess}
                </div>
              )}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <FontAwesomeIcon icon={faShieldAlt} className="absolute left-3 top-1/2 -translate-y-1/2 text-textMuted text-sm pointer-events-none" />
                    <select
                      value={roleFilter}
                      onChange={(e) => setRoleFilter(e.target.value)}
                      className="h-10 pl-10 pr-8 border border-borderColor rounded-lg text-sm appearance-none bg-white cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      <option value="">All Roles</option>
                      {roles.map((r) => (
                        <option key={r.id} value={r.id}>{roleDisplayName(r.name || '')}</option>
                      ))}
                    </select>
                    <FontAwesomeIcon icon={faChevronDown} className="absolute right-3 top-1/2 -translate-y-1/2 text-textMuted text-xs pointer-events-none" />
                  </div>
                  <div className="relative">
                    <FontAwesomeIcon icon={faBuilding} className="absolute left-3 top-1/2 -translate-y-1/2 text-textMuted text-sm pointer-events-none" />
                    <select
                      value={departmentFilter}
                      onChange={(e) => setDepartmentFilter(e.target.value)}
                      className="h-10 pl-10 pr-8 border border-borderColor rounded-lg text-sm appearance-none bg-white cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      {DEPARTMENT_OPTIONS.map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                    <FontAwesomeIcon icon={faChevronDown} className="absolute right-3 top-1/2 -translate-y-1/2 text-textMuted text-xs pointer-events-none" />
                  </div>
                  <div className="relative">
                    <FontAwesomeIcon icon={faCircleDot} className="absolute left-3 top-1/2 -translate-y-1/2 text-textMuted text-sm pointer-events-none" />
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="h-10 pl-10 pr-8 border border-borderColor rounded-lg text-sm appearance-none bg-white cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      {STATUS_OPTIONS.map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                    <FontAwesomeIcon icon={faChevronDown} className="absolute right-3 top-1/2 -translate-y-1/2 text-textMuted text-xs pointer-events-none" />
                  </div>
                  <div className="h-8 w-px bg-borderColor" />
                  <button type="button" className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
                    <FontAwesomeIcon icon={faFilter} />
                    <span>More Filters</span>
                  </button>
                  <button type="button" onClick={handleClearFilters} className="h-10 px-4 text-sm font-medium text-primary hover:text-primaryHover flex items-center space-x-2">
                    <FontAwesomeIcon icon={faTimes} />
                    <span>Clear All</span>
                  </button>
                </div>
                {selectedIds.size > 0 && (
                  <div className="flex items-center space-x-3">
                    <span className="text-sm text-textSecondary">{selectedIds.size} selected</span>
                    <button
                      type="button"
                      onClick={handleBulkActivate}
                      disabled={bulkActionLoading || selectedUserList.every((u) => u.status === 'active')}
                      className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <FontAwesomeIcon icon={faCheckCircle} />
                      <span>{bulkActionLoading ? 'Updating...' : 'Activate'}</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleBulkDeactivate}
                      disabled={bulkActionLoading}
                      className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <FontAwesomeIcon icon={faBan} />
                      <span>Deactivate</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleBulkChangeRoleOpen}
                      disabled={bulkActionLoading}
                      className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <FontAwesomeIcon icon={faUserTie} />
                      <span>Change Role</span>
                    </button>
                  </div>
                )}
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-borderColor">
                      <th className="text-left py-3 px-4 w-12">
                        <input
                          type="checkbox"
                          checked={users.length > 0 && selectedIds.size === users.length}
                          onChange={toggleSelectAll}
                          className="w-4 h-4 text-primary border-borderColor rounded focus:ring-primary"
                        />
                      </th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">User</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">Email</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">Role</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">Department</th>
                      <th className="text-center py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">Status</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">Last Active</th>
                      <th className="text-right py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr>
                        <td colSpan={8} className="py-10 text-center text-textSecondary">
                          Loading...
                        </td>
                      </tr>
                    ) : users.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="py-10 text-center text-textSecondary">
                          No users found.
                        </td>
                      </tr>
                    ) : (
                      users.map((user, idx) => (
                        <tr key={user.id} className="border-b border-borderColor hover:bg-gray-50 h-16">
                          <td className="py-3 px-4">
                            <input
                              type="checkbox"
                              checked={selectedIds.has(user.id)}
                              onChange={() => toggleSelect(user.id)}
                              className="w-4 h-4 text-primary border-borderColor rounded focus:ring-primary"
                            />
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex items-center space-x-3">
                              <img src={getAvatarUrl(idx)} alt="" className="w-10 h-10 rounded-full" />
                              <div>
                                <div className="text-sm font-medium text-textPrimary">
                                  {[user.first_name, user.last_name].filter(Boolean).join(' ') || user.email || '—'}
                                </div>
                                <div className="text-xs text-textSecondary">ID: {user.id.slice(0, 8).toUpperCase()}</div>
                              </div>
                            </div>
                          </td>
                          <td className="py-3 px-4 text-sm text-textSecondary">{user.email}</td>
                          <td className="py-3 px-4">
                            {(user.roles?.length ? user.roles : user.role ? [{ name: user.role }] : []).length > 0 ? (
                              <div className="flex flex-wrap gap-1">
                                {(user.roles?.length ? user.roles : [{ name: user.role }]).map((r: { id?: string; name?: string }, i: number) => {
                                  const roleName = r?.name || ''
                                  return (
                                    <span
                                      key={r?.id || i}
                                      className={`inline-flex items-center text-xs font-medium px-2 py-1 rounded-full ${roleBadgeClass(roleName)}`}
                                    >
                                      <FontAwesomeIcon icon={roleIcon(roleName)} className="mr-1" />
                                      {roleDisplayName(roleName)}
                                    </span>
                                  )
                                })}
                              </div>
                            ) : (
                              <span className="text-textMuted text-sm">—</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-sm text-textSecondary">{user.department ?? '—'}</td>
                          <td className="py-3 px-4 text-center">
                            <span className={`inline-flex items-center text-xs font-medium px-2 py-1 rounded-full ${user.status === 'active' ? 'text-successGreen bg-green-50' : 'text-textMuted bg-gray-100'}`}>
                              <span className={`w-1.5 h-1.5 rounded-full mr-1 ${user.status === 'active' ? 'bg-successGreen' : 'bg-textMuted'}`} />
                              {user.status === 'active' ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-sm text-textSecondary">{user.last_active ?? '—'}</td>
                          <td className="py-3 px-4">
                            <div className="flex items-center justify-end space-x-2">
                              <button type="button" onClick={() => openViewModal(user)} className="w-8 h-8 flex items-center justify-center text-textMuted hover:text-primary hover:bg-indigo-50 rounded-lg" title="View Details">
                                <FontAwesomeIcon icon={faEye} className="text-sm" />
                              </button>
                              <button type="button" onClick={() => openEditModal(user)} className="w-8 h-8 flex items-center justify-center text-textMuted hover:text-infoBlue hover:bg-blue-50 rounded-lg" title="Edit User">
                                <FontAwesomeIcon icon={faEdit} className="text-sm" />
                              </button>
                              <button
                                type="button"
                                onClick={() => handleToggleStatus(user)}
                                className={`w-8 h-8 flex items-center justify-center rounded-lg ${user.status === 'active' ? 'text-textMuted hover:text-errorRed hover:bg-red-50' : 'text-textMuted hover:text-successGreen hover:bg-green-50'}`}
                                title={user.status === 'active' ? 'Deactivate' : 'Activate'}
                              >
                                <FontAwesomeIcon icon={user.status === 'active' ? faBan : faCheck} className="text-sm" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-between mt-6 pt-4 border-t border-borderColor">
                <div className="text-sm text-textSecondary">
                  Showing {users.length} of {total} users
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="w-8 h-8 flex items-center justify-center border border-borderColor rounded-lg text-textMuted hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <FontAwesomeIcon icon={faChevronLeft} className="text-xs" />
                  </button>
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    const p = i + 1
                    return (
                      <button
                        key={p}
                        type="button"
                        onClick={() => setPage(p)}
                        className={`w-8 h-8 flex items-center justify-center rounded-lg ${page === p ? 'bg-primary text-white' : 'border border-borderColor text-textSecondary hover:bg-gray-50'}`}
                      >
                        {p}
                      </button>
                    )
                  })}
                  <button
                    type="button"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    className="w-8 h-8 flex items-center justify-center border border-borderColor rounded-lg text-textMuted hover:bg-gray-50 disabled:opacity-50"
                  >
                    <FontAwesomeIcon icon={faChevronRight} className="text-xs" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'roles' && (
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-textPrimary mb-1">Role Permissions Matrix</h2>
                  <p className="text-sm text-textSecondary">Manage role-based access control across all modules</p>
                </div>
                <button
                  type="button"
                  onClick={handleSaveRolePermissions}
                  disabled={permissionsLoading || permissionsSaving}
                  className="h-10 px-4 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <FontAwesomeIcon icon={faCheck} />
                  <span>{permissionsSaving ? 'Saving...' : 'Save Changes'}</span>
                </button>
              </div>
              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
              )}
              {permissionsSaveSuccess && (
                <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 text-green-800 text-sm font-medium">
                    <FontAwesomeIcon icon={faCheckCircle} className="text-green-600 text-lg" />
                    <span>Permissions saved successfully. Changes apply to all users with the updated roles.</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setPermissionsSaveSuccess(false)}
                    className="shrink-0 p-1 text-green-600 hover:text-green-800 hover:bg-green-100 rounded"
                    aria-label="Dismiss"
                  >
                    <FontAwesomeIcon icon={faClose} className="text-sm" />
                  </button>
                </div>
              )}
              {permissionsLoading ? (
                <div className="py-12 text-center text-textSecondary">Loading permissions...</div>
              ) : permissions.length === 0 && rolesForMatrix.length === 0 ? (
                <div className="py-12 text-center text-textSecondary">No permissions or roles found.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="border-b-2 border-borderColor">
                        <th className="text-left py-4 px-4 text-sm font-semibold text-textPrimary bg-gray-50 sticky left-0 z-10 min-w-[200px]">Module / Permission</th>
                        {rolesForMatrix.map((r) => (
                          <th key={r.id} className="text-center py-4 px-4 text-sm font-semibold text-textPrimary min-w-[120px] bg-gray-50">
                            <div className="flex flex-col items-center">
                              <FontAwesomeIcon icon={roleIcon(r.name)} className="mb-1 text-current" />
                              <span>{roleDisplayName(r.name)}</span>
                            </div>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {['expense', 'admin', 'audit', 'user'].map((resource) => {
                        const permsInResource = permissions.filter((p) => p.resource === resource)
                        if (permsInResource.length === 0) return null
                        const resourceLabel =
                          resource === 'expense' ? 'Expenses' : resource === 'admin' ? 'Administration' : resource === 'audit' ? 'Audit' : 'Users'
                        const resourceIcon = resource === 'expense' ? faReceipt : resource === 'admin' ? faCog : resource === 'audit' ? faCheckSquare : faUsers
                        return (
                          <Fragment key={resource}>
                            <tr className="border-b border-borderColor bg-gray-50">
                              <td colSpan={(rolesForMatrix.length || 1) + 1} className="py-3 px-4 text-sm font-semibold text-textPrimary">
                                <FontAwesomeIcon icon={resourceIcon} className="mr-2 text-primary" />
                                {resourceLabel} Module
                              </td>
                            </tr>
                            {permsInResource.map((perm) => (
                              <tr key={perm.id} className="border-b border-borderColor hover:bg-gray-50">
                                <td className="py-3 px-4 text-sm text-textSecondary bg-white sticky left-0 z-10">
                                  {perm.description || perm.name}
                                </td>
                                {rolesForMatrix.map((role) => (
                                  <td key={role.id} className="py-3 px-4 text-center">
                                    <input
                                      type="checkbox"
                                      checked={(rolePermissionMatrix[role.id] ?? new Set()).has(perm.id)}
                                      onChange={() => toggleRolePermission(role.id, perm.id)}
                                      className="w-5 h-5 text-primary border-borderColor rounded focus:ring-primary"
                                    />
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </Fragment>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
              <div className="mt-6 p-4 bg-indigo-50 border border-indigo-100 rounded-lg">
                <div className="flex items-start space-x-3">
                  <FontAwesomeIcon icon={faInfoCircle} className="text-primary text-lg mt-0.5" />
                  <div>
                    <div className="text-sm font-medium text-textPrimary mb-1">Permission Management Tips</div>
                    <ul className="text-xs text-textSecondary space-y-1">
                      <li>• Changes take effect when you click Save Changes</li>
                      <li>• Admin role typically has full access; adjust other roles as needed</li>
                      <li>• Review permissions regularly to maintain security compliance</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'activity' && (
            <div className="p-6">
              {activityError && (
                <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                  {activityError}
                </div>
              )}
              {activityLoading ? (
                <div className="flex items-center justify-center py-12 text-textSecondary">
                  <FontAwesomeIcon icon={faClock} className="animate-spin mr-2" />
                  Loading activity…
                </div>
              ) : activities.length === 0 ? (
                <div className="py-6">
                  <p className="text-textSecondary">No activity recorded yet. User and role changes will appear here.</p>
                  <p className="text-textSecondary text-sm mt-2">If you added users or changed roles but nothing appears, the activity table may be missing — run database setup (see docs/SETUP_FOR_TEAMMATES.md in the repo).</p>
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-borderColor text-left text-textMuted font-medium">
                          <th className="py-3 pr-4">Time</th>
                          <th className="py-3 pr-4">Action</th>
                          <th className="py-3 pr-4">By</th>
                          <th className="py-3 pr-4">Target</th>
                          <th className="py-3">Details</th>
                        </tr>
                      </thead>
                      <tbody>
                        {activities.map((a) => {
                          const by = a.performed_by_name || a.performed_by_email || '—'
                          const target =
                            a.target_user_id
                              ? (a.target_user_name || a.target_user_email || 'User')
                              : a.target_role_name
                                ? `Role: ${a.target_role_name}`
                                : '—'
                          const timeStr = a.created_at
                            ? new Date(a.created_at).toLocaleString(undefined, {
                                dateStyle: 'short',
                                timeStyle: 'short',
                              })
                            : '—'
                          const detailsStr =
                            typeof a.details === 'object' && a.details !== null
                              ? Object.entries(a.details)
                                  .filter(([, v]) => v != null && v !== '')
                                  .map(([k, v]) => `${k}: ${String(v)}`)
                                  .join(', ') || '—'
                              : '—'
                          return (
                            <tr key={a.id} className="border-b border-borderColor last:border-0">
                              <td className="py-3 pr-4 text-textSecondary whitespace-nowrap">{timeStr}</td>
                              <td className="py-3 pr-4 font-medium">{a.action_label}</td>
                              <td className="py-3 pr-4 text-textSecondary">{by}</td>
                              <td className="py-3 pr-4">{target}</td>
                              <td className="py-3 text-textSecondary">{detailsStr}</td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                  {activityTotal > activityPageSize && (
                    <div className="flex items-center justify-between mt-4 pt-4 border-t border-borderColor">
                      <span className="text-sm text-textSecondary">
                        Showing {(activityPage - 1) * activityPageSize + 1}–{Math.min(activityPage * activityPageSize, activityTotal)} of {activityTotal}
                      </span>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => setActivityPage((p) => Math.max(1, p - 1))}
                          disabled={activityPage <= 1 || activityLoading}
                          className="h-9 px-3 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                        >
                          <FontAwesomeIcon icon={faChevronLeft} />
                        </button>
                        <span className="text-sm text-textSecondary">
                          Page {activityPage} of {Math.ceil(activityTotal / activityPageSize) || 1}
                        </span>
                        <button
                          type="button"
                          onClick={() => setActivityPage((p) => p + 1)}
                          disabled={activityPage >= Math.ceil(activityTotal / activityPageSize) || activityLoading}
                          className="h-9 px-3 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                        >
                          <FontAwesomeIcon icon={faChevronRight} />
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </section>

      {activeTab === 'users' && (
        <section className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-5 border border-purple-200">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-purple-600 rounded-xl flex items-center justify-center">
                <FontAwesomeIcon icon={faCrown} className="text-white text-xl" />
              </div>
              <span className="text-2xl font-bold text-purple-600">{roleCount('admin')}</span>
            </div>
            <div className="text-sm font-semibold text-textPrimary mb-1">Admin</div>
            <div className="text-xs text-textSecondary">Full system access</div>
          </div>
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-5 border border-blue-200">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center">
                <FontAwesomeIcon icon={faUserTie} className="text-white text-xl" />
              </div>
              <span className="text-2xl font-bold text-blue-600">{roleCount('approver')}</span>
            </div>
            <div className="text-sm font-semibold text-textPrimary mb-1">Approver</div>
            <div className="text-xs text-textSecondary">Team oversight & approval</div>
          </div>
          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-5 border border-green-200">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-green-600 rounded-xl flex items-center justify-center">
                <FontAwesomeIcon icon={faCalculator} className="text-white text-xl" />
              </div>
              <span className="text-2xl font-bold text-green-600">{roleCount('finance')}</span>
            </div>
            <div className="text-sm font-semibold text-textPrimary mb-1">Finance</div>
            <div className="text-xs text-textSecondary">Financial operations</div>
          </div>
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-5 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-gray-600 rounded-xl flex items-center justify-center">
                <FontAwesomeIcon icon={faUser} className="text-white text-xl" />
              </div>
              <span className="text-2xl font-bold text-gray-600">{roleCount('employee')}</span>
            </div>
            <div className="text-sm font-semibold text-textPrimary mb-1">Employee</div>
            <div className="text-xs text-textSecondary">Standard user access</div>
          </div>
        </section>
      )}

      {/* User modal */}
      {modalMode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={closeModal} aria-hidden />
          <div className="relative bg-surface rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-surface border-b border-borderColor px-8 py-6 flex items-center justify-between z-10">
              <div>
                <h2 className="text-2xl font-bold text-textPrimary mb-1">
                  {modalMode === 'add' && 'Add User'}
                  {modalMode === 'edit' && 'Edit User'}
                  {modalMode === 'view' && 'View User'}
                </h2>
                <p className="text-sm text-textSecondary">
                  {modalMode === 'add' && 'Create a new user account'}
                  {modalMode === 'edit' && 'Update user information and permissions'}
                  {modalMode === 'view' && 'User details'}
                </p>
              </div>
              <button type="button" onClick={closeModal} className="w-10 h-10 flex items-center justify-center text-textMuted hover:text-textPrimary hover:bg-gray-100 rounded-lg">
                <FontAwesomeIcon icon={faClose} className="text-xl" />
              </button>
            </div>
            <div className="p-8">
              <div className="grid grid-cols-2 gap-6 mb-6">
                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-2">First Name *</label>
                  <input
                    type="text"
                    value={formFirst}
                    onChange={(e) => setFormFirst(e.target.value)}
                    disabled={modalMode === 'view'}
                    className="w-full h-10 px-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-50 disabled:text-textSecondary"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-2">Last Name *</label>
                  <input
                    type="text"
                    value={formLast}
                    onChange={(e) => setFormLast(e.target.value)}
                    disabled={modalMode === 'view'}
                    className="w-full h-10 px-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-50 disabled:text-textSecondary"
                  />
                </div>
              </div>
              <div className="mb-6">
                <label className="block text-sm font-medium text-textPrimary mb-2">Email *</label>
                <input
                  type="email"
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  disabled={modalMode === 'view' || modalMode === 'edit'}
                  className="w-full h-10 px-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-50 disabled:text-textSecondary"
                />
              </div>
              {modalMode === 'add' && (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-textPrimary mb-2">Password *</label>
                  <input
                    type="password"
                    value={formPassword}
                    onChange={(e) => setFormPassword(e.target.value)}
                    className="w-full h-10 px-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>
              )}
              <div className="mb-6">
                <label className="block text-sm font-medium text-textPrimary mb-2">Status</label>
                <select
                  value={formStatus}
                  onChange={(e) => setFormStatus(e.target.value)}
                  disabled={modalMode === 'view'}
                  className="w-full h-10 px-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white disabled:bg-gray-50"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
              {(modalMode === 'add' || modalMode === 'edit' || modalMode === 'view') && (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-textPrimary mb-2">Roles</label>
                  <div className="flex flex-wrap gap-3">
                    {roles.map((r) => (
                      <label
                        key={r.id}
                        className={`inline-flex items-center gap-2 px-3 py-2 border rounded-lg cursor-pointer ${formRoleIds.includes(r.id) ? 'border-primary bg-indigo-50 text-primary' : 'border-borderColor bg-white text-textSecondary'}`}
                      >
                        <input
                          type="checkbox"
                          checked={formRoleIds.includes(r.id)}
                          onChange={() => toggleFormRole(r.id)}
                          disabled={modalMode === 'view'}
                          className="w-4 h-4 text-primary border-borderColor rounded focus:ring-primary"
                        />
                        <span className="text-sm font-medium capitalize">{roleDisplayName(r.name)}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
              {(modalMode === 'add' || modalMode === 'edit') && (
                <div className="flex justify-end space-x-3">
                  <button type="button" onClick={closeModal} className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50">
                    Cancel
                  </button>
                  <button type="button" onClick={handleSaveUser} disabled={saving} className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium disabled:opacity-50">
                    {saving ? 'Saving...' : 'Save'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Bulk Change Role modal */}
      {showBulkRoleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setShowBulkRoleModal(false)} aria-hidden />
          <div className="relative bg-surface rounded-2xl shadow-2xl w-full max-w-md p-6">
            <h3 className="text-lg font-semibold text-textPrimary mb-2">Change Role</h3>
            <p className="text-sm text-textSecondary mb-4">Set role for {selectedIds.size} selected user(s). This replaces their current role(s).</p>
            <div className="mb-6">
              <label className="block text-sm font-medium text-textPrimary mb-2">Role</label>
              <select
                value={bulkRoleId}
                onChange={(e) => setBulkRoleId(e.target.value)}
                className="w-full h-10 px-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
              >
                {roles.map((r) => (
                  <option key={r.id} value={r.id}>{roleDisplayName(r.name)}</option>
                ))}
              </select>
            </div>
            <div className="flex justify-end space-x-3">
              <button type="button" onClick={() => setShowBulkRoleModal(false)} className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50">
                Cancel
              </button>
              <button type="button" onClick={handleBulkChangeRoleApply} disabled={bulkActionLoading} className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium disabled:opacity-50">
                {bulkActionLoading ? 'Updating...' : 'Apply'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
