'use client'

import { useParams, useRouter } from 'next/navigation'
import { useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, FileText, Loader2, ShieldCheck } from 'lucide-react'
import {
  useApplication,
  useApplicationTransitions,
  useSlaStatus,
  useTransitionApplication,
} from '@/hooks/useApi'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'

function statusVariant(status: string): 'success' | 'danger' | 'default' | 'warning' | 'info' | 'outline' {
  switch (status) {
    case 'APPROVED':
      return 'success'
    case 'REJECTED':
      return 'danger'
    case 'QUERY_RAISED':
      return 'warning'
    case 'INSPECTION':
      return 'info'
    case 'SUBMITTED':
    case 'UNDER_REVIEW':
      return 'default'
    default:
      return 'outline'
  }
}

function slaVariant(status: string): 'success' | 'warning' | 'danger' | 'default' | 'info' | 'outline' {
  switch (status) {
    case 'ON_TRACK':
      return 'success'
    case 'AT_RISK':
      return 'warning'
    case 'BREACHED':
      return 'danger'
    case 'COMPLETED':
      return 'info'
    default:
      return 'outline'
  }
}

export default function ApplicationDetailPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const applicationId = params.applicationId as string

  const { data: application, isLoading } = useApplication(applicationId)
  const { data: transitions } = useApplicationTransitions(applicationId)
  const { data: sla } = useSlaStatus(applicationId)
  const transition = useTransitionApplication()

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-gray-600">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <p className="mt-4 text-sm">Loading application...</p>
      </div>
    )
  }

  if (!application) {
    return (
      <Card>
        <CardContent className="py-16 text-center">
          <p className="text-lg text-gray-900">Application not found</p>
        </CardContent>
      </Card>
    )
  }

  const available = transitions?.available_transitions || []

  const runTransition = async (to: string) => {
    try {
      await transition.mutateAsync({ applicationId, toStatus: to })
      queryClient.invalidateQueries({ queryKey: ['application'] })
      queryClient.invalidateQueries({ queryKey: ['application-transitions'] })
      queryClient.invalidateQueries({ queryKey: ['application-sla'] })
      queryClient.invalidateQueries({ queryKey: ['applications'] })
    } catch (e) {
      console.error(e)
    }
  }

  const status = application.status

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard/applications')}>
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Applications
      </Button>

      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold text-gray-900 capitalize">{application.approval_name}</h1>
            <Badge variant={statusVariant(status)}>{status.replace('_', ' ')}</Badge>
          </div>
          <p className="mt-1 text-gray-600">{application.department}</p>
        </div>
        {available.length > 0 && (
          <div className="space-y-1 text-right">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Available actions</p>
            <div className="flex flex-wrap gap-2">
              {available.map((t: any) => (
                <Button
                  key={t.to}
                  size="sm"
                  variant={t.to === 'SUBMITTED' ? 'default' : 'outline'}
                  onClick={() => runTransition(t.to)}
                  disabled={transition.isPending}
                >
                  {t.label}
                </Button>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-6 col-span-1">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-blue-600" />
            SLA Status
          </h3>
          {sla ? (
            <div className="space-y-2">
              <Badge variant={slaVariant(sla.status)}>{sla.status.replace('_', ' ')}</Badge>
              <p className="text-sm text-gray-700">{sla.reason}</p>
              <div className="grid grid-cols-2 gap-2 text-sm pt-2">
                <div className="text-gray-500">Elapsed</div>
                <div className="text-right font-medium text-gray-900">{sla.days_elapsed} days</div>
                <div className="text-gray-500">Remaining</div>
                <div className="text-right font-medium text-gray-900">{sla.days_remaining} days</div>
                <div className="text-gray-500">Deadline</div>
                <div className="text-right font-medium text-gray-900">{sla.deadline || '—'}</div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500">SLA not yet computed.</p>
          )}
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6 col-span-2">
          <h3 className="font-semibold text-gray-900 mb-3">Details</h3>
          <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <div className="text-gray-500">Application ID</div>
            <div className="font-medium text-gray-900">{application.application_id}</div>
            <div className="text-gray-500">Project</div>
            <div className="font-medium text-gray-900">{application.project_name || '—'}</div>
            <div className="text-gray-500">Processing Time</div>
            <div className="font-medium text-gray-900">
              {application.estimated_processing_days
                ? `${application.estimated_processing_days} days`
                : '—'}
            </div>
            <div className="text-gray-500">Submitted At</div>
            <div className="font-medium text-gray-900">
              {application.submitted_at
                ? new Date(application.submitted_at).toLocaleString()
                : 'Not submitted'}
            </div>
            <div className="text-gray-500">Approved At</div>
            <div className="font-medium text-gray-900">
              {application.approved_at ? new Date(application.approved_at).toLocaleString() : '—'}
            </div>
          </div>
        </div>
      </div>

      <Card>
        <CardContent className="p-6">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            Journey
          </h3>
          <div className="text-sm text-gray-600">
            This application was started from the{' '}
            <span className="font-medium">Explore Government Services</span> journey and flows
            through the same tracking, SLA and officer review pipeline as every other approval.
            Upload documents from the service page to attach them here.
          </div>
        </CardContent>
      </Card>
    </div>
  )
}