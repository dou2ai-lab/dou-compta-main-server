'use client'
import { useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faMoneyBillWave, faCalculator } from '@fortawesome/free-solid-svg-icons'
import { payrollAPI } from '@/lib/api'

export default function PayrollPage() {
  const [form, setForm] = useState({ employee_name: '', gross_salary: '', net_salary: '', employer_charges: '', urssaf: '', retirement: '' })
  const [allocations, setAllocations] = useState<any[]>([])
  const [computing, setComputing] = useState(false)

  async function handleCompute() {
    setComputing(true)
    try {
      const res = await payrollAPI.allocateCharges({
        employee_name: form.employee_name,
        gross_salary: Number(form.gross_salary), net_salary: Number(form.net_salary),
        employer_charges: Number(form.employer_charges), urssaf: Number(form.urssaf), retirement: Number(form.retirement),
      })
      setAllocations(res || [])
    } catch (err) { console.error(err) }
    finally { setComputing(false) }
  }

  const fmt = (n: number) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(n)

  return (
    <div className="p-6 max-w-[1000px] mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-textPrimary">Paie & Social</h1>
        <p className="text-sm text-textSecondary mt-1">Ventilation des charges sociales</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-borderColor p-6">
          <h2 className="text-sm font-semibold mb-4">Donnees du bulletin</h2>
          <div className="space-y-3">
            {[
              { key: 'employee_name', label: 'Employe', type: 'text' },
              { key: 'gross_salary', label: 'Salaire brut', type: 'number' },
              { key: 'net_salary', label: 'Salaire net', type: 'number' },
              { key: 'employer_charges', label: 'Charges patronales', type: 'number' },
              { key: 'urssaf', label: 'URSSAF (salariale)', type: 'number' },
              { key: 'retirement', label: 'Retraite (salariale)', type: 'number' },
            ].map(f => (
              <div key={f.key}>
                <label className="block text-xs font-medium mb-1">{f.label}</label>
                <input type={f.type} value={(form as any)[f.key]} onChange={(e) => setForm({...form, [f.key]: e.target.value})}
                  className="w-full px-3 py-2 border border-borderColor rounded-lg text-sm" />
              </div>
            ))}
          </div>
          <button onClick={handleCompute} disabled={computing}
            className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm disabled:opacity-50">
            <FontAwesomeIcon icon={faCalculator} /> {computing ? 'Calcul...' : 'Ventiler les charges'}
          </button>
        </div>
        <div className="bg-white rounded-xl border border-borderColor p-6">
          <h2 className="text-sm font-semibold mb-4">Ecriture comptable</h2>
          {allocations.length === 0 ? (
            <p className="text-sm text-textSecondary text-center py-8">Saisissez les donnees et cliquez sur Ventiler</p>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b"><th className="text-left py-2 text-xs text-textSecondary">Compte</th>
                  <th className="text-right py-2 text-xs text-textSecondary">Debit</th><th className="text-right py-2 text-xs text-textSecondary">Credit</th></tr>
              </thead>
              <tbody>
                {allocations.map((a: any, i: number) => (
                  <tr key={i} className="border-b hover:bg-gray-50">
                    <td className="py-2 text-sm"><span className="font-mono text-primary">{a.account_code}</span> {a.account_name}</td>
                    <td className="py-2 text-sm text-right">{Number(a.debit) > 0 ? fmt(a.debit) : ''}</td>
                    <td className="py-2 text-sm text-right">{Number(a.credit) > 0 ? fmt(a.credit) : ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
