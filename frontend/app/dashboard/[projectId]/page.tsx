'use client'

import { useParams, useRouter } from 'next/navigation'
import { ArrowRight, Bot, FileText, Gift, ShieldCheck } from 'lucide-react'
import { useProject } from '@/hooks/useApi'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

function DetailRow({ label, value }: { label: string; value?: string | number }) {
  return (
    <div className="flex justify-between py-2">
      <span className="text-sm text-gray-600">{label}</span>
      <span className="text-sm font-medium text-gray-900">{value ?? '—'}</span>
    </div>
  )
}

export default function ProjectOverviewPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.projectId as string
  const { data: project, isLoading, isError } = useProject(projectId)

  if (isLoading) {
    return <div className="text-center py-24 text-gray-600">Loading project...</div>
  }

  if (isError || !project) {
    return (
      <div className="text-center py-24">
        <p className="text-lg text-gray-900">Project not found</p>
        <Button className="mt-4" onClick={() => router.push('/dashboard')}>
          Back to Dashboard
        </Button>
      </div>
    )
  }

  const actions = [
    { href: 'approvals', label: 'View Approvals', icon: FileText },
    { href: 'documents', label: 'Upload Documents', icon: FileText },
    { href: 'compliance', label: 'Compliance Status', icon: ShieldCheck },
    { href: 'copilot', label: 'Ask Regulatory Copilot', icon: Bot },
    { href: 'schemes', label: 'Find Schemes', icon: Gift },
  ]

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
        <div className="mt-2 flex items-center gap-3">
          <Badge variant="default">{project.industry || 'Industry'}</Badge>
          <Badge variant="outline">{project.sector || 'Sector'}</Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Project Details</CardTitle>
          </CardHeader>
          <CardContent>
            <DetailRow label="Company" value={project.company_name} />
            <DetailRow label="Investment" value={project.investment_amount ? `₹${Number(project.investment_amount).toLocaleString()}` : '—'} />
            <DetailRow label="State" value={project.location_state} />
            <DetailRow label="District" value={project.location_district} />
            <DetailRow label="Created" value={project.created_at ? new Date(project.created_at).toLocaleDateString() : '—'} />
          </CardContent>
        </Card>

        <div className="space-y-4">
          {actions.map((action) => {
            const Icon = action.icon
            return (
              <Card
                key={action.href}
                className="hover:shadow-md transition cursor-pointer"
                onClick={() => router.push(`/dashboard/${projectId}/${action.href}`)}
              >
                <CardHeader className="p-4 flex-row items-center justify-between space-y-0">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center">
                      <Icon className="w-4.5 h-4.5 text-blue-600" />
                    </div>
                    <CardTitle className="text-sm">{action.label}</CardTitle>
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-400" />
                </CardHeader>
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  )
}