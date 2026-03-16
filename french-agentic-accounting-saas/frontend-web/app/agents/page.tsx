'use client'
import { useState, useEffect } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faRobot, faPlay, faPause, faSync } from '@fortawesome/free-solid-svg-icons'
import { agentsAPI } from '@/lib/api'

export default function AgentsPage() {
  const [tasks, setTasks] = useState<any[]>([])
  const [status, setStatus] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadData() }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [tasksRes, statusRes] = await Promise.all([agentsAPI.listTasks(), agentsAPI.getStatus()])
      setTasks(tasksRes || [])
      setStatus(statusRes)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  async function handleToggle(agentCode: string) {
    try {
      await agentsAPI.toggleTask(agentCode)
      loadData()
    } catch (err) { console.error(err) }
  }

  return (
    <div className="p-6 max-w-[1200px] mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-textPrimary">Agents Autonomes</h1>
        <p className="text-sm text-textSecondary mt-1">Gestion des agents A2A</p>
      </div>

      {/* Status cards */}
      {status && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg border border-borderColor text-center">
            <div className="text-2xl font-bold text-primary">{status.total_agents}</div>
            <div className="text-xs text-textSecondary">Agents</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg border border-green-200 text-center">
            <div className="text-2xl font-bold text-green-700">{status.active_agents}</div>
            <div className="text-xs text-green-600">Actifs</div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-borderColor text-center">
            <div className="text-2xl font-bold">{status.total_runs}</div>
            <div className="text-xs text-textSecondary">Executions</div>
          </div>
          <div className={`p-4 rounded-lg border text-center ${status.error_rate > 10 ? 'bg-red-50 border-red-200' : 'bg-white border-borderColor'}`}>
            <div className={`text-2xl font-bold ${status.error_rate > 10 ? 'text-red-700' : ''}`}>{status.error_rate}%</div>
            <div className="text-xs text-textSecondary">Taux erreur</div>
          </div>
        </div>
      )}

      {/* Tasks */}
      {loading ? (
        <div className="text-center py-12 text-textSecondary">Chargement...</div>
      ) : (
        <div className="space-y-3">
          {tasks.map((task) => (
            <div key={task.agent_code} className="bg-white rounded-xl border border-borderColor p-5 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${task.is_active ? 'bg-green-50' : 'bg-gray-100'}`}>
                  <FontAwesomeIcon icon={faRobot} className={task.is_active ? 'text-green-600' : 'text-gray-400'} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm text-textPrimary">{task.agent_code}</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${task.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                      {task.is_active ? 'Actif' : 'Inactif'}
                    </span>
                  </div>
                  <p className="text-xs text-textSecondary">{task.name}</p>
                  <p className="text-xs text-textMuted mt-0.5">Cron: {task.cron_expression} | Executions: {task.run_count} | Erreurs: {task.error_count}</p>
                </div>
              </div>
              <button onClick={() => handleToggle(task.agent_code)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium ${task.is_active ? 'bg-red-50 text-red-700 hover:bg-red-100' : 'bg-green-50 text-green-700 hover:bg-green-100'}`}>
                <FontAwesomeIcon icon={task.is_active ? faPause : faPlay} className="mr-1" />
                {task.is_active ? 'Desactiver' : 'Activer'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
