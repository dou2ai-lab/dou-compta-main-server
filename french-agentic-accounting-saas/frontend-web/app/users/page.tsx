'use client'

import { useState, useEffect, useCallback } from 'react'
import Badge from '@/components/ui/Badge'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faUsers,
  faPlus,
  faDownload,
  faUpload,
  faEdit,
  faTrash,
  faEye,
  faUserSecret,
  faBan,
  faCheckCircle,
  faClock,
  faShieldAlt,
  faBuilding,
  faCircleDot,
  faFilter,
  faTimes,
  faUserTag,
  faSearch,
  faCrown,
  faUserTie,
  faChevronDown,
  faSpinner,
  faExclamationTriangle,
} from '@fortawesome/free-solid-svg-icons'
import { adminAPI, type AdminUser, type AdminRole, type AdminActivityItem } from '@/lib/api'
import { getAuthErrorMessage } from '@/lib/api'

const ROLE_STYLE: Record<string, string> = {
  admin: 'text-purple-600 bg-purple-50',
  approver: 'text-blue-600 bg-blue-50',
  finance: 'text-green-600 bg-green-50',
  employee: 'text-gray-600 bg-gray-100',
}

function roleDisplayName(name: string): string {
  return name ? name.charAt(0).toUpperCase() + name.slice(1) : name
}

