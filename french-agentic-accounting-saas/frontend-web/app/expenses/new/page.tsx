'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faCloudUploadAlt,
  faCamera,
  faSpinner,
  faCheck,
  faRobot,
  faSave,
  faFolderPlus,
  faPaperPlane,
  faTimes,
  faInfo,
  faExclamation,
  faChevronDown,
  faUpload,
  faExclamationTriangle,
} from '@fortawesome/free-solid-svg-icons'
import { fileAPI, expensesAPI, reportAPI, adminAPI, getAuthErrorMessage } from '@/lib/api'
import type { AdminCategory } from '@/lib/api'
import type { ReceiptAPIResponse, ReceiptExtractionFromAPI, ReceiptOcrFromAPI } from '@/types/receipt'

type UploadState = 'empty' | 'processing' | 'success'

type LineItem = {
  description?: string
  quantity?: number
  unit_price?: number
  amount?: number
  vat_rate?: number
}

type ExpenseFormState = {
  merchant_name: string
  expense_date: string
  amount: string
  vat_amount: string
  vat_rate: string
  category: string
  description: string
  currency: string
  subtotal?: string
  invoice_number?: string
  payment_method?: string
  merchant_address?: string
  merchant_vat_number?: string
  line_items?: LineItem[]
}

/** Format value for date input (YYYY-MM-DD). Backend may return ISO string or date. */
function toDateInputValue(value: string | number | null | undefined): string {
  if (value == null) return ''
  const s = String(value).trim()
  if (!s) return ''
  const match = s.match(/^(\d{4}-\d{2}-\d{2})/)
  return match ? match[1]! : s
}

/**
 * Merge extraction (primary) and ocr (fallback). Use extraction field when not null/undefined, else ocr, else default.
 * Ensures form gets all values even when extraction returns nulls.
 */
function mergeExtractionToFormState(
  extraction: ReceiptExtractionFromAPI | null | undefined,
  ocr: ReceiptOcrFromAPI | null | undefined
): Partial<ExpenseFormState> {
  const e = extraction ?? {}
  const o = ocr ?? {}
  const str = (v: unknown, d = '') =>
    v != null && String(v).trim() !== '' ? String(v).trim() : d
  const num = (v: unknown) =>
    v != null && !Number.isNaN(Number(v)) ? String(v) : ''

  const currencyVal = str(e.currency, str(o.currency, 'EUR'))
  return {
    merchant_name: str(e.merchant_name, str(o.merchant_name, '')),
    expense_date: toDateInputValue(e.expense_date ?? o.expense_date),
    amount: num(e.total_amount ?? o.total_amount),
    vat_amount: num(e.vat_amount ?? o.vat_amount),
    vat_rate: num(e.vat_rate ?? o.vat_rate),
    category: str(e.category, str(o.category, '')),
    description: str(e.description, str(o.description, '')),
    currency: currencyVal || 'EUR',
    subtotal: e.subtotal != null ? String(e.subtotal) : o.total_amount != null ? String(o.total_amount) : '',
    invoice_number: str(e.invoice_number, ''),
    payment_method: str(e.payment_method, ''),
    merchant_address: str(e.merchant_address, ''),
    merchant_vat_number: (e as Record<string, unknown>).merchant_vat_number != null
      ? String((e as Record<string, unknown>).merchant_vat_number)
      : '',
    line_items: Array.isArray(e.line_items) && e.line_items.length > 0
      ? e.line_items.map((item) => ({
          description: item?.description ?? (item as { name?: string }).name ?? '',
          quantity: item?.quantity,
          unit_price: item?.unit_price ?? item?.price,
          amount: item?.amount ?? item?.price,
          vat_rate: item?.vat_rate,
        }))
      : undefined,
  }
}

/** Build form state from receipt API response (upload or GET receipt). Uses meta_data.extraction + meta_data.ocr fallback. */
function formStateFromReceiptResponse(receipt: ReceiptAPIResponse | Record<string, unknown>): Partial<ExpenseFormState> {
  // Handle both meta_data (snake_case) and metaData (camelCase)
  const meta = (receipt as ReceiptAPIResponse).meta_data ?? (receipt as Record<string, unknown>).metaData ?? {}
  const metaObj = meta && typeof meta === 'object' ? meta as Record<string, unknown> : {}
  const extraction = (metaObj.extraction ?? null) as ReceiptExtractionFromAPI | null
  const ocr = (metaObj.ocr ?? (receipt as ReceiptAPIResponse).extracted_data ?? null) as ReceiptOcrFromAPI | null
  return mergeExtractionToFormState(extraction, ocr)
}

