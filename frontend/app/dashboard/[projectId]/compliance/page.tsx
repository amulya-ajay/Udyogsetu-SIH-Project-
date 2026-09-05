'use client'

import { useParams, useRouter } from 'next/navigation'
import { CheckCircle2, AlertTriangle, Clock } from 'lucide-react'
import { useComplianceDashboard } from '@/hooks/useApi'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export default function ProjectCompliancePage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.projectId as string
  const { data, isLoading, isError } = useComplianceDashboard(projectId)

  if (isLoading) {
    return <div className="text-center py-24 text-gray-600">Loading compliance data...</div>
  }

  if (isError || !data) {
    return (
      <div className="text-center py-24">
        <p className="text-lg text-gray-900">Compliance data unavailable</p>
        <p className="mt-2 text-gray-600">
          Run the approval analysis first to generate compliance requirements.
        </p>
        <Button className="mt-6" onClick={() => router.push(`/dashboard/${projectId}/approvals`)}>
          Go to Approvals
        </Button>
      </div>
    )
  }

  const items = data.items || []
  const onTrack = items.filter((i: any) => i.status === 'ON_TRACK').length
  const atRisk = items.filter((i: any) => i.status === 'AT_RISK').length
  const overdue = items.filter((i: any) => i.status === 'OVERDUE').length
  const score = data.score ?? Math.round((onTrack / Math.max(items.length, 1)) * 100)

  const stats = [
    { label: 'Compliance Score', value: `${score}%`, color: 'text-blue-600', icon: CheckCircle2 },
    { label: 'On Track', value: onTrack, color: 'text-green-600', icon: CheckCircle2 },
    { label: 'At Risk', value: atRisk, color: 'text-yellow-600', icon: AlertTriangle },
    { label: 'Overdue', value: overdue, color: 'text-red-600', icon: Clock },
  ]

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Compliance</h1>
        <p className="mt-1 text-gray-600">Monitor post-approval compliance requirements and renewals</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {stats.map((stat, idx) => {
          const Icon = stat.icon
          return (
            <Card key={idx}>
              <CardHeader className="p-6 pb-2">
                <Icon className={`w-5 h-5 mb-2 ${stat.color}`} />
                <CardTitle className="text-3xl font-bold">{stat.value}</CardTitle>
              </CardHeader>
              <CardContent className="p-6 pt-2">
                <p className="text-sm text-gray-600">{stat.label}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Compliance Requirements</CardTitle>
        </CardHeader>
        <CardContent>
          {items.length === 0 ? (
            <p className="py-12 text-center text-gray-600">No compliance items generated yet.</p>
          ) : (
            <div className="divide-y divide-gray-200">
              {items.map((item: any) => (
                <div key={item.id} className="py-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{item.requirement}</p>
                    <p className="text-sm text-gray-600">
                      {item.category} · Due {item.next_due ? new Date(item.next_due).toLocaleDateString() : '—'}
                    </p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium ${
                      item.status === 'ON_TRACK'
                        ? 'bg-green-100 text-green-800'
                        : item.status === 'AT_RISK'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {item.status.replace('_', ' ')}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}