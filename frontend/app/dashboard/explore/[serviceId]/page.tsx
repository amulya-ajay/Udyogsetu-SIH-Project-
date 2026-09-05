'use client'

import { useParams } from 'next/navigation'
import { Compass, Loader2, Landmark } from 'lucide-react'
import { useService } from '@/hooks/useApi'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { ExploreApply } from '@/features/ExploreApply'

function riskVariant(risk: string): 'danger' | 'warning' | 'success' | 'outline' {
  switch ((risk || '').toUpperCase()) {
    case 'HIGH':
      return 'danger'
    case 'MEDIUM':
      return 'warning'
    case 'LOW':
      return 'success'
    default:
      return 'outline'
  }
}

export default function ServiceDetailPage() {
  const params = useParams()
  const serviceId = params.serviceId as string
  const { data: service, isLoading } = useService(serviceId)

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-gray-600">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <p className="mt-4 text-sm">Loading service...</p>
      </div>
    )
  }

  if (!service) {
    return (
      <Card>
        <CardContent className="py-16 text-center">
          <p className="text-lg text-gray-900">Service not found</p>
        </CardContent>
      </Card>
    )
  }

  const fees = service.fees
  const eligibility = service.eligibility_summary

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center">
              <Compass className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 capitalize">{service.name}</h1>
              <p className="mt-1 text-gray-600 capitalize">
                {service.category} · {service.authority}
              </p>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {service.is_demo && <Badge variant="warning">Demo</Badge>}
          <Badge variant="info">{String(service.application_mode).replace('_', ' ')}</Badge>
          {service.sla_days ? <Badge variant="outline">{service.sla_days} day SLA</Badge> : null}
          <Badge variant={riskVariant(service.risk_level)}>{service.risk_level} Risk</Badge>
        </div>
      </div>

      {service.description && (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <p className="text-gray-700">{service.description}</p>
          {service.official_reference && (
            <p className="mt-2 text-sm text-gray-500">
              <Landmark className="w-4 h-4 inline mr-1" />
              {service.official_reference}
            </p>
          )}
        </div>
      )}

      {(fees || eligibility) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {eligibility && (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h3 className="font-semibold text-gray-900 mb-1">Eligibility</h3>
              <p className="text-sm text-gray-700 whitespace-pre-line">{eligibility}</p>
            </div>
          )}
          {fees && (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h3 className="font-semibold text-gray-900 mb-1">Fees</h3>
              <p className="text-sm text-gray-700 whitespace-pre-line">{fees}</p>
            </div>
          )}
        </div>
      )}

      <ExploreApply service={service} />
    </div>
  )
}