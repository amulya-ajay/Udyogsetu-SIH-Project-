'use client'

import { useState } from 'react'
import { useParams } from 'next/navigation'
import { useMatchSchemes } from '@/hooks/useApi'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Loader2, Gift, BadgeCheck } from 'lucide-react'
import { useProject } from '@/hooks/useApi'

export default function ProjectSchemesPage() {
  const params = useParams()
  const projectId = params.projectId as string
  const { data: project } = useProject(projectId)
  const matchSchemes = useMatchSchemes()

  const [investment, setInvestment] = useState<string>('')
  const [employees, setEmployees] = useState<string>('')
  const [matches, setMatches] = useState<any[]>([])

  const handleMatch = async () => {
    const result = await matchSchemes.mutateAsync({
      industry: project?.industry || '',
      location: project?.location_district || 'Maharashtra',
      investment: parseFloat(investment) || project?.investment_amount || 0,
      employees: parseInt(employees) || 0,
      business_type: 'Manufacturing',
    })
    const data = (result as any)?.matches || result || []
    setMatches(Array.isArray(data) ? data : [])
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Schemes & Government Support</h1>
        <p className="mt-1 text-gray-600">
          Find subsidies and incentives that match your project profile
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Match Your Project</CardTitle>
          <CardDescription>
            Enter your project details to discover eligible schemes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Investment (₹)
              </label>
              <Input
                type="number"
                placeholder="e.g. 5000000"
                value={investment}
                onChange={(e) => setInvestment(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Employees
              </label>
              <Input
                type="number"
                placeholder="e.g. 25"
                value={employees}
                onChange={(e) => setEmployees(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <Button onClick={handleMatch} disabled={matchSchemes.isPending} className="w-full">
                {matchSchemes.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Matching...
                  </>
                ) : (
                  <>
                    <Gift className="w-4 h-4 mr-2" />
                    Find Schemes
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {matches.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {matches.map((scheme: any) => (
            <Card key={scheme.id} className="hover:shadow-md transition">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle>{scheme.name}</CardTitle>
                    <CardDescription className="mt-1">{scheme.department}</CardDescription>
                  </div>
                  {typeof scheme.match_score === 'number' && (
                    <span className="px-3 py-1 rounded-full bg-green-100 text-green-800 text-xs font-semibold">
                      {scheme.match_score}% match
                    </span>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {Array.isArray(scheme.benefits) && scheme.benefits.length > 0 && (
                  <ul className="space-y-2">
                    {scheme.benefits.map((benefit: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                        <BadgeCheck className="w-4 h-4 text-green-600 mt-0.5 shrink-0" />
                        {benefit}
                      </li>
                    ))}
                  </ul>
                )}
                {scheme.match_reason && (
                  <p className="mt-4 text-sm text-gray-600">{scheme.match_reason}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {matches.length === 0 && !matchSchemes.isPending && (
        <p className="text-center py-12 text-gray-600">
          No schemes matched yet. Run the match above to see available support.
        </p>
      )}
    </div>
  )
}