export default function NewExpensePage() {
  const router = useRouter()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadState, setUploadState] = useState<UploadState>('empty')
  const [isDragging, setIsDragging] = useState(false)
  const [processingProgress, setProcessingProgress] = useState(0)
  const [error, setError] = useState('')
  const [ocrWarning, setOcrWarning] = useState<string | null>(null)
  const uploadInProgressRef = useRef(false)
  const [receiptId, setReceiptId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [categories, setCategories] = useState<AdminCategory[]>([])
  const [categoriesLoading, setCategoriesLoading] = useState(true)
  const [suggestCategoryLoading, setSuggestCategoryLoading] = useState(false)
  const [suggestionReasoning, setSuggestionReasoning] = useState<string | null>(null)
  const [formData, setFormData] = useState<ExpenseFormState>({
    merchant_name: '',
    expense_date: '',
    amount: '',
    vat_amount: '',
    vat_rate: '',
    category: '',
    description: '',
    currency: 'EUR',
  })

  // Load categories for dropdown (tenant categories; used for suggestion and list)
  useEffect(() => {
    let cancelled = false
    adminAPI.listCategories().then((list) => {
      if (!cancelled) setCategories(list)
    }).catch(() => { if (!cancelled) setCategories([]) }).finally(() => { if (!cancelled) setCategoriesLoading(false) })
    return () => { cancelled = true }
  }, [])

  // When upload succeeds, fetch receipt and populate form (handles any delay/race)
  useEffect(() => {
    if (uploadState !== 'success' || !receiptId) return
    let cancelled = false
    fileAPI
      .getReceipt(receiptId)
      .then((res: unknown) => {
        if (cancelled) return
        const receipt = (typeof res === 'object' && res !== null && 'data' in res)
          ? (res as { data: Record<string, unknown> }).data
          : res
        const raw = receipt as ReceiptAPIResponse | Record<string, unknown>
        const meta = raw?.meta_data ?? (raw as Record<string, unknown>)?.metaData
        if (meta && typeof meta === 'object' && ((meta as Record<string, unknown>).extraction || (meta as Record<string, unknown>).ocr)) {
          const merged = formStateFromReceiptResponse(raw)
          setFormData((prev) => ({ ...prev, ...merged }))
          if (!merged.category && (merged.merchant_name || merged.description)) {
            adminAPI.suggestCategory({
              merchant_name: merged.merchant_name || null,
              description: merged.description || null,
              amount: merged.amount ? parseFloat(merged.amount) : null,
            }).then((res) => {
              if (res.suggested_category) {
                setFormData((prev) => ({ ...prev, category: res.suggested_category!.name }))
                setSuggestionReasoning(res.reasoning ?? null)
              }
            }).catch(() => {})
          }
        }
      })
      .catch(() => { /* ignore - we already populated in handleFileUpload */ })
    return () => { cancelled = true }
  }, [uploadState, receiptId])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    void handleFileUpload(e.dataTransfer.files)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      void handleFileUpload(e.target.files)
    }
  }

  const handleFileUpload = async (files: FileList) => {
    const file = files[0]
    if (!file) return
    if (uploadInProgressRef.current) return
    uploadInProgressRef.current = true

    // Frontend validation: type and size
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/heic', 'application/pdf']
    if (!allowedTypes.includes(file.type)) {
      uploadInProgressRef.current = false
      setError('Invalid file type. Please upload JPG, PNG, HEIC, or PDF files.')
      return
    }

    const maxSize = 10 * 1024 * 1024 // 10MB
    if (file.size > maxSize) {
      uploadInProgressRef.current = false
      setError('File size exceeds 10MB limit. Please upload a smaller file.')
      return
    }

    setError('')
    setOcrWarning(null)
    setReceiptId(null)
    setFormData({
      merchant_name: '',
      expense_date: '',
      amount: '',
      vat_amount: '',
      vat_rate: '',
      category: '',
      description: '',
      currency: 'EUR',
      subtotal: '',
      invoice_number: '',
      payment_method: '',
      merchant_address: '',
      merchant_vat_number: '',
    })
    setUploadState('processing')
    setProcessingProgress(10)

    // Simple fake progress to keep UI responsive while backend OCR runs
    let current = 10
    const interval = setInterval(() => {
      current = Math.min(current + 5, 95)
      setProcessingProgress(current)
      if (current >= 95) {
        clearInterval(interval)
      }
    }, 400)

    try {
      // 1. Upload receipt (this triggers backend OCR pipeline)
      const uploadRes = await fileAPI.upload(file) as ReceiptAPIResponse & { receipt_id?: string; id?: string; data?: { receipt_id?: string; id?: string } }
      const rid =
        uploadRes.receipt_id ||
        uploadRes.id ||
        uploadRes.data?.receipt_id ||
        uploadRes.data?.id

      if (!rid) {
        throw new Error('Upload succeeded but no receipt ID was returned.')
      }

      setReceiptId(rid)

      // If upload response already has status === 'completed' and meta_data, pre-fill form once
      if (uploadRes.status === 'completed' && uploadRes.meta_data && (uploadRes.meta_data.extraction || uploadRes.meta_data.ocr)) {
        const merged = formStateFromReceiptResponse(uploadRes)
        setFormData((prev) => ({ ...prev, ...merged }))
      }

      // 2. Poll OCR status
      const maxAttempts = 20
      let ocrCompleted = false
      let ocrFailed = false
      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        const statusRes = await fileAPI.getReceiptStatus(rid) as { ocr_status?: string }
        if (statusRes.ocr_status === 'completed') {
          ocrCompleted = true
          break
        }
        if (statusRes.ocr_status === 'failed') {
          ocrFailed = true
          setOcrWarning(
            'OCR could not read this receipt (e.g. Tesseract is not installed or not in your PATH). You can still enter the details manually below.'
          )
          break
        }
        await new Promise((resolve) => setTimeout(resolve, 1000))
      }

      if (!ocrCompleted && !ocrFailed) {
        throw new Error('OCR is taking longer than expected. Please try again in a moment.')
      }

      // 3. Load full receipt and populate form from meta_data.extraction + meta_data.ocr (with fallback)
      const receipt = (await fileAPI.getReceipt(rid)) as ReceiptAPIResponse
      const merged = formStateFromReceiptResponse(receipt)
      setFormData((prev) => ({ ...prev, ...merged }))

      // Show OCR warning if backend reported a pipeline/OCR error
      const pipelineError = receipt.meta_data?.pipeline_error
      if (pipelineError && !ocrWarning) {
        setOcrWarning(
          pipelineError.includes('tesseract') || pipelineError.toLowerCase().includes('path')
            ? 'OCR failed: Tesseract is not installed or not in your PATH. Extracted data may be incomplete.'
            : `OCR warning: ${pipelineError}`
        )
      }

      clearInterval(interval)
      setProcessingProgress(100)
      setError('')
      uploadInProgressRef.current = false
      setUploadState('success')
    } catch (err: any) {
      uploadInProgressRef.current = false
      clearInterval(interval)
      setUploadState('empty')
      setProcessingProgress(0)
      setReceiptId(null)
      setFormData({
        merchant_name: '',
        expense_date: '',
        amount: '',
        vat_amount: '',
        vat_rate: '',
        category: '',
        description: '',
        currency: 'EUR',
        subtotal: '',
        invoice_number: '',
        payment_method: '',
        merchant_address: '',
        merchant_vat_number: '',
      })
      const rawMessage = err?.response?.data?.detail ?? err?.message ?? ''
      const isOcrError =
        typeof rawMessage === 'string' &&
        (rawMessage.toLowerCase().includes('tesseract') || rawMessage.toLowerCase().includes('ocr') || rawMessage.toLowerCase().includes('path'))
      if (isOcrError) {
        setOcrWarning(
          'OCR is not available (e.g. Tesseract is not installed or not in your PATH). You can still create an expense by entering the details manually.'
        )
      }
      const message =
        rawMessage === 'Network Error'
          ? 'Could not connect to the server. Ensure the file service is running on port 8005 and try again.'
          : String(rawMessage) || 'Failed to process receipt. Please try again.'
      setError(message)
    }
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleSuggestCategory = async () => {
    setSuggestCategoryLoading(true)
    setSuggestionReasoning(null)
    try {
      const amount = formData.amount ? parseFloat(formData.amount) : undefined
      const res = await adminAPI.suggestCategory({
        merchant_name: formData.merchant_name || null,
        description: formData.description || null,
        amount: amount ?? null,
      })
      if (res.suggested_category) {
        setFormData((prev) => ({ ...prev, category: res.suggested_category!.name }))
        setSuggestionReasoning(res.reasoning ?? null)
      } else {
        setSuggestionReasoning('No suggestion (add merchant or description).')
      }
    } catch {
      setSuggestionReasoning('Suggestion failed.')
    } finally {
      setSuggestCategoryLoading(false)
    }
  }

  const buildPayload = () => {
    const payload: any = {
      amount: parseFloat(formData.amount),
      currency: formData.currency || 'EUR',
      expense_date: formData.expense_date,
      merchant_name: formData.merchant_name,
      category: formData.category || undefined,
      description: formData.description || undefined,
    }
    if (formData.vat_amount) payload.vat_amount = parseFloat(formData.vat_amount)
    if (formData.vat_rate) payload.vat_rate = parseFloat(formData.vat_rate)
    if (receiptId) payload.receipt_ids = [receiptId]
    return payload
  }

  const handleSaveDraft = async () => {
    if (!formData.merchant_name || !formData.expense_date || !formData.amount) {
      setError('Please fill in merchant, date, and total amount before saving.')
      return
    }
    setSaving(true)
    setError('')
    try {
      await expensesAPI.create(buildPayload())
      router.push('/expenses')
    } catch (err: any) {
      setError(getAuthErrorMessage(err, 'Failed to save expense.'))
    } finally {
      setSaving(false)
    }
  }

  const handleAddToReport = async () => {
    if (!formData.merchant_name || !formData.expense_date || !formData.amount) {
      setError('Please fill in merchant, date, and total amount before adding to a report.')
      return
    }

    setSaving(true)
    setError('')

    try {
      const created = await expensesAPI.create(buildPayload())
      const expenseId = created?.data?.id ?? created?.id
      if (!expenseId) {
        throw new Error('Failed to determine created expense ID.')
      }

      const now = new Date()
      const periodStart = new Date(now.getFullYear(), now.getMonth(), 1)
      const periodEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0)
      const period_start_date = periodStart.toISOString().slice(0, 10)
      const period_end_date = periodEnd.toISOString().slice(0, 10)
      const monthLabel = now.toLocaleString('default', { month: 'long', year: 'numeric' })

      const payload = {
        report_type: 'period',
        title: `Expenses ${monthLabel}`,
        description: 'Created from New Expense page.',
        period_start_date,
        period_end_date,
        period_type: 'monthly',
        expense_ids: [expenseId],
      }

      const report = await reportAPI.create(payload)
      const reportId = report?.data?.id ?? report?.id

      if (reportId) {
        router.push(`/reports/${reportId}`)
      } else {
        router.push('/reports')
      }
    } catch (err: any) {
      setError(getAuthErrorMessage(err, 'Failed to add expense to report.'))
    } finally {
      setSaving(false)
    }
  }

  const handleSubmit = async () => {
    if (!formData.merchant_name || !formData.expense_date || !formData.amount) {
      setError('Please fill in merchant, date, and total amount before submitting.')
      return
    }

    setSaving(true)
    setError('')

    try {
      const created = await expensesAPI.create(buildPayload())
      const expenseId = created?.data?.id ?? created?.id
      if (expenseId) {
        await expensesAPI.submit(String(expenseId))
      }
      router.push('/expenses')
    } catch (err: any) {
      setError(getAuthErrorMessage(err, 'Failed to submit expense.'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <section className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary mb-2">New Expense</h1>
            <p className="text-textSecondary">Upload receipt and AI will extract the details automatically</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => router.back()}
              className="h-10 px-6 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveDraft}
              disabled={saving || !formData.merchant_name || !formData.expense_date || !formData.amount}
              className="h-10 px-6 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FontAwesomeIcon icon={faSave} />
              <span>Save as Draft</span>
            </button>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <section className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-textPrimary mb-1">Receipt Upload</h2>
              <p className="text-sm text-textSecondary">Upload your receipt for automatic data extraction</p>
            </div>

            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 text-errorRed px-4 py-3 rounded text-sm">
                {error}
              </div>
            )}

            {ocrWarning && (
              <div className="mb-4 bg-amber-50 border border-warningAmber text-textPrimary px-4 py-3 rounded-xl flex items-start gap-3">
                <FontAwesomeIcon icon={faExclamationTriangle} className="text-warningAmber mt-0.5 flex-shrink-0" />
                <p className="text-sm">{ocrWarning}</p>
              </div>
            )}

            {uploadState === 'empty' && (
              <div
                className={`upload-zone border-2 border-dashed rounded-xl p-12 text-center cursor-pointer ${
                  isDragging ? 'dragging border-primary bg-E0E7FF' : 'border-borderColor hover:border-[#818CF8] hover:bg-EEF2FF'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={handleUploadClick}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/jpg,image/png,image/heic,application/pdf"
                  className="hidden"
                  onChange={handleFileSelect}
                />
                <div className="w-16 h-16 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <FontAwesomeIcon icon={faCloudUploadAlt} className="text-primary text-3xl" />
                </div>
                <h3 className="text-lg font-semibold text-textPrimary mb-2">Drop receipt here or click to upload</h3>
                <p className="text-sm text-textSecondary mb-4">Supports JPG, PNG, PDF up to 10MB</p>
                <div className="flex items-center justify-center space-x-3">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleUploadClick()
                    }}
                    className="h-10 px-6 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium"
                  >
                    Choose File
                  </button>
                  <button className="h-10 px-6 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2">
                    <FontAwesomeIcon icon={faCamera} />
                    <span>Take Photo</span>
                  </button>
                </div>
              </div>
            )}

            {uploadState === 'processing' && (
              <div className="border-2 border-primary rounded-xl p-8 bg-indigo-50">
                <div className="flex items-center space-x-4 mb-4">
                  <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center animate-spin">
                    <FontAwesomeIcon icon={faSpinner} className="text-white text-xl" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-textPrimary mb-1">Processing Receipt</h3>
                    <p className="text-sm text-textSecondary">Extracting data with AI...</p>
                  </div>
                </div>
                <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-300"
                    style={{ width: `${processingProgress}%` }}
                  ></div>
                </div>
                <p className="text-xs text-textMuted mt-2 text-center">{processingProgress}% complete</p>
              </div>
            )}

            {uploadState === 'success' && (
              <div className="border-2 border-successGreen rounded-xl p-6 bg-green-50">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-successGreen rounded-lg flex items-center justify-center flex-shrink-0">
                    <FontAwesomeIcon icon={faCheck} className="text-white text-xl" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-textPrimary mb-2">Data Extracted Successfully</h3>
                    <p className="text-sm text-textSecondary mb-4">
                      AI has extracted the following information from your receipt. Please review and confirm.
                    </p>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-white rounded-lg p-3 border border-green-200">
                        <div className="text-xs text-textMuted mb-1">Merchant</div>
                        <div className="text-sm font-medium text-textPrimary">
                          {formData.merchant_name || 'Detected merchant name'}
                        </div>
                      </div>
                      <div className="bg-white rounded-lg p-3 border border-green-200">
                        <div className="text-xs text-textMuted mb-1">Date</div>
                        <div className="text-sm font-medium text-textPrimary">
                          {formData.expense_date || 'Detected date'}
                        </div>
                      </div>
                      <div className="bg-white rounded-lg p-3 border border-green-200">
                        <div className="text-xs text-textMuted mb-1">Total Amount</div>
                        <div className="text-sm font-medium text-textPrimary">
                          {formData.amount ? `€${formData.amount}` : '—'}
                        </div>
                      </div>
                      <div className="bg-white rounded-lg p-3 border border-green-200">
                        <div className="text-xs text-textMuted mb-1">VAT Amount</div>
                        <div className="text-sm font-medium text-textPrimary">
                          {formData.vat_amount
                            ? `€${formData.vat_amount}${formData.vat_rate ? ` (${formData.vat_rate}%)` : ''}`
                            : 'Detected VAT'}
                        </div>
                      </div>
                      {formData.invoice_number && (
                        <div className="bg-white rounded-lg p-3 border border-green-200">
                          <div className="text-xs text-textMuted mb-1">Invoice #</div>
                          <div className="text-sm font-medium text-textPrimary">{formData.invoice_number}</div>
                        </div>
                      )}
                      {formData.subtotal && (
                        <div className="bg-white rounded-lg p-3 border border-green-200">
                          <div className="text-xs text-textMuted mb-1">Subtotal</div>
                          <div className="text-sm font-medium text-textPrimary">€{formData.subtotal}</div>
                        </div>
                      )}
                      {formData.payment_method && (
                        <div className="bg-white rounded-lg p-3 border border-green-200 col-span-2">
                          <div className="text-xs text-textMuted mb-1">Payment</div>
                          <div className="text-sm font-medium text-textPrimary">{formData.payment_method}</div>
                        </div>
                      )}
                      {formData.merchant_address && (
                        <div className="bg-white rounded-lg p-3 border border-green-200 col-span-2">
                          <div className="text-xs text-textMuted mb-1">Merchant Address</div>
                          <div className="text-sm font-medium text-textPrimary">{formData.merchant_address}</div>
                        </div>
                      )}
                      {formData.merchant_vat_number && (
                        <div className="bg-white rounded-lg p-3 border border-green-200">
                          <div className="text-xs text-textMuted mb-1">VAT Number</div>
                          <div className="text-sm font-medium text-textPrimary">{formData.merchant_vat_number}</div>
                        </div>
                      )}
                      {formData.description && (
                        <div className="bg-white rounded-lg p-3 border border-green-200 col-span-2">
                          <div className="text-xs text-textMuted mb-1">Description</div>
                          <div className="text-sm font-medium text-textPrimary">{formData.description}</div>
                        </div>
                      )}
                    </div>
                    {formData.line_items && formData.line_items.length > 0 && (
                      <div className="mt-4">
                        <div className="text-xs font-medium text-textMuted mb-2">Line Items</div>
                        <div className="bg-white rounded-lg border border-green-200 overflow-hidden">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="bg-gray-50 border-b border-green-200">
                                <th className="text-left py-2 px-3 font-medium text-textMuted">Description</th>
                                <th className="text-right py-2 px-3 font-medium text-textMuted">Qty</th>
                                <th className="text-right py-2 px-3 font-medium text-textMuted">Unit</th>
                                <th className="text-right py-2 px-3 font-medium text-textMuted">Amount</th>
                              </tr>
                            </thead>
                            <tbody>
                              {formData.line_items.map((item, i) => (
                                <tr key={i} className="border-b border-gray-100 last:border-0">
                                  <td className="py-2 px-3 text-textPrimary">{item.description || '-'}</td>
                                  <td className="py-2 px-3 text-right text-textSecondary">{item.quantity ?? '-'}</td>
                                  <td className="py-2 px-3 text-right text-textSecondary">
                                    {item.unit_price != null ? `€${item.unit_price}` : '-'}
                                  </td>
                                  <td className="py-2 px-3 text-right font-medium text-textPrimary">
                                    {item.amount != null ? `€${item.amount}` : '-'}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                    <button
                      onClick={() => {
                        setUploadState('empty')
                        setError('')
                        setOcrWarning(null)
                      }}
                      className="mt-4 text-sm text-primary hover:text-primaryHover font-medium flex items-center space-x-2"
                    >
                      <FontAwesomeIcon icon={faUpload} />
                      <span>Upload Different Receipt</span>
                    </button>
                  </div>
                  <div className="w-32 h-40 bg-white rounded-lg border border-borderColor overflow-hidden flex-shrink-0">
                    <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                      <FontAwesomeIcon icon={faCloudUploadAlt} className="text-4xl text-textMuted" />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </section>

          <section className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-textPrimary mb-1">Expense Details</h2>
              <p className="text-sm text-textSecondary">Review and complete the expense information</p>
            </div>

            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-2">
                    Merchant Name <span className="text-errorRed">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={formData.merchant_name}
                      onChange={(e) => setFormData({ ...formData, merchant_name: e.target.value })}
                      className="w-full h-10 px-3 pr-20 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                    <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs font-medium text-primary bg-indigo-50 px-2 py-1 rounded-full flex items-center space-x-1">
                      <FontAwesomeIcon icon={faRobot} className="text-xs" />
                      <span>AI</span>
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-2">
                    Date <span className="text-errorRed">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="date"
                      value={formData.expense_date}
                      onChange={(e) => setFormData({ ...formData, expense_date: e.target.value })}
                      className="w-full h-10 px-3 pr-20 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                    <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs font-medium text-primary bg-indigo-50 px-2 py-1 rounded-full flex items-center space-x-1">
                      <FontAwesomeIcon icon={faRobot} className="text-xs" />
                      <span>AI</span>
                    </span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-2">
                    Total Amount <span className="text-errorRed">*</span>
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-sm text-textMuted">€</span>
                    <input
                      type="number"
                      value={formData.amount}
                      onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                      step="0.01"
                      className="w-full h-10 pl-8 pr-20 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                    <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs font-medium text-primary bg-indigo-50 px-2 py-1 rounded-full flex items-center space-x-1">
                      <FontAwesomeIcon icon={faRobot} className="text-xs" />
                      <span>AI</span>
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-2">VAT Amount</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-sm text-textMuted">€</span>
                    <input
                      type="number"
                      value={formData.vat_amount}
                      onChange={(e) => setFormData({ ...formData, vat_amount: e.target.value })}
                      step="0.01"
                      className="w-full h-10 pl-8 pr-20 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                    <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs font-medium text-primary bg-indigo-50 px-2 py-1 rounded-full flex items-center space-x-1">
                      <FontAwesomeIcon icon={faRobot} className="text-xs" />
                      <span>AI</span>
                    </span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-2">
                    VAT Rate <span className="text-errorRed">*</span>
                  </label>
                  <select
                    className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    value={formData.vat_rate || ''}
                    onChange={(e) => setFormData({ ...formData, vat_rate: e.target.value })}
                  >
                    <option value="">Select VAT rate</option>
                    <option value="20">20% - Standard Rate</option>
                    <option value="10">10% - Reduced Rate (Restaurants)</option>
                    <option value="5.5">5.5% - Super Reduced Rate</option>
                    <option value="2.1">2.1% - Special Rate</option>
                    <option value="0">0% - Zero Rate</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-2">
                    Category <span className="text-errorRed">*</span>
                  </label>
                  <div className="flex items-center gap-2">
                    <div className="relative flex-1">
                      <select
                        className="w-full h-10 px-3 pr-24 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent appearance-none bg-white"
                        value={formData.category || ''}
                        onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                        disabled={categoriesLoading}
                      >
                        <option value="">Select category...</option>
                        {(categories.length ? categories : [
                          { id: '', name: 'meals' }, { id: '', name: 'travel' }, { id: '', name: 'accommodation' },
                          { id: '', name: 'transport' }, { id: '', name: 'office' }, { id: '', name: 'training' },
                        ]).map((c) => (
                          <option key={c.id || c.name} value={c.name}>{c.name}</option>
                        ))}
                      </select>
                      <FontAwesomeIcon
                        icon={faChevronDown}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-textMuted pointer-events-none"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={handleSuggestCategory}
                      disabled={suggestCategoryLoading || categoriesLoading}
                      className="h-10 px-4 rounded-lg border border-primary bg-indigo-50 text-primary text-sm font-medium hover:bg-indigo-100 flex items-center gap-2 shrink-0 disabled:opacity-50"
                    >
                      {suggestCategoryLoading ? (
                        <FontAwesomeIcon icon={faSpinner} className="animate-spin" />
                      ) : (
                        <FontAwesomeIcon icon={faRobot} className="text-xs" />
                      )}
                      <span>Suggest</span>
                    </button>
                  </div>
                  {suggestionReasoning && (
                    <p className="mt-1.5 text-xs text-textMuted">{suggestionReasoning}</p>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-textPrimary mb-2">
                  Description <span className="text-errorRed">*</span>
                </label>
                <textarea
                  rows={3}
                  placeholder="Business purpose of this expense..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-2">
                    Payment Method <span className="text-errorRed">*</span>
                  </label>
                  <select
                    className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    value={formData.payment_method || 'company-card'}
                    onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                  >
                    {formData.payment_method && !['company-card', 'personal-card', 'cash', 'bank-transfer'].includes(formData.payment_method) && (
                      <option value={formData.payment_method}>From receipt: {formData.payment_method}</option>
                    )}
                    <option value="company-card">Company Card (****4521)</option>
                    <option value="personal-card">Personal Card</option>
                    <option value="cash">Cash</option>
                    <option value="bank-transfer">Bank Transfer</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-2">
                    Cost Center <span className="text-errorRed">*</span>
                  </label>
                  <select
                    className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    defaultValue="sales"
                  >
                    <option value="sales">Sales Department</option>
                    <option value="marketing">Marketing</option>
                    <option value="engineering">Engineering</option>
                    <option value="operations">Operations</option>
                    <option value="finance">Finance</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-2">Project (Optional)</label>
                  <select className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent">
                    <option value="">Select project...</option>
                    <option value="proj1">Q1 Product Launch</option>
                    <option value="proj2">Client Onboarding</option>
                    <option value="proj3">Website Redesign</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-textPrimary mb-2">Billable to Client</label>
                  <div className="flex items-center space-x-3 h-10">
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                    <span className="text-sm text-textSecondary">Mark as billable</span>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-textPrimary mb-2">Attendees (For meals)</label>
                <div className="flex flex-wrap gap-2 mb-2">
                  <span className="inline-flex items-center space-x-2 px-3 py-1.5 bg-indigo-50 text-primary text-sm rounded-lg">
                    <span>Jean Dupont (You)</span>
                    <button className="text-primary hover:text-primaryHover">
                      <FontAwesomeIcon icon={faTimes} className="text-xs" />
                    </button>
                  </span>
                  <span className="inline-flex items-center space-x-2 px-3 py-1.5 bg-indigo-50 text-primary text-sm rounded-lg">
                    <span>Marie Laurent</span>
                    <button className="text-primary hover:text-primaryHover">
                      <FontAwesomeIcon icon={faTimes} className="text-xs" />
                    </button>
                  </span>
                </div>
                <select className="w-full h-10 px-3 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent">
                  <option value="">Add attendee...</option>
                  <option value="user1">Thomas Bernard</option>
                  <option value="user2">Sophie Martin</option>
                  <option value="user3">Pierre Dubois</option>
                  <option value="external">External Guest</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-textPrimary mb-2">Additional Notes</label>
                <textarea
                  rows={3}
                  placeholder="Any additional information..."
                  className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
                />
              </div>
            </div>
          </section>

          <section className="flex items-center justify-between">
            <button
              onClick={() => router.back()}
              className="h-12 px-6 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50"
            >
              Cancel
            </button>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleSaveDraft}
                disabled={saving || !formData.merchant_name || !formData.expense_date || !formData.amount}
                className="h-12 px-6 border border-borderColor rounded-lg text-sm font-medium text-textSecondary hover:bg-gray-50 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FontAwesomeIcon icon={faSave} />
                <span>Save as Draft</span>
              </button>
              <button
                onClick={handleAddToReport}
                disabled={saving || !formData.merchant_name || !formData.expense_date || !formData.amount}
                className="h-12 px-6 bg-infoBlue hover:bg-blue-600 text-white rounded-lg text-sm font-medium flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FontAwesomeIcon icon={faFolderPlus} />
                <span>Add to Report</span>
              </button>
              <button
                onClick={handleSubmit}
                disabled={saving || !formData.merchant_name || !formData.expense_date || !formData.amount}
                className="h-12 px-8 bg-primary hover:bg-primaryHover disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium flex items-center space-x-2"
              >
                <FontAwesomeIcon icon={faPaperPlane} />
                <span>{saving ? 'Submitting...' : 'Submit for Approval'}</span>
              </button>
            </div>
          </section>
        </div>

        <div className="col-span-1">
          <section className="bg-surface rounded-xl p-6 border border-borderColor shadow-sm sticky top-24">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-textPrimary mb-1">Policy Validation</h2>
              <p className="text-sm text-textSecondary">Real-time compliance checks</p>
            </div>

            <div className="space-y-4">
              <div className="p-4 bg-lowRisk border border-green-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-successGreen rounded-lg flex items-center justify-center flex-shrink-0">
                    <FontAwesomeIcon icon={faCheck} className="text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-textPrimary mb-1">Within Meal Limit</div>
                    <div className="text-xs text-textSecondary mb-2">
                      €89.00 is within the daily meal limit of €100.00
                    </div>
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-successGreen" style={{ width: '89%' }}></div>
                    </div>
                    <div className="flex justify-between text-xs text-textMuted mt-1">
                      <span>€89.00</span>
                      <span>€100.00 limit</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-lowRisk border border-green-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-successGreen rounded-lg flex items-center justify-center flex-shrink-0">
                    <FontAwesomeIcon icon={faCheck} className="text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-textPrimary mb-1">VAT Compliant</div>
                    <div className="text-xs text-textSecondary">
                      VAT rate (10%) is correct for restaurant meals in France
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-lowRisk border border-green-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-successGreen rounded-lg flex items-center justify-center flex-shrink-0">
                    <FontAwesomeIcon icon={faCheck} className="text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-textPrimary mb-1">Receipt Quality</div>
                    <div className="text-xs text-textSecondary">All required information present and legible</div>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-infoBlue rounded-lg flex items-center justify-center flex-shrink-0">
                    <FontAwesomeIcon icon={faInfo} className="text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-textPrimary mb-1">URSSAF Guidelines</div>
                    <div className="text-xs text-textSecondary mb-2">
                      Business meals with clients are fully deductible when properly documented
                    </div>
                    <button className="text-xs text-infoBlue hover:text-blue-700 font-medium">Learn More →</button>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-mediumRisk border border-amber-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-warningAmber rounded-lg flex items-center justify-center flex-shrink-0">
                    <FontAwesomeIcon icon={faExclamation} className="text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-textPrimary mb-1">Approaching Daily Limit</div>
                    <div className="text-xs text-textSecondary mb-2">
                      You have €11.00 remaining in your daily meal budget
                    </div>
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-warningAmber" style={{ width: '89%' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-borderColor">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium text-textPrimary">Overall Compliance Score</span>
                <span className="text-2xl font-bold text-successGreen">98%</span>
              </div>
              <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-successGreen to-green-400" style={{ width: '98%' }}></div>
              </div>
              <p className="text-xs text-textMuted mt-2">Excellent! This expense meets all policy requirements.</p>
            </div>

            <div className="mt-6 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
                  <FontAwesomeIcon icon={faRobot} className="text-white" />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-textPrimary mb-1">AI Suggestion</div>
                  <div className="text-xs text-textSecondary mb-3">
                    Based on your expense patterns, consider adding this to your &quot;Client Meetings&quot; report
                  </div>
                  <button className="w-full h-8 bg-primary hover:bg-primaryHover text-white rounded-lg text-xs font-medium">
                    Apply Suggestion
                  </button>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </>
  )
}
