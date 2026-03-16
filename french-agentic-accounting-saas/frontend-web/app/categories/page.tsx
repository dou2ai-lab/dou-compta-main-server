'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faFolder,
  faPlus,
  faDownload,
  faSync,
  faChevronDown,
  faChevronRight,
  faSearch,
  faPlane,
  faUtensils,
  faHotel,
  faLaptop,
  faPhone,
  faUsers,
  faBook,
  faBuilding,
  faGift,
  faGripVertical,
  faEdit,
  faSave,
  faTimes,
  faCheckCircle,
  faSpinner,
  faExclamationTriangle,
  faTrash,
} from '@fortawesome/free-solid-svg-icons'
import { adminAPI, type AdminCategory, type AdminGLAccount, getAuthErrorMessage } from '@/lib/api'

const ICON_MAP: Record<string, { icon: typeof faFolder; color: string }> = {
  travel: { icon: faPlane, color: 'text-infoBlue' },
  meal: { icon: faUtensils, color: 'text-successGreen' },
  accommodation: { icon: faHotel, color: 'text-purple-600' },
  office: { icon: faLaptop, color: 'text-pink-600' },
  communication: { icon: faPhone, color: 'text-orange-600' },
  professional: { icon: faUsers, color: 'text-cyan-600' },
  training: { icon: faBook, color: 'text-indigo-600' },
  facilities: { icon: faBuilding, color: 'text-amber-600' },
  gift: { icon: faGift, color: 'text-red-600' },
}

function getIcon(name: string, code: string) {
  const key = (name || code || '').toLowerCase().replace(/\s+/g, '_').slice(0, 12)
  for (const [k, v] of Object.entries(ICON_MAP)) {
    if (key.includes(k) || code.toLowerCase().includes(k)) return v
  }
  return { icon: faFolder, color: 'text-primary' }
}

type TreeItem = AdminCategory & { children: TreeItem[] }

function buildTree(categories: AdminCategory[]): TreeItem[] {
  const byId = new Map<string, TreeItem>()
  categories.forEach((c) => byId.set(c.id, { ...c, children: [] }))
  const roots: TreeItem[] = []
  categories.forEach((c) => {
    const node = byId.get(c.id)!
    if (!c.parent_id) roots.push(node)
    else {
      const parent = byId.get(c.parent_id)
      if (parent) parent.children.push(node)
      else roots.push(node)
    }
  })
  roots.sort((a, b) => a.name.localeCompare(b.name))
  roots.forEach((r) => r.children.sort((a, b) => a.name.localeCompare(b.name)))
  return roots
}

export default function CategoriesPage() {
  const [categories, setCategories] = useState<AdminCategory[]>([])
  const [glAccounts, setGlAccounts] = useState<AdminGLAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [categorySearch, setCategorySearch] = useState('')
  const [saveLoading, setSaveLoading] = useState(false)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [createParentId, setCreateParentId] = useState<string | null>(null)
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)

  const tree = useMemo(() => buildTree(categories), [categories])
  const glById = useMemo(() => new Map(glAccounts.map((g) => [g.id, g])), [glAccounts])
  const selected = categories.find((c) => c.id === selectedId)
  const selectedChildren = useMemo(
    () => categories.filter((c) => c.parent_id === selectedId),
    [categories, selectedId]
  )

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [catList, glList] = await Promise.all([adminAPI.listCategories(), adminAPI.listGLAccounts()])
      setCategories(catList)
      setGlAccounts(glList)
      if (catList.length && !selectedId) setSelectedId(catList[0].id)
      if (selectedId && !catList.some((c) => c.id === selectedId)) setSelectedId(catList[0]?.id ?? null)
      if (expanded.size === 0 && catList.length) setExpanded(new Set([catList[0].id]))
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, 'Failed to load categories and GL accounts'))
      setCategories([])
      setGlAccounts([])
    } finally {
      setLoading(false)
    }
  }, [selectedId, expanded.size])

  useEffect(() => {
    loadData()
  }, [loadData])

  const toggle = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const filterTree = (items: TreeItem[], search: string): TreeItem[] => {
    if (!search.trim()) return items
    const s = search.trim().toLowerCase()
    return items.filter((item) => {
      const match = item.name.toLowerCase().includes(s) || item.code.toLowerCase().includes(s)
      const filteredChildren = filterTree(item.children, search)
      if (filteredChildren.length) return true
      return match
    }).map((item) => ({
      ...item,
      children: filterTree(item.children, search),
    }))
  }

  const filteredTree = useMemo(() => filterTree(tree, categorySearch), [tree, categorySearch])

  const handleSave = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!selected) return
    const form = e.currentTarget
    const name = (form.querySelector('[name="categoryName"]') as HTMLInputElement)?.value?.trim()
    const code = (form.querySelector('[name="categoryCode"]') as HTMLInputElement)?.value?.trim()
    const description = (form.querySelector('[name="categoryDescription"]') as HTMLTextAreaElement)?.value?.trim() || null
    const gl_account_id = (form.querySelector('[name="glAccountId"]') as HTMLSelectElement)?.value || null
    const isActive = (form.querySelector('[name="isActive"]') as HTMLSelectElement)?.value === 'active'
    if (!name || !code) return
    setSaveLoading(true)
    setError(null)
    try {
      await adminAPI.updateCategory(selected.id, {
        name,
        code,
        description,
        gl_account_id: gl_account_id || null,
        is_active: isActive,
      })
      loadData()
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, 'Failed to update category'))
    } finally {
      setSaveLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const form = e.currentTarget
    const name = (form.querySelector('[name="newCategoryName"]') as HTMLInputElement)?.value?.trim()
    const code = (form.querySelector('[name="newCategoryCode"]') as HTMLInputElement)?.value?.trim()
    const description = (form.querySelector('[name="newCategoryDescription"]') as HTMLTextAreaElement)?.value?.trim() || null
    const gl_account_id = (form.querySelector('[name="newGlAccountId"]') as HTMLSelectElement)?.value || null
    if (!name || !code) return
    setSaveLoading(true)
    setError(null)
    try {
      await adminAPI.createCategory({
        name,
        code,
        description,
        gl_account_id: gl_account_id || null,
        parent_id: createParentId,
      })
      setCreateModalOpen(false)
      setCreateParentId(null)
      loadData()
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, 'Failed to create category'))
    } finally {
      setSaveLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    setError(null)
    try {
      await adminAPI.deleteCategory(id)
      setDeleteConfirmId(null)
      if (selectedId === id) setSelectedId(categories.find((c) => c.id !== id)?.id ?? null)
      loadData()
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, 'Failed to delete category'))
    }
  }

  const totalCategories = categories.length
  const activeCategories = categories.filter((c) => c.is_active).length
  const parentCount = categories.filter((c) => !c.parent_id).length
  const childCount = totalCategories - parentCount

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">Categories & GL Account Management</h1>
            <p className="text-textSecondary">Manage expense categories and general ledger account mappings</p>
          </div>
          <div className="flex items-center space-x-3">
            <button type="button" className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
              <FontAwesomeIcon icon={faDownload} />
              <span>Export Categories</span>
            </button>
            <button type="button" className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
              <FontAwesomeIcon icon={faSync} />
              <span>Import from ERP</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setCreateParentId(null)
                setCreateModalOpen(true)
              }}
              className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2"
            >
              <FontAwesomeIcon icon={faPlus} />
              <span>New Category</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4">
          <div className="bg-surface rounded-xl p-5 border border-borderColor">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-textSecondary">Total Categories</span>
              <div className="w-10 h-10 bg-indigo-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faFolder} className="text-primary" />
              </div>
            </div>
            <div className="text-2xl font-bold text-textPrimary">{totalCategories}</div>
            <div className="text-xs text-textMuted mt-1">{parentCount} parent, {childCount} child</div>
          </div>
          <div className="bg-surface rounded-xl p-5 border border-borderColor">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-textSecondary">GL Accounts</span>
              <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faSync} className="text-successGreen" />
              </div>
            </div>
            <div className="text-2xl font-bold text-textPrimary">{glAccounts.length}</div>
            <div className="text-xs text-textMuted mt-1">Available for mapping</div>
          </div>
          <div className="bg-surface rounded-xl p-5 border border-borderColor">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-textSecondary">Active Categories</span>
              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faCheckCircle} className="text-infoBlue" />
              </div>
            </div>
            <div className="text-2xl font-bold text-textPrimary">{activeCategories}</div>
            <div className="text-xs text-textMuted mt-1">{totalCategories - activeCategories} inactive</div>
          </div>
          <div className="bg-surface rounded-xl p-5 border border-borderColor">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-textSecondary">Last Sync</span>
              <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faSync} className="text-purple-600" />
              </div>
            </div>
            <div className="text-2xl font-bold text-textPrimary">—</div>
            <div className="text-xs text-textMuted mt-1">Manual refresh above</div>
          </div>
        </div>
      </section>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-800 text-sm">
          <FontAwesomeIcon icon={faExclamationTriangle} />
          {error}
        </div>
      )}

      <div className="grid grid-cols-12 gap-6">
        <section className="col-span-5 bg-surface rounded-xl border border-borderColor">
          <div className="p-6 border-b border-borderColor">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-textPrimary">Category Tree</h2>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => setExpanded(new Set(categories.map((c) => c.id)))}
                  className="w-8 h-8 flex items-center justify-center text-textSecondary hover:text-textPrimary hover:bg-gray-50 rounded-lg"
                  title="Expand All"
                >
                  <FontAwesomeIcon icon={faChevronDown} />
                </button>
                <button
                  type="button"
                  onClick={() => setExpanded(new Set())}
                  className="w-8 h-8 flex items-center justify-center text-textSecondary hover:text-textPrimary hover:bg-gray-50 rounded-lg"
                  title="Collapse All"
                >
                  <FontAwesomeIcon icon={faChevronRight} />
                </button>
              </div>
            </div>
            <div className="relative">
              <FontAwesomeIcon icon={faSearch} className="absolute left-3 top-1/2 -translate-y-1/2 text-textMuted" />
              <input
                type="text"
                placeholder="Search categories..."
                value={categorySearch}
                onChange={(e) => setCategorySearch(e.target.value)}
                className="w-full h-10 pl-10 pr-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          </div>
          <div className="p-4 overflow-y-auto max-h-[calc(100vh-420px)]">
            {loading ? (
              <div className="flex items-center justify-center py-12 text-textSecondary">
                <FontAwesomeIcon icon={faSpinner} spin className="mr-2" />
                Loading...
              </div>
            ) : (
              <div className="space-y-1">
                {filteredTree.map((item) => {
                  const isExpanded = expanded.has(item.id)
                  const isSelected = selectedId === item.id
                  const { icon, color } = getIcon(item.name, item.code)
                  return (
                    <div key={item.id} className="transition-all duration-200 rounded-lg">
                      <div
                        onClick={() => setSelectedId(item.id)}
                        className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                          isSelected ? 'bg-indigo-50 border-l-[3px] border-l-primary' : 'hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              toggle(item.id)
                            }}
                            className="w-5 h-5 flex items-center justify-center text-textMuted hover:text-textPrimary"
                          >
                            {item.children.length > 0 ? (
                              isExpanded ? (
                                <FontAwesomeIcon icon={faChevronDown} className="text-xs" />
                              ) : (
                                <FontAwesomeIcon icon={faChevronRight} className="text-xs" />
                              )
                            ) : (
                              <span className="w-2" />
                            )}
                          </button>
                          <FontAwesomeIcon icon={icon} className={color} />
                          <div>
                            <div className="text-sm font-medium text-textPrimary">{item.name}</div>
                            <div className="text-xs text-textMuted">{item.children.length} subcategories</div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span
                            className={`text-xs font-medium px-2 py-1 rounded-full ${
                              item.is_active ? 'text-successGreen bg-green-50' : 'text-textMuted bg-gray-100'
                            }`}
                          >
                            {item.is_active ? 'Active' : 'Inactive'}
                          </span>
                          <button
                            type="button"
                            className="w-6 h-6 flex items-center justify-center text-textMuted hover:text-textPrimary"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <FontAwesomeIcon icon={faGripVertical} className="text-xs" />
                          </button>
                        </div>
                      </div>
                      {item.children.length > 0 && isExpanded && (
                        <div className="ml-11 space-y-1 pb-2">
                          {item.children.map((child) => {
                            const gl = child.gl_account_id ? glById.get(child.gl_account_id) : null
                            return (
                              <div
                                key={child.id}
                                className="flex items-center justify-between p-2 hover:bg-gray-50 rounded-lg cursor-pointer"
                                onClick={() => setSelectedId(child.id)}
                              >
                                <div className="flex items-center space-x-3">
                                  <span className="text-sm text-textPrimary">{child.name}</span>
                                </div>
                                <span className="text-xs text-textMuted">{gl?.account_code ?? child.code}</span>
                              </div>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </section>

        <section className="col-span-7 bg-surface rounded-xl border border-borderColor">
          <div className="p-6 border-b border-borderColor">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {selected ? (
                  <>
                    <div className="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center">
                      <FontAwesomeIcon icon={getIcon(selected.name, selected.code).icon} className={`text-primary text-xl ${getIcon(selected.name, selected.code).color}`} />
                    </div>
                    <div>
                      <h2 className="text-xl font-semibold text-textPrimary">{selected.name}</h2>
                      <p className="text-sm text-textSecondary">
                        {selected.parent_id ? 'Subcategory' : 'Parent Category'} • Code: {selected.code}
                      </p>
                    </div>
                  </>
                ) : (
                  <div>
                    <h2 className="text-xl font-semibold text-textPrimary">Category Details</h2>
                    <p className="text-sm text-textSecondary">Select a category from the tree</p>
                  </div>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => {
                    if (selected) {
                      setCreateParentId(selected.id)
                      setCreateModalOpen(true)
                    }
                  }}
                  className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2"
                >
                  <FontAwesomeIcon icon={faPlus} />
                  <span>Add Subcategory</span>
                </button>
                {selected && (
                  <>
                    <button
                      type="button"
                      onClick={() => setDeleteConfirmId(selected.id)}
                      className="h-10 px-4 border border-errorRed text-errorRed rounded-lg text-sm font-medium hover:bg-red-50 flex items-center space-x-2"
                    >
                      <FontAwesomeIcon icon={faTrash} />
                      <span>Delete</span>
                    </button>
                    <button
                      type="submit"
                      form="category-edit-form"
                      disabled={saveLoading}
                      className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2 disabled:opacity-50"
                    >
                      {saveLoading && <FontAwesomeIcon icon={faSpinner} spin />}
                      <FontAwesomeIcon icon={faSave} />
                      <span>Save Changes</span>
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>

          {selected && (
            <form id="category-edit-form" onSubmit={handleSave} className="p-6 space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-textPrimary mb-4">Basic Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-textPrimary mb-2">Category Name *</label>
                    <input
                      name="categoryName"
                      type="text"
                      defaultValue={selected.name}
                      required
                      className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-textPrimary mb-2">Category Code *</label>
                    <input
                      name="categoryCode"
                      type="text"
                      defaultValue={selected.code}
                      required
                      placeholder="e.g. 6250"
                      className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-textPrimary mb-2">GL Account</label>
                    <select
                      name="glAccountId"
                      defaultValue={selected.gl_account_id ?? ''}
                      className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    >
                      <option value="">— None —</option>
                      {glAccounts.map((g) => (
                        <option key={g.id} value={g.id}>
                          {g.account_code} – {g.account_name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-textPrimary mb-2">Status</label>
                    <select
                      name="isActive"
                      defaultValue={selected.is_active ? 'active' : 'inactive'}
                      className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                    </select>
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-textPrimary mb-2">Description</label>
                    <textarea
                      name="categoryDescription"
                      rows={2}
                      defaultValue={selected.description ?? ''}
                      placeholder="Optional description..."
                      className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                  </div>
                </div>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-textPrimary mb-4">Subcategories</h3>
                <div className="border border-borderColor rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-gray-50 border-b border-borderColor">
                        <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase">Subcategory</th>
                        <th className="text-left py-3 px-4 text-xs font-semibold text-textMuted uppercase">GL Code</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedChildren.map((child) => {
                        const gl = child.gl_account_id ? glById.get(child.gl_account_id) : null
                        return (
                          <tr key={child.id} className="border-b border-borderColor last:border-0 hover:bg-gray-50">
                            <td className="py-3 px-4 text-sm text-textPrimary">{child.name}</td>
                            <td className="py-3 px-4 text-sm text-textSecondary">{gl?.account_code ?? child.code}</td>
                          </tr>
                        )
                      })}
                      {selectedChildren.length === 0 && (
                        <tr>
                          <td colSpan={2} className="py-8 text-center text-sm text-textMuted">
                            No subcategories. Use &quot;Add Subcategory&quot; to create one.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </form>
          )}

          {!selected && !loading && (
            <div className="p-16 flex flex-col items-center justify-center text-textMuted">
              <FontAwesomeIcon icon={faFolder} className="text-4xl mb-4 opacity-50" />
              <p className="text-sm">Select a category from the tree to view and edit details</p>
            </div>
          )}
        </section>
      </div>

      {/* Create Category Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => { setCreateModalOpen(false); setCreateParentId(null) }}>
          <div className="bg-surface rounded-xl border border-borderColor shadow-xl w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-borderColor">
              <h2 className="text-xl font-semibold text-textPrimary">{createParentId ? 'New Subcategory' : 'New Category'}</h2>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-textPrimary mb-1">Category Name *</label>
                <input
                  name="newCategoryName"
                  type="text"
                  required
                  placeholder="e.g. Travel & Transport"
                  className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-textPrimary mb-1">Category Code *</label>
                <input
                  name="newCategoryCode"
                  type="text"
                  required
                  placeholder="e.g. 6250"
                  className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-textPrimary mb-1">GL Account</label>
                <select
                  name="newGlAccountId"
                  className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
                >
                  <option value="">— None —</option>
                  {glAccounts.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.account_code} – {g.account_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-textPrimary mb-1">Description</label>
                <textarea
                  name="newCategoryDescription"
                  rows={2}
                  placeholder="Optional"
                  className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => { setCreateModalOpen(false); setCreateParentId(null) }}
                  className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saveLoading}
                  className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium disabled:opacity-50 flex items-center gap-2"
                >
                  {saveLoading && <FontAwesomeIcon icon={faSpinner} spin />}
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete confirm */}
      {deleteConfirmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setDeleteConfirmId(null)}>
          <div className="bg-surface rounded-xl border border-borderColor shadow-xl w-full max-w-sm mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <p className="text-textPrimary mb-4">Delete this category? This may affect expense mappings.</p>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setDeleteConfirmId(null)}
                className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleDelete(deleteConfirmId)}
                className="h-10 px-4 bg-errorRed text-white rounded-lg text-sm font-medium hover:opacity-90"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
