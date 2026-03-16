'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { monitoringAPI } from '@/lib/api';

interface ServiceHealth {
  service_name: string;
  status: string;
  last_seen: string | null;
  metrics_count: number;
  time_since_last_seconds?: number;
}

interface Alert {
  id: string;
  service_name: string;
  metric_name: string;
  metric_value: number;
  threshold: number;
  severity: string;
  message: string;
  triggered_at: string;
}

interface SLO {
  id: string;
  service_name: string;
  metric_name: string;
  target_value: number;
  compliance: boolean;
  error_budget_percentage: number;
}

function MonitoringPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [slos, setSlos] = useState<SLO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchMonitoringData();
      const interval = setInterval(fetchMonitoringData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  const fetchMonitoringData = async () => {
    try {
      setLoading(true);
      
      // Fetch service health
      const servicesData = await monitoringAPI.getServiceHealth();
      setServices(Array.isArray(servicesData) ? servicesData : [servicesData]);

      // Fetch active alerts
      const alertsData = await monitoringAPI.getActiveAlerts();
      setAlerts(Array.isArray(alertsData) ? alertsData : []);

      // Fetch SLOs
      const slosData = await monitoringAPI.getSLOs();
      const slosList = Array.isArray(slosData) ? slosData : [];
      // Calculate compliance for each SLO
      const slosWithCompliance = await Promise.all(
        slosList.map(async (slo: any) => {
          try {
            const compliance = await monitoringAPI.getSLOCompliance(slo.id);
            return { ...slo, ...compliance };
          } catch {
            return { ...slo, compliance: false, error_budget_percentage: 0 };
          }
        })
      );
      setSlos(slosWithCompliance);

      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch monitoring data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'unhealthy':
        return 'bg-red-100 text-red-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'info':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (authLoading || !isAuthenticated) {
    return <><div className="flex justify-center items-center h-screen text-lg">Loading...</div></>;
  }

  return (
    <>
      <div className="min-h-screen bg-gray-100 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900">Production Monitoring</h1>
            <p className="text-gray-600 mt-2">Real-time monitoring, SLOs, and alerts</p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
              {error}
            </div>
          )}

          {loading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Loading monitoring data...</p>
            </div>
          )}

          {/* Service Health Overview */}
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Service Health</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {services.map((service) => (
                <div key={service.service_name} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium text-gray-900">{service.service_name}</h3>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(service.status)}`}>
                      {service.status}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    <p>Last seen: {service.last_seen ? new Date(service.last_seen).toLocaleString() : 'Never'}</p>
                    <p>Metrics: {service.metrics_count}</p>
                    {service.time_since_last_seconds !== undefined && (
                      <p>Time since last: {service.time_since_last_seconds.toFixed(0)}s</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Active Alerts */}
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Active Alerts</h2>
            {alerts.length === 0 ? (
              <p className="text-gray-600">No active alerts</p>
            ) : (
              <div className="space-y-4">
                {alerts.map((alert) => (
                  <div key={alert.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <h3 className="font-medium text-gray-900">{alert.service_name}</h3>
                        <p className="text-sm text-gray-600">{alert.metric_name}</p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                        {alert.severity}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{alert.message}</p>
                    <div className="text-xs text-gray-500">
                      <p>Value: {alert.metric_value} | Threshold: {alert.threshold}</p>
                      <p>Triggered: {new Date(alert.triggered_at).toLocaleString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* SLO Compliance */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">SLO Compliance</h2>
            {slos.length === 0 ? (
              <p className="text-gray-600">No SLOs defined</p>
            ) : (
              <div className="space-y-4">
                {slos.map((slo) => (
                  <div key={slo.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <h3 className="font-medium text-gray-900">{slo.service_name}</h3>
                        <p className="text-sm text-gray-600">{slo.metric_name}</p>
                      </div>
                      <div className="text-right">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${slo.compliance ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {slo.compliance ? 'Compliant' : 'Non-Compliant'}
                        </span>
                      </div>
                    </div>
                    <div className="mt-2">
                      <div className="flex justify-between text-sm text-gray-600 mb-1">
                        <span>Target: {slo.target_value}</span>
                        <span>Error Budget: {slo.error_budget_percentage.toFixed(2)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${slo.compliance ? 'bg-green-500' : 'bg-red-500'}`}
                          style={{ width: `${Math.min(100, 100 - slo.error_budget_percentage)}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export default MonitoringPage;

