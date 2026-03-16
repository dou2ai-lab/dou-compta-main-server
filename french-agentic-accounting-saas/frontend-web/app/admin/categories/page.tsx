'use client'

import { useState, useEffect, useMemo } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faFolder,
  faPlus,
  faChevronDown,
  faChevronRight,
  faSearch,
  faSave,
  faTrash,
  faTimes,
  faCheckCircle,
  faCalculator,
  faFolderTree,
  faExclamationTriangle,
  faEllipsisV,
  faRobot,
  faSpinner,
} from '@fortawesome/free-solid-svg-icons'
import { useLanguage } from '@/contexts/LanguageContext'
import { adminAPI, type AdminCategory, type AdminGLAccount } from '@/lib/api'

type FormMode = 'none' | 'create' | 'edit'

function buildTree(categories: AdminCategory[]): { roots: AdminCategory[]; childrenByParent: Record<string, AdminCategory[]> } {
  const childrenByParent: Record<string, AdminCategory[]> = {}
  const roots: AdminCategory[] = []
  for (const c of categories) {
    if (c.parent_id) {
      const key = c.parent_id
      if (!childrenByParent[key]) childrenByParent[key] = []
      childrenByParent[key].push(c)
    } else {
      roots.push(c)
    }
  }
  roots.sort((a, b) => a.name.localeCompare(b.name))
  for (const key of Object.keys(childrenByParent)) {
    childrenByParent[key].sort((a, b) => a.name.localeCompare(b.name))
  }
  return { roots, childrenByParent }
}