export default function UsersPage() {
  const [activeTab, setActiveTab] = useState<'users' | 'roles' | 'activity'>('users')
  const [users, setUsers] = useState<AdminUser[]>([])
  const [roles, setRoles] = useState<AdminRole[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState<'add' | 'edit' | null>(null)
  const [editUser, setEditUser] = useState<AdminUser | null>(null)
  const [formEmail, setFormEmail] = useState('')
  const [formFirstName, setFormFirstName] = useState('')
  const [formLastName, setFormLastName] = useState('')
  const [formPassword, setFormPassword] = useState('')
  const [formStatus, setFormStatus] = useState('active')
  const [formRoleIds, setFormRoleIds] = useState<string[]>([])
  const [submitLoading, setSubmitLoading] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)
  const [activities, setActivities] = useState<AdminActivityItem[]>([])
  const [activityTotal, setActivityTotal] = useState(0)
  const [activityPage, setActivityPage] = useState(1)
  const [activityPageSize] = useState(20)
  const [activityLoading, setActivityLoading] = useState(false)

  const loadUsers = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await adminAPI.users({
        page,
        page_size: pageSize,
        search: search || undefined,
        role_id: roleFilter || undefined,
        status: statusFilter === 'All Status' || !statusFilter ? undefined : statusFilter,
      })
      setUsers(data?.users ?? [])
      setTotal(data?.total ?? 0)
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, 'Failed to load users'))
      setUsers([])
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, search, roleFilter, statusFilter])

  const loadRoles = useCallback(async () => {
    try {
      const data = await adminAPI.roles()
      setRoles(data?.roles ?? [])
    } catch (err: unknown) {
      console.error('Failed to load roles:', err)
      setRoles([])
    }
  }, [])

  useEffect(() => {
    if (activeTab === 'users') loadUsers()
  }, [activeTab, loadUsers])

  useEffect(() => {
    if (activeTab === 'roles') loadRoles()
  }, [activeTab, loadRoles])

  const loadActivity = useCallback(async () => {
    setActivityLoading(true)
    try {
      const result = await adminAPI.activity({ page: activityPage, page_size: activityPageSize })
      setActivities(result.activities ?? [])
      setActivityTotal(result.total ?? 0)
    } catch (err: unknown) {
      console.error('Failed to load activity:', err)
      setActivities([])
      setActivityTotal(0)
    } finally {
      setActivityLoading(false)
    }
  }, [activityPage, activityPageSize])

  useEffect(() => {
    if (activeTab === 'activity') loadActivity()
  }, [activeTab, activityPage, loadActivity])

  const openAddModal = () => {
    setEditUser(null)
    setFormEmail('')
    setFormFirstName('')
    setFormLastName('')
    setFormPassword('')
    setFormStatus('active')
    setFormRoleIds([])
    setModalOpen('add')
  }

  const openEditModal = async (user: AdminUser) => {
    setEditUser(user)
    setFormEmail(user.email)
    setFormFirstName(user.first_name || '')
    setFormLastName(user.last_name || '')
    setFormPassword('')
    setFormStatus(user.status || 'active')
    setFormRoleIds((user.roles || []).map((r) => r.id))
    setModalOpen('edit')
  }

  const closeModal = () => {
    setModalOpen(null)
    setEditUser(null)
    setSubmitLoading(false)
  }

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitLoading(true)
    setError(null)
    try {
      await adminAPI.createUser({
        email: formEmail,
        first_name: formFirstName,
        last_name: formLastName,
        password: formPassword || undefined,
        status: formStatus,
        role_ids: formRoleIds.length ? formRoleIds : undefined,
      })
      closeModal()
      loadUsers()
      if (activeTab === 'roles') loadRoles()
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, 'Failed to create user'))
    } finally {
      setSubmitLoading(false)
    }
  }

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editUser) return
    setSubmitLoading(true)
    setError(null)
    try {
      await adminAPI.updateUser(editUser.id, {
        email: formEmail,
        first_name: formFirstName,
        last_name: formLastName,
        password: formPassword || undefined,
        status: formStatus,
        role_ids: formRoleIds,
      })
      closeModal()
      loadUsers()
      if (activeTab === 'roles') loadRoles()
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, 'Failed to update user'))
    } finally {
      setSubmitLoading(false)
    }
  }

  const handleDeleteUser = async (userId: string) => {
    setError(null)
    try {
      await adminAPI.deleteUser(userId)
      setDeleteConfirm(null)
      loadUsers()
      if (activeTab === 'roles') loadRoles()
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, 'Failed to delete user'))
    }
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

  const activeCount = users.filter((u) => (u.status || '').toLowerCase() === 'active').length
  const adminCount = users.filter((u) => (u.roles || []).some((r) => r.name?.toLowerCase() === 'admin')).length

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">Users & Roles Management</h1>
            <p className="text-textSecondary">Manage user accounts, roles, and permissions across the organization</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              type="button"
              className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2"
            >
              <FontAwesomeIcon icon={faDownload} />
              <span>Export Users</span>
            </button>
            <button
              type="button"
              className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2"
            >
              <FontAwesomeIcon icon={faUpload} />
              <span>Import Users</span>
            </button>
            <button
              type="button"
              className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2"
              onClick={openAddModal}
            >
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
            </div>
            <div className="text-2xl font-bold text-textPrimary mb-1">{total}</div>
            <div className="text-sm text-textSecondary">Total Users</div>
          </div>
          <div className="bg-surface rounded-xl p-5 border border-borderColor shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faCheckCircle} className="text-successGreen text-xl" />
              </div>
            </div>
            <div className="text-2xl font-bold text-textPrimary mb-1">{activeCount}</div>
            <div className="text-sm text-textSecondary">Active (this page)</div>
          </div>
          <div className="bg-surface rounded-xl p-5 border border-borderColor shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="w-12 h-12 bg-purple-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faShieldAlt} className="text-purple-600 text-xl" />
              </div>
            </div>
            <div className="text-2xl font-bold text-textPrimary mb-1">{adminCount}</div>
            <div className="text-sm text-textSecondary">Administrators (this page)</div>
          </div>
          <div className="bg-surface rounded-xl p-5 border border-borderColor shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="w-12 h-12 bg-amber-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faClock} className="text-warningAmber text-xl" />
              </div>
            </div>
            <div className="text-2xl font-bold text-textPrimary mb-1">{roles.length}</div>
            <div className="text-sm text-textSecondary">Roles</div>
          </div>
        </div>
      </section>

      <section className="bg-surface rounded-xl border border-borderColor shadow-sm">
        <div className="border-b border-borderColor px-6">
          <div className="flex items-center space-x-6">
            <button
              type="button"
              onClick={() => setActiveTab('users')}
              className={`py-4 px-2 border-b-2 text-sm font-medium ${
                activeTab === 'users' ? 'border-primary text-primary' : 'border-transparent text-textSecondary hover:text-textPrimary hover:border-gray-300'
              }`}
            >
              User List
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('roles')}
              className={`py-4 px-2 border-b-2 text-sm font-medium ${
                activeTab === 'roles' ? 'border-primary text-primary' : 'border-transparent text-textSecondary hover:text-textPrimary hover:border-gray-300'
              }`}
            >
              Roles & Permissions
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('activity')}
              className={`py-4 px-2 border-b-2 text-sm font-medium ${
                activeTab === 'activity' ? 'border-primary text-primary' : 'border-transparent text-textSecondary hover:text-textPrimary hover:border-gray-300'
              }`}
            >
              Activity Log
            </button>
          </div>
        </div>

        {error && (
          <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-800 text-sm">
            <FontAwesomeIcon icon={faExclamationTriangle} />
            {error}
          </div>
        )}

        {activeTab === 'users' && (
          <div className="p-6">
            <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
              <div className="flex items-center space-x-3 flex-wrap">
                <div className="relative">
                  <FontAwesomeIcon icon={faSearch} className="absolute left-3 top-1/2 -translate-y-1/2 text-textMuted text-sm" />
                  <input
                    type="text"
                    placeholder="Search by name or email..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && loadUsers()}
                    className="h-10 pl-10 pr-4 border border-borderColor rounded-lg text-sm w-56 focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => loadUsers()}
                  className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50"
                >
                  Search
                </button>
                <select
                  value={roleFilter}
                  onChange={(e) => setRoleFilter(e.target.value)}
                  className="h-10 pl-10 pr-8 border border-borderColor rounded-lg text-sm appearance-none bg-white cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">All Roles</option>
                  {roles.map((r) => (
                    <option key={r.id} value={r.id}>
                      {roleDisplayName(r.name)}
                    </option>
                  ))}
                </select>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="h-10 pl-10 pr-8 border border-borderColor rounded-lg text-sm appearance-none bg-white cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">All Status</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              {loading ? (
                <div className="flex items-center justify-center py-12 text-textSecondary">
                  <FontAwesomeIcon icon={faSpinner} spin className="mr-2" />
                  Loading users...
                </div>
              ) : (
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
                      <th className="text-center py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">Status</th>
                      <th className="text-right py-3 px-4 text-xs font-semibold text-textMuted uppercase tracking-wide">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
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
                            <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
                              <span className="text-sm font-medium text-primary">
                                {(user.first_name?.[0] || user.email?.[0] || '?').toUpperCase()}
                              </span>
                            </div>
                            <div>
                              <div className="text-sm font-medium text-textPrimary">
                                {user.first_name} {user.last_name}
                              </div>
                              <div className="text-xs text-textSecondary">ID: {user.id.slice(0, 8)}...</div>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-sm text-textSecondary">{user.email}</td>
                        <td className="py-3 px-4">
                          {(user.roles || []).length === 0 ? (
                            <span className="text-xs text-textMuted">No role</span>
                          ) : (
                            (user.roles || []).map((r) => (
                              <span
                                key={r.id}
                                className={`inline-flex items-center text-xs font-medium px-2 py-1 rounded-full mr-1 ${
                                  ROLE_STYLE[r.name?.toLowerCase() || ''] || 'text-gray-600 bg-gray-100'
                                }`}
                              >
                                {r.name?.toLowerCase() === 'admin' && <FontAwesomeIcon icon={faCrown} className="mr-1" />}
                                {r.name?.toLowerCase() === 'approver' && <FontAwesomeIcon icon={faUserTie} className="mr-1" />}
                                {roleDisplayName(r.name)}
                              </span>
                            ))
                          )}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span
                            className={`inline-flex items-center text-xs font-medium px-2 py-1 rounded-full ${
                              (user.status || '').toLowerCase() === 'active' ? 'text-successGreen bg-green-50' : 'text-textMuted bg-gray-100'
                            }`}
                          >
                            <FontAwesomeIcon
                              icon={faCheckCircle}
                              className={`text-[6px] mr-1 ${(user.status || '').toLowerCase() === 'active' ? 'opacity-100' : 'opacity-50'}`}
                            />
                            {roleDisplayName(user.status || '')}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end space-x-2">
                            <button
                              type="button"
                              className="w-8 h-8 flex items-center justify-center text-textMuted hover:text-infoBlue hover:bg-blue-50 rounded-lg"
                              title="Edit"
                              onClick={() => openEditModal(user)}
                            >
                              <FontAwesomeIcon icon={faEdit} className="text-sm" />
                            </button>
                            {deleteConfirm === user.id ? (
                              <>
                                <span className="text-xs text-errorRed font-medium">Delete?</span>
                                <button
                                  type="button"
                                  className="w-8 h-8 flex items-center justify-center text-errorRed hover:bg-red-50 rounded-lg"
                                  title="Confirm delete"
                                  onClick={() => handleDeleteUser(user.id)}
                                >
                                  <FontAwesomeIcon icon={faCheckCircle} className="text-sm" />
                                </button>
                                <button
                                  type="button"
                                  className="w-8 h-8 flex items-center justify-center text-textMuted hover:bg-gray-100 rounded-lg"
                                  title="Cancel"
                                  onClick={() => setDeleteConfirm(null)}
                                >
                                  <FontAwesomeIcon icon={faTimes} className="text-sm" />
                                </button>
                              </>
                            ) : (
                              <button
                                type="button"
                                className="w-8 h-8 flex items-center justify-center text-textMuted hover:text-errorRed hover:bg-red-50 rounded-lg"
                                title="Delete"
                                onClick={() => setDeleteConfirm(user.id)}
                              >
                                <FontAwesomeIcon icon={faTrash} className="text-sm" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            {!loading && total > pageSize && (
              <div className="flex items-center justify-between mt-4">
                <span className="text-sm text-textSecondary">
                  Page {page} of {Math.ceil(total / pageSize)} ({total} total)
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => p - 1)}
                    className="h-9 px-3 border border-borderColor rounded-lg text-sm disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    type="button"
                    disabled={page >= Math.ceil(total / pageSize)}
                    onClick={() => setPage((p) => p + 1)}
                    className="h-9 px-3 border border-borderColor rounded-lg text-sm disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'roles' && (
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-textPrimary">Roles & Permissions</h2>
            </div>
            {roles.length === 0 && !loading ? (
              <div className="text-textSecondary py-8">No roles found. Run database bootstrap to seed roles.</div>
            ) : (
              <div className="grid grid-cols-2 gap-6">
                {roles.map((role) => (
                  <div key={role.id} className="p-6 border border-borderColor rounded-xl hover:border-primary transition-colors">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div
                          className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            ROLE_STYLE[role.name?.toLowerCase() || ''] || 'text-gray-600 bg-gray-100'
                          }`}
                        >
                          {role.name?.toLowerCase() === 'admin' && <FontAwesomeIcon icon={faCrown} />}
                          {role.name?.toLowerCase() === 'approver' && <FontAwesomeIcon icon={faUserTie} />}
                          {role.name?.toLowerCase() === 'finance' && <FontAwesomeIcon icon={faShieldAlt} />}
                          {(role.name?.toLowerCase() === 'employee' || !role.name) && <FontAwesomeIcon icon={faUsers} />}
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-textPrimary">{roleDisplayName(role.name || '')}</h3>
                          {role.description && (
                            <p className="text-xs text-textSecondary mt-0.5">{role.description}</p>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-textSecondary">Users</span>
                        <span className="font-medium text-textPrimary">{role.user_count ?? 0}</span>
                      </div>
                      {role.is_system_role && (
                        <span className="text-xs text-textMuted">System role (managed by seed)</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'activity' && (
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-textPrimary">Activity Log</h2>
              <button
                type="button"
                onClick={() => loadActivity()}
                className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50"
              >
                Refresh
              </button>
            </div>
            {activityLoading ? (
              <div className="flex items-center justify-center py-12 text-textSecondary">
                <FontAwesomeIcon icon={faSpinner} spin className="mr-2" />
                Loading activity...
              </div>
            ) : activities.length === 0 ? (
              <div className="border border-borderColor rounded-lg p-6 text-center text-textSecondary text-sm">
                No activity recorded yet. User and role changes will appear here.
              </div>
            ) : (
              <>
                <div className="border border-borderColor rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-gray-50 border-b border-borderColor">
                        <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase">Time</th>
                        <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase">Action</th>
                        <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase">Performed by</th>
                        <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase">Target</th>
                      </tr>
                    </thead>
                    <tbody>
                      {activities.map((a) => (
                        <tr key={a.id} className="border-b border-borderColor last:border-0 hover:bg-gray-50">
                          <td className="py-3 px-4 text-sm text-textSecondary">
                            {a.created_at ? new Date(a.created_at).toLocaleString() : '—'}
                          </td>
                          <td className="py-3 px-4 text-sm font-medium text-textPrimary">{a.action_label || a.action}</td>
                          <td className="py-3 px-4 text-sm text-textSecondary">
                            {a.performed_by_name || a.performed_by_email || a.performed_by_id}
                          </td>
                          <td className="py-3 px-4 text-sm text-textSecondary">
                            {a.target_user_name || a.target_user_email || a.target_role_name || '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {activityTotal > activityPageSize && (
                  <div className="flex items-center justify-between mt-4">
                    <span className="text-sm text-textSecondary">
                      Page {activityPage} of {Math.ceil(activityTotal / activityPageSize)} ({activityTotal} total)
                    </span>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        disabled={activityPage <= 1}
                        onClick={() => setActivityPage((p) => p - 1)}
                        className="h-9 px-3 border border-borderColor rounded-lg text-sm disabled:opacity-50"
                      >
                        Previous
                      </button>
                      <button
                        type="button"
                        disabled={activityPage >= Math.ceil(activityTotal / activityPageSize)}
                        onClick={() => setActivityPage((p) => p + 1)}
                        className="h-9 px-3 border border-borderColor rounded-lg text-sm disabled:opacity-50"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </section>

      {/* Add / Edit User Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={closeModal}>
          <div
            className="bg-surface rounded-xl border border-borderColor shadow-xl w-full max-w-md mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 border-b border-borderColor">
              <h2 className="text-xl font-semibold text-textPrimary">
                {modalOpen === 'add' ? 'Add User' : 'Edit User'}
              </h2>
            </div>
            <form
              onSubmit={modalOpen === 'add' ? handleCreateUser : handleUpdateUser}
              className="p-6 space-y-4"
            >
              <div>
                <label className="block text-sm font-medium text-textPrimary mb-1">Email</label>
                <input
                  type="email"
                  required
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="user@example.com"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-1">First name</label>
                  <input
                    type="text"
                    value={formFirstName}
                    onChange={(e) => setFormFirstName(e.target.value)}
                    className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-1">Last name</label>
                  <input
                    type="text"
                    value={formLastName}
                    onChange={(e) => setFormLastName(e.target.value)}
                    className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-textPrimary mb-1">
                  Password {modalOpen === 'edit' && '(leave blank to keep current)'}
                </label>
                <input
                  type="password"
                  value={formPassword}
                  onChange={(e) => setFormPassword(e.target.value)}
                  className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder={modalOpen === 'edit' ? '••••••••' : 'Set password'}
                  required={modalOpen === 'add'}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-textPrimary mb-1">Status</label>
                <select
                  value={formStatus}
                  onChange={(e) => setFormStatus(e.target.value)}
                  className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-textPrimary mb-1">Roles</label>
                <div className="flex flex-wrap gap-2">
                  {roles.map((r) => (
                    <label key={r.id} className="inline-flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formRoleIds.includes(r.id)}
                        onChange={(e) => {
                          if (e.target.checked) setFormRoleIds((prev) => [...prev, r.id])
                          else setFormRoleIds((prev) => prev.filter((id) => id !== r.id))
                        }}
                        className="w-4 h-4 text-primary border-borderColor rounded focus:ring-primary"
                      />
                      <span className="text-sm text-textPrimary">{roleDisplayName(r.name || '')}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitLoading}
                  className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium disabled:opacity-50 flex items-center gap-2"
                >
                  {submitLoading && <FontAwesomeIcon icon={faSpinner} spin />}
                  {modalOpen === 'add' ? 'Create User' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
