'use client'

import React, { useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts'
import { Button } from '@/components/ui/button'
import { useOfficerOverview } from '@/hooks/useApi'

interface OfficerDashboardProps {
  user: any
}

export function OfficerDashboard({ user }: OfficerDashboardProps) {
  const [selectedFilter, setSelectedFilter] = useState('all')
  const [timeRange, setTimeRange] = useState('week')
  const { data: live, isLoading } = useOfficerOverview()

  const overview = live?.overview ?? {
    total_applications: 0,
    pending_review: 0,
    sla_breaches: 0,
    avg_processing_days: 0,
    approved: 0,
  }
  const departments: any[] = live?.departments ?? []
  const distribution: any[] = live?.distribution ?? []

  const metrics = [
    {
      label: 'Total Applications',
      value: String(overview.total_applications ?? 0),
      change: 'live',
      status: 'info',
    },
    {
      label: 'Pending Review',
      value: String(overview.pending_review ?? 0),
      change: 'live',
      status: 'warning',
    },
    {
      label: 'SLA Breaches',
      value: String(overview.sla_breaches ?? 0),
      change: 'live',
      status: 'down',
    },
    {
      label: 'Avg Processing Time',
      value: `${overview.avg_processing_days ?? 0} days`,
      change: 'live',
      status: 'down',
    },
  ]

  const pendingApplications = [
    {
      id: 'APP-001',
      applicant: 'ABC Industries Pvt Ltd',
      type: 'Factory License',
      status: 'Under Review',
      submitted: '15 days ago',
      sla: '30 days',
      daysLeft: 15,
      risk: 'low',
    },
    {
      id: 'APP-002',
      applicant: 'XYZ Manufacturing',
      type: 'MPCB Consent',
      status: 'Query Raised',
      submitted: '25 days ago',
      sla: '60 days',
      daysLeft: 35,
      risk: 'high',
    },
    {
      id: 'APP-003',
      applicant: 'Tech Solutions Ltd',
      type: 'Fire Permission',
      status: 'Inspection Scheduled',
      submitted: '10 days ago',
      sla: '45 days',
      daysLeft: 35,
      risk: 'low',
    },
  ]

  const departmentStats = departments.map((d: any) => ({
    department: d.department,
    approved: d.approved ?? 0,
    processed: d.total ?? 0,
    pending: d.pending ?? 0,
    avgDays: d.avg_days ?? 0,
  }))

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'high':
        return 'text-red-600 bg-red-50'
      case 'medium':
        return 'text-yellow-600 bg-yellow-50'
      case 'low':
        return 'text-green-600 bg-green-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  return (
    <div className="space-y-8 p-8 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-4xl font-bold text-gray-900">Officer Dashboard</h1>
        <div className="text-right">
          <p className="text-gray-600">{user?.name || 'Officer'}</p>
          <p className="text-sm text-gray-500">{user?.department || 'Department'}</p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric, idx) => (
          <div key={idx} className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-gray-600 text-sm">{metric.label}</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{metric.value}</p>
              </div>
              <div className={metric.status === 'up' ? 'text-red-600' : metric.status === 'info' ? 'text-blue-600' : 'text-green-600'}>
                {metric.status === 'up' ? '↑' : metric.status === 'info' ? '•' : '↓'} {metric.change}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Pending Applications */}
        <div className="col-span-2 space-y-6">
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-xl font-bold text-gray-900">Pending Applications</h2>
              <select
                value={selectedFilter}
                onChange={(e) => setSelectedFilter(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-lg text-sm"
              >
                <option value="all">All Departments</option>
                <option value="maitri">MAITRI</option>
                <option value="mpcb">MPCB</option>
                <option value="fire">Fire Safety</option>
              </select>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      Application ID
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      Applicant
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      SLA Progress
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      Risk
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {pendingApplications.map((app) => (
                    <tr key={app.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium text-gray-900">{app.id}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{app.applicant}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{app.status}</td>
                      <td className="px-6 py-4">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{
                              width: `${((parseInt(app.sla) - app.daysLeft) / parseInt(app.sla)) * 100}%`,
                            }}
                          ></div>
                        </div>
                        <p className="text-xs text-gray-600 mt-1">{app.daysLeft} days left</p>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(app.risk)}`}>
                          {app.risk.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <Button size="sm" variant="outline">
                          Review
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Department Stats */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">Department Performance</h2>
            </div>

            <div className="h-64 p-6">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={departmentStats} margin={{ top: 5, right: 20, bottom: 5, left: -10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="department" tick={{ fontSize: 12, fill: '#6b7280' }} />
                  <YAxis tick={{ fontSize: 12, fill: '#6b7280' }} />
                  <Tooltip
                    contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
                  />
                  <Bar dataKey="processed" name="Processed" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={28} />
                  <Bar dataKey="pending" name="Pending" fill="#f59e0b" radius={[4, 4, 0, 0]} barSize={28} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-bold text-gray-900 mb-4">Quick Stats</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Today's Submissions</span>
                <span className="font-bold text-gray-900">12</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">This Week</span>
                <span className="font-bold text-gray-900">67</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">This Month</span>
                <span className="font-bold text-gray-900">247</span>
              </div>
            </div>
          </div>

          {/* Alerts */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-bold text-gray-900 mb-4">System Alerts</h3>
            <div className="space-y-3">
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm font-medium text-red-800">5 SLA Breaches</p>
                <p className="text-xs text-red-600 mt-1">Require immediate attention</p>
              </div>
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm font-medium text-yellow-800">12 At Risk</p>
                <p className="text-xs text-yellow-600 mt-1">May breach SLA soon</p>
              </div>
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm font-medium text-blue-800">38 Pending</p>
                <p className="text-xs text-blue-600 mt-1">Awaiting review</p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-bold text-gray-900 mb-4">Quick Actions</h3>
            <div className="space-y-2">
              <Button className="w-full justify-start" variant="outline">
                Generate SLA Report
              </Button>
              <Button className="w-full justify-start" variant="outline">
                Send Bulk Reminders
              </Button>
              <Button className="w-full justify-start" variant="outline">
                Schedule Reviews
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default OfficerDashboard