export default function CategoriesGLPage() {
  const { t } = useLanguage()
  const [categories, setCategories] = useState<AdminCategory[]>([])
  const [glAccounts, setGLAccounts] = useState<AdminGLAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [formMode, setFormMode] = useState<FormMode>('none')
  const [categorySearch, setCategorySearch] = useState('')
  const [glSearch, setGlSearch] = useState('')
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)
  const [suggestTry, setSuggestTry] = useState({ merchant_name: '', description: '', amount: '' })
  const [suggestLoading, setSuggestLoading] = useState(false)
  const [suggestResult, setSuggestResult] = useState<{ name: string; confidence: number; reasoning: string | null } | null>(null)
  const [glModalOpen, setGlModalOpen] = useState(false)
  const [glForm, setGlForm] = useState({ account_code: '', account_name: '', account_type: 'expense', description: '' })
  const [glSaving, setGlSaving] = useState(false)

  const [formData, setFormData] = useState({
    name: '',
    code: '',
    description: '',
    gl_account_id: '' as string | null,
    parent_id: '' as string | null,
    is_active: true,
  })

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [cats, gls] = await Promise.all([
        adminAPI.listCategories(),
        adminAPI.listGLAccounts(),
      ])
      setCategories(cats)
      setGLAccounts(gls)
      if (cats.length > 0 && expanded.size === 0) {
        setExpanded(new Set(cats.filter((c) => !c.parent_id).map((c) => c.id)))
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load categories and GL accounts')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const { roots, childrenByParent } = useMemo(() => buildTree(categories), [categories])

  const filterCategories = (list: AdminCategory[], search: string): AdminCategory[] => {
    if (!search.trim()) return list
    const q = search.trim().toLowerCase()
    return list.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.code.toLowerCase().includes(q) ||
        (c.description || '').toLowerCase().includes(q)
    )
  }

  const filteredRoots = useMemo(() => filterCategories(roots, categorySearch), [roots, categorySearch])

  const selectedCategory = selectedId ? categories.find((c) => c.id === selectedId) : null
  const activeCount = categories.filter((c) => c.is_active).length

  const toggle = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const expandAll = () => setExpanded(new Set(categories.map((c) => c.id)))
  const collapseAll = () => setExpanded(new Set())

  const openCreate = (parentId?: string | null) => {
    setFormData({
      name: '',
      code: '',
      description: '',
      gl_account_id: null,
      parent_id: parentId || null,
      is_active: true,
    })
    setFormMode('create')
    setSelectedId(null)
  }

  const openEdit = (cat: AdminCategory) => {
    setSelectedId(cat.id)
    setFormData({
      name: cat.name,
      code: cat.code ?? '',
      description: cat.description || '',
      gl_account_id: cat.gl_account_id || null,
      parent_id: cat.parent_id || null,
      is_active: cat.is_active,
    })
    setFormMode('edit')
  }

  const cancelForm = () => {
    setFormMode('none')
    if (selectedId) setFormData({
      name: selectedCategory?.name ?? '',
      code: selectedCategory?.code ?? '',
      description: selectedCategory?.description ?? '',
      gl_account_id: selectedCategory?.gl_account_id ?? null,
      parent_id: selectedCategory?.parent_id ?? null,
      is_active: selectedCategory?.is_active ?? true,
    })
  }

  const handleSaveCreate = async () => {
    const name = formData.name.trim().toLowerCase()
    if (!name) {
      setError('Name is required')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const created = await adminAPI.createCategory({
        name,
        code: name,
        description: formData.description.trim() || undefined,
        gl_account_id: formData.gl_account_id || undefined,
        parent_id: formData.parent_id || undefined,
      })
      setCategories((prev) => [...prev, created])
      setFormMode('none')
      setSelectedId(created.id)
      setFormData({ name: '', code: '', description: '', gl_account_id: null, parent_id: null, is_active: true })
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to create category')
    } finally {
      setSaving(false)
    }
  }

  const handleSaveEdit = async () => {
    const name = formData.name.trim().toLowerCase()
    if (!selectedId || !name) return
    setSaving(true)
    setError(null)
    try {
      const updated = await adminAPI.updateCategory(selectedId, {
        name,
        code: name,
        description: formData.description.trim() || null,
        gl_account_id: formData.gl_account_id || null,
        parent_id: formData.parent_id || null,
        is_active: formData.is_active,
      })
      setCategories((prev) => prev.map((c) => (c.id === selectedId ? updated : c)))
      setFormMode('none')
      setSelectedId(updated.id)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to update category')
    } finally {
      setSaving(false)
    }
  }

  const handleTrySuggest = async () => {
    setSuggestLoading(true)
    setSuggestResult(null)
    try {
      const res = await adminAPI.suggestCategory({
        merchant_name: suggestTry.merchant_name || null,
        description: suggestTry.description || null,
        amount: suggestTry.amount ? parseFloat(suggestTry.amount) : null,
      })
      if (res.suggested_category) {
        setSuggestResult({
          name: res.suggested_category.name,
          confidence: res.confidence,
          reasoning: res.reasoning ?? null,
        })
      } else {
        setSuggestResult({ name: '—', confidence: 0, reasoning: 'No suggestion.' })
      }
    } catch {
      setSuggestResult({ name: '—', confidence: 0, reasoning: 'Request failed.' })
    } finally {
      setSuggestLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    setDeleting(true)
    setError(null)
    try {
      await adminAPI.deleteCategory(id)
      setCategories((prev) => prev.filter((c) => c.id !== id))
      if (selectedId === id) {
        setSelectedId(null)
        setFormMode('none')
      }
      setConfirmDeleteId(null)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to delete category')
    } finally {
      setDeleting(false)
    }
  }

  const filteredGL = useMemo(() => {
    if (!glSearch.trim()) return glAccounts
    const q = glSearch.trim().toLowerCase()
    return glAccounts.filter(
      (a) =>
        a.account_code.toLowerCase().includes(q) ||
        a.account_name.toLowerCase().includes(q) ||
        (a.description || '').toLowerCase().includes(q)
    )
  }, [glAccounts, glSearch])

  const renderTreeItem = (cat: AdminCategory, depth = 0) => {
    const children = childrenByParent[cat.id] || []
    const isExp = expanded.has(cat.id)
    const isSel = selectedId === cat.id
    return (
      <div key={cat.id} style={{ marginLeft: depth ? 20 : 0 }}>
        <div
          role="button"
          tabIndex={0}
          onClick={() => {
            setSelectedId(cat.id)
            setFormMode('edit')
            setFormData({
              name: cat.name,
              code: cat.code,
              description: cat.description || '',
              gl_account_id: cat.gl_account_id || null,
              parent_id: cat.parent_id || null,
              is_active: cat.is_active,
            })
          }}
          onKeyDown={(e) => e.key === 'Enter' && setSelectedId(cat.id)}
          className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all hover:bg-gray-50 ${isSel ? 'bg-indigo-50 border-l-[3px] border-l-primary' : ''}`}
        >
          <div className="flex items-center space-x-3 min-w-0">
            <button
              type="button"
              className="w-5 h-5 flex-shrink-0 flex items-center justify-center text-textMuted hover:text-textPrimary"
              onClick={(e) => {
                e.stopPropagation()
                toggle(cat.id)
              }}
            >
              {children.length > 0 ? (
                <FontAwesomeIcon icon={isExp ? faChevronDown : faChevronRight} className="text-xs" />
              ) : (
                <span className="w-5 inline-block" />
              )}
            </button>
            <FontAwesomeIcon icon={faFolder} className="text-primary flex-shrink-0" />
            <div className="min-w-0">
              <div className="text-sm font-medium text-textPrimary truncate">{cat.name}</div>
              {children.length > 0 && (
                <div className="text-xs text-textMuted">{children.length} sub</div>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span
              className={`text-xs font-medium px-2 py-1 rounded-full ${cat.is_active ? 'text-successGreen bg-green-50' : 'text-textMuted bg-gray-100'}`}
            >
              {cat.is_active ? 'Active' : 'Inactive'}
            </span>
            <button
              type="button"
              title={t('categories.addSubcategory') || 'Add subcategory'}
              onClick={(e) => {
                e.stopPropagation()
                openCreate(cat.id)
              }}
              className="w-7 h-7 flex items-center justify-center rounded text-textMuted hover:bg-indigo-100 hover:text-primary"
            >
              <FontAwesomeIcon icon={faPlus} className="text-xs" />
            </button>
          </div>
        </div>
        {isExp && children.length > 0 && (
          <div className="mt-1 space-y-0">
            {children.map((ch) => renderTreeItem(ch, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="min-w-0 w-full max-w-full">
      <section className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">
              {t('categories.title') || 'Categories & GL Account Management'}
            </h1>
            <p className="text-textSecondary">
              {t('categories.subtitle') || 'Manage expense categories and general ledger account mappings'}
            </p>
          </div>
          <button
            type="button"
            onClick={() => openCreate(null)}
            className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2"
          >
            <FontAwesomeIcon icon={faPlus} />
            <span>{t('categories.newCategory') || 'New Category'}</span>
          </button>
        </div>

        {error && (
          <div className="mb-4 p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm flex items-center justify-between">
            <span>{error}</span>
            <button type="button" onClick={() => setError(null)} className="text-red-600 hover:text-red-800">
              <FontAwesomeIcon icon={faTimes} />
            </button>
          </div>
        )}

        <div className="grid grid-cols-4 gap-4">
          <div className="bg-surface rounded-xl p-5 border border-borderColor">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-textSecondary">{t('categories.totalCategories') || 'Total Categories'}</span>
              <div className="w-10 h-10 bg-indigo-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faFolderTree} className="text-primary" />
              </div>
            </div>
            <div className="text-2xl font-bold text-textPrimary">{categories.length}</div>
            <div className="text-xs text-textMuted mt-1">
              {roots.length} root, {categories.length - roots.length} child
            </div>
          </div>
          <div className="bg-surface rounded-xl p-5 border border-borderColor">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-textSecondary">{t('categories.glAccounts') || 'GL Accounts'}</span>
              <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faCalculator} className="text-successGreen" />
              </div>
            </div>
            <div className="text-2xl font-bold text-textPrimary">{glAccounts.length}</div>
            <div className="text-xs text-textMuted mt-1">Available for mapping</div>
          </div>
          <div className="bg-surface rounded-xl p-5 border border-borderColor">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-textSecondary">{t('categories.activeCategories') || 'Active Categories'}</span>
              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faCheckCircle} className="text-infoBlue" />
              </div>
            </div>
            <div className="text-2xl font-bold text-textPrimary">{activeCount}</div>
            <div className="text-xs text-textMuted mt-1">{categories.length - activeCount} inactive</div>
          </div>
          <div className="bg-surface rounded-xl p-5 border border-borderColor">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-textSecondary">{t('categories.categoryTree') || 'Category Tree'}</span>
              <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center">
                <FontAwesomeIcon icon={faFolder} className="text-purple-600" />
              </div>
            </div>
            <div className="text-2xl font-bold text-textPrimary">{roots.length}</div>
            <div className="text-xs text-textMuted mt-1">Root categories</div>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-12 gap-6 min-w-0">
        <section className="col-span-5 min-w-0 bg-surface rounded-xl border border-borderColor">
          <div className="p-6 border-b border-borderColor">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-textPrimary">{t('categories.categoryTree') || 'Category Tree'}</h2>
              <div className="flex items-center space-x-2">
                <button type="button" className="w-8 h-8 flex items-center justify-center text-textSecondary hover:text-textPrimary hover:bg-gray-50 rounded-lg" title="Expand All" onClick={expandAll}>
                  <FontAwesomeIcon icon={faChevronDown} />
                </button>
                <button type="button" className="w-8 h-8 flex items-center justify-center text-textSecondary hover:text-textPrimary hover:bg-gray-50 rounded-lg" title="Collapse All" onClick={collapseAll}>
                  <FontAwesomeIcon icon={faChevronRight} />
                </button>
              </div>
            </div>
            <div className="relative">
              <FontAwesomeIcon icon={faSearch} className="absolute left-3 top-1/2 -translate-y-1/2 text-textMuted" />
              <input
                type="text"
                placeholder={t('categories.searchCategories') || 'Search categories...'}
                value={categorySearch}
                onChange={(e) => setCategorySearch(e.target.value)}
                className="w-full h-10 pl-10 pr-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          </div>

          <div className="p-4 overflow-y-auto max-h-[calc(100vh-400px)]">
            {loading ? (
              <p className="text-textSecondary text-sm">Loading...</p>
            ) : (
              <div className="space-y-1">
                {filteredRoots.length === 0 ? (
                  <p className="text-textMuted text-sm py-4">
                    {categorySearch ? 'No categories match your search.' : 'No categories yet. Create one to get started.'}
                  </p>
                ) : (
                  filteredRoots.map((root) => renderTreeItem(root))
                )}
              </div>
            )}
          </div>
        </section>

        <section className="col-span-7 min-w-0 bg-surface rounded-xl border border-borderColor overflow-hidden">
          <div className="p-6 border-b border-borderColor">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center">
                  <FontAwesomeIcon icon={faFolder} className="text-primary text-xl" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-textPrimary">
                    {formMode === 'create' ? (t('categories.newCategory') || 'New Category') : selectedCategory ? selectedCategory.name : '—'}
                  </h2>
                  <p className="text-sm text-textSecondary">
                    {formMode === 'create'
                      ? 'Add a new expense category'
                      : selectedCategory
                        ? selectedCategory.name
                        : (t('categories.selectCategory') || 'Select a category from the tree')}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {formMode !== 'none' && (
                  <>
                    <button type="button" onClick={cancelForm} className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50">
                      {t('common.cancel') || 'Cancel'}
                    </button>
                    <button
                      type="button"
                      onClick={formMode === 'create' ? handleSaveCreate : handleSaveEdit}
                      disabled={saving || !formData.name.trim()}
                      className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2 disabled:opacity-50"
                    >
                      <FontAwesomeIcon icon={faSave} />
                      <span>{saving ? 'Saving...' : (t('categories.saveChanges') || 'Save Changes')}</span>
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="p-6 overflow-y-auto max-h-[calc(100vh-400px)]">
            {(formMode !== 'none' || selectedCategory) ? (
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-2">Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData((f) => ({ ...f, name: e.target.value }))}
                    placeholder="e.g. meals"
                    className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-2" htmlFor="parent-category-select">{t('categories.parentCategory') || 'Parent Category'}</label>
                  <select
                    id="parent-category-select"
                    value={formData.parent_id ?? ''}
                    onChange={(e) => {
                      const v = e.target.value
                      setFormData((f) => ({ ...f, parent_id: v === '' ? null : v }))
                    }}
                    className="w-full min-h-[2.5rem] px-3 py-2 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white text-textPrimary"
                  >
                    <option value="">{t('categories.noneRoot') || 'None (Root Level)'}</option>
                    {categories
                      .filter((c) => c.id !== selectedId)
                      .map((c) => (
                        <option key={c.id} value={String(c.id)}>
                          {c.parent_id ? `  ${c.name}` : c.name}
                        </option>
                      ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-2" htmlFor="gl-account-select">{t('categories.glMapping') || 'GL Account Mapping'}</label>
                  <select
                    id="gl-account-select"
                    value={formData.gl_account_id ?? ''}
                    onChange={(e) => {
                      const v = e.target.value
                      setFormData((f) => ({ ...f, gl_account_id: v === '' ? null : v }))
                    }}
                    className="w-full min-h-[2.5rem] px-3 py-2 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white text-textPrimary"
                  >
                    <option value="">No GL account</option>
                    {glAccounts.map((a) => (
                      <option key={a.id} value={String(a.id)}>
                        {a.account_code} - {a.account_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-2">Description (optional)</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData((f) => ({ ...f, description: e.target.value }))}
                    rows={2}
                    className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <div className="text-sm font-medium text-textPrimary">{t('categories.activeCategory') || 'Active Category'}</div>
                    <div className="text-xs text-textSecondary">Enable this category for expense submissions</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData((f) => ({ ...f, is_active: e.target.checked }))}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary" />
                  </label>
                </div>

                {formMode === 'edit' && selectedId && (
                  <div className="border-t border-borderColor pt-6 flex items-center justify-between">
                    {confirmDeleteId === selectedId ? (
                      <div className="flex items-center space-x-3">
                        <span className="text-sm text-textSecondary">Delete this category?</span>
                        <button
                          type="button"
                          onClick={() => handleDelete(selectedId)}
                          disabled={deleting}
                          className="h-10 px-4 bg-errorRed hover:bg-red-700 text-white rounded-lg text-sm font-medium"
                        >
                          {deleting ? 'Deleting...' : 'Yes, delete'}
                        </button>
                        <button type="button" onClick={() => setConfirmDeleteId(null)} className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50">
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={() => setConfirmDeleteId(selectedId)}
                        className="h-10 px-4 border border-errorRed text-errorRed hover:bg-red-50 rounded-lg text-sm font-medium flex items-center space-x-2"
                      >
                        <FontAwesomeIcon icon={faTrash} />
                        <span>{t('categories.deleteCategory') || 'Delete Category'}</span>
                      </button>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-textMuted">
                <FontAwesomeIcon icon={faFolder} className="text-4xl mb-4 opacity-50" />
                <p className="text-sm">{t('categories.selectCategory') || 'Select a category from the tree or create a new one'}</p>
              </div>
            )}
          </div>
        </section>
      </div>

      <section className="mt-8 bg-surface rounded-xl border border-borderColor">
        <div className="p-6 border-b border-borderColor">
          <h2 className="text-xl font-semibold text-textPrimary mb-1">Try category suggestion</h2>
          <p className="text-sm text-textSecondary mb-4">Rule-based and semantic suggestion (PRD). Enter sample merchant, description, or amount.</p>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <input
              type="text"
              placeholder="Merchant name"
              value={suggestTry.merchant_name}
              onChange={(e) => setSuggestTry((s) => ({ ...s, merchant_name: e.target.value }))}
              className="h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <input
              type="text"
              placeholder="Description"
              value={suggestTry.description}
              onChange={(e) => setSuggestTry((s) => ({ ...s, description: e.target.value }))}
              className="h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <input
              type="number"
              step="0.01"
              placeholder="Amount (optional)"
              value={suggestTry.amount}
              onChange={(e) => setSuggestTry((s) => ({ ...s, amount: e.target.value }))}
              className="h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <button
              type="button"
              onClick={handleTrySuggest}
              disabled={suggestLoading}
              className="h-10 px-4 rounded-lg border border-primary bg-indigo-50 text-primary text-sm font-medium hover:bg-indigo-100 flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {suggestLoading ? <FontAwesomeIcon icon={faSpinner} className="animate-spin" /> : <FontAwesomeIcon icon={faRobot} />}
              <span>Suggest</span>
            </button>
          </div>
          {suggestResult && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-borderColor">
              <div className="text-sm font-medium text-textPrimary">Suggested: {suggestResult.name}</div>
              <div className="text-xs text-textMuted mt-1">Confidence: {(suggestResult.confidence * 100).toFixed(0)}%</div>
              {suggestResult.reasoning && <div className="text-xs text-textSecondary mt-1">{suggestResult.reasoning}</div>}
            </div>
          )}
        </div>
      </section>

      <section className="mt-8 bg-surface rounded-xl border border-borderColor">
        <div className="p-6 border-b border-borderColor">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-textPrimary mb-1">{t('categories.glIntegration') || 'GL Account Integration'}</h2>
              <p className="text-sm text-textSecondary">{t('categories.glIntegrationDesc') || 'General ledger accounts available for category mapping'}</p>
            </div>
            <button
              type="button"
              onClick={() => setGlModalOpen(true)}
              className="h-10 px-4 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium flex items-center space-x-2"
            >
              <FontAwesomeIcon icon={faPlus} />
              <span>Add GL account</span>
            </button>
          </div>
          <div className="flex items-center space-x-3 flex-wrap gap-2">
            <div className="flex-1 min-w-[200px] relative">
              <FontAwesomeIcon icon={faSearch} className="absolute left-3 top-1/2 -translate-y-1/2 text-textMuted" />
              <input
                type="text"
                placeholder={t('categories.searchGL') || 'Search GL accounts...'}
                value={glSearch}
                onChange={(e) => setGlSearch(e.target.value)}
                className="w-full h-10 pl-10 pr-4 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr className="border-b border-borderColor">
                <th className="text-left py-3 px-6 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('categories.accountCode') || 'Account Code'}</th>
                <th className="text-left py-3 px-6 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('categories.accountName') || 'Account Name'}</th>
                <th className="text-left py-3 px-6 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('categories.accountType') || 'Account Type'}</th>
                <th className="text-center py-3 px-6 text-xs font-semibold text-textMuted uppercase tracking-wide">{t('categories.mappedCategories') || 'Mapped'}</th>
              </tr>
            </thead>
            <tbody>
              {filteredGL.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-textMuted text-sm">
                    {loading ? 'Loading...' : glAccounts.length === 0 ? 'No GL accounts. Create them via admin or import from ERP.' : 'No accounts match your search.'}
                  </td>
                </tr>
              ) : (
                filteredGL.map((row) => {
                  const mappedCount = categories.filter((c) => c.gl_account_id === row.id).length
                  return (
                    <tr key={row.id} className="border-b border-borderColor hover:bg-gray-50 h-14">
                      <td className="py-3 px-6 text-sm font-medium text-textPrimary">{row.account_code}</td>
                      <td className="py-3 px-6 text-sm text-textPrimary">{row.account_name}</td>
                      <td className="py-3 px-6">
                        <span className="inline-flex items-center text-xs font-medium text-purple-600 bg-purple-50 px-2 py-1 rounded-full">{row.account_type}</span>
                      </td>
                      <td className="py-3 px-6 text-center">
                        <span className={`text-sm font-medium ${mappedCount === 0 ? 'text-warningAmber' : 'text-textPrimary'}`}>{mappedCount}</span>
                        <span className="text-xs text-textMuted ml-1">categories</span>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between p-6 border-t border-borderColor">
          <div className="text-sm text-textSecondary">
            {t('categories.showingGL') || 'Showing'} {filteredGL.length} of {glAccounts.length} GL accounts
          </div>
        </div>
      </section>

      {glModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true" aria-labelledby="gl-modal-title">
          <div className="bg-surface rounded-xl border border-borderColor shadow-xl w-full max-w-md mx-4 p-6">
            <h2 id="gl-modal-title" className="text-lg font-semibold text-textPrimary mb-4">Add GL account</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-textPrimary mb-1">Account code</label>
                <input
                  type="text"
                  value={glForm.account_code}
                  onChange={(e) => setGlForm((f) => ({ ...f, account_code: e.target.value }))}
                  placeholder="e.g. 6001"
                  className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-textPrimary mb-1">Account name</label>
                <input
                  type="text"
                  value={glForm.account_name}
                  onChange={(e) => setGlForm((f) => ({ ...f, account_name: e.target.value }))}
                  placeholder="e.g. Travel expenses"
                  className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-textPrimary mb-1">Account type</label>
                <select
                  value={glForm.account_type}
                  onChange={(e) => setGlForm((f) => ({ ...f, account_type: e.target.value }))}
                  className="w-full min-h-[2.5rem] px-3 py-2 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
                >
                  <option value="expense">Expense</option>
                  <option value="asset">Asset</option>
                  <option value="liability">Liability</option>
                  <option value="equity">Equity</option>
                  <option value="revenue">Revenue</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-textPrimary mb-1">Description (optional)</label>
                <input
                  type="text"
                  value={glForm.description}
                  onChange={(e) => setGlForm((f) => ({ ...f, description: e.target.value }))}
                  className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button type="button" onClick={() => setGlModalOpen(false)} className="h-10 px-4 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50">
                Cancel
              </button>
              <button
                type="button"
                disabled={!glForm.account_code.trim() || !glForm.account_name.trim() || glSaving}
                onClick={async () => {
                  setGlSaving(true)
                  setError(null)
                  try {
                    await adminAPI.createGLAccount({
                      account_code: glForm.account_code.trim(),
                      account_name: glForm.account_name.trim(),
                      account_type: glForm.account_type,
                      description: glForm.description.trim() || undefined,
                    })
                    await loadData()
                    setGlModalOpen(false)
                    setGlForm({ account_code: '', account_name: '', account_type: 'expense', description: '' })
                  } catch (e: unknown) {
                    setError(e instanceof Error ? e.message : 'Failed to create GL account')
                  } finally {
                    setGlSaving(false)
                  }
                }}
                className="h-10 px-4 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {glSaving ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
