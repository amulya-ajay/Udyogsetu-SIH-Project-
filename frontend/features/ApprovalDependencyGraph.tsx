'use client'

import React, { useEffect, useState } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useApprovalGraph } from '@/hooks/useApi'

interface DependencyGraphProps {
  projectId: string
}

const STATUS_COLORS: Record<string, string> = {
  APPROVED: '#10b981',
  SUBMITTED: '#3b82f6',
  UNDER_REVIEW: '#f59e0b',
  QUERY_RAISED: '#ef4444',
  NOT_STARTED: '#6b7280',
}

export function ApprovalDependencyGraph({ projectId }: DependencyGraphProps) {
  const { data, isLoading } = useApprovalGraph(projectId)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [critical, setCritical] = useState<string[]>([])
  const [durationDays, setDurationDays] = useState(0)

  useEffect(() => {
    if (!data) return

    const graphNodes: Node[] = []
    const graphEdges: Edge[] = []
    const criticalIds = new Set<string>((data.critical_path?.approval_ids ?? []) as string[])

    // Project root node.
    graphNodes.push({
      id: 'project',
      data: { label: 'Project Initiated' },
      position: { x: 250, y: 0 },
      style: {
        background: '#3b82f6',
        color: 'white',
        border: '2px solid #1e40af',
        borderRadius: '8px',
        padding: '10px',
        fontWeight: 'bold',
      },
    })

    const total = data.nodes?.length ?? 0
    const mid = Math.ceil(total / 2)

    data.nodes?.forEach((approval: any, index: number) => {
      const isCritical = criticalIds.has(approval.id)
      const bg = STATUS_COLORS[approval.status] ?? '#6b7280'
      graphNodes.push({
        id: approval.id,
        data: {
          label: (
            <div>
              <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>{approval.label}</div>
              <div style={{ fontSize: '12px', opacity: 0.85 }}>{approval.department}</div>
              <div style={{ fontSize: '11px', marginTop: '4px', opacity: 0.7 }}>
                ~{approval.days} days • {approval.status?.replace(/_/g, ' ')}
              </div>
            </div>
          ),
        },
        position: {
          x: index < mid ? 0 : 520,
          y: (index % mid) * 140 + 120,
        },
        style: {
          background: bg,
          color: 'white',
          border: isCritical ? '3px solid #facc15' : '2px solid rgba(0,0,0,0.3)',
          borderRadius: '8px',
          padding: '12px',
          minWidth: '210px',
          textAlign: 'center',
          fontSize: '12px',
        },
      })
    })

    // Connect any node with no incoming dependency to the project root.
    const hasIncoming = new Set(data.edges?.map((e: any) => e.target) ?? [])
    data.nodes?.forEach((approval: any) => {
      if (!hasIncoming.has(approval.id)) {
        graphEdges.push({
          id: `project-${approval.id}`,
          source: 'project',
          target: approval.id,
          style: { stroke: '#9ca3af' },
        })
      }
    })

    // Add real dependency edges, highlighting those on the critical path.
    data.edges?.forEach((e: any, i: number) => {
      const onCritical =
        criticalIds.has(e.source) && criticalIds.has(e.target)
      graphEdges.push({
        id: e.id ?? `e${i}`,
        source: e.source,
        target: e.target,
        animated: onCritical,
        label: onCritical ? 'critical' : undefined,
        style: onCritical
          ? { stroke: '#facc15', strokeWidth: 3 }
          : { stroke: '#6b7280' },
      })
    })

    setNodes(graphNodes)
    setEdges(graphEdges)
    setCritical([...criticalIds])
    setDurationDays(data.critical_path?.duration_days ?? 0)
  }, [data, setNodes, setEdges])

  if (isLoading) {
    return <div className="text-center py-12">Loading dependency graph...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-2xl font-semibold text-gray-900">Approval Dependency Map</h3>
        <div className="flex gap-8">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{data?.nodes?.length ?? 0}</div>
            <div className="text-sm text-gray-600">Approvals</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-yellow-600">{critical.length}</div>
            <div className="text-sm text-gray-600">On Critical Path</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900">{durationDays} days</div>
            <div className="text-sm text-gray-600">Est. Total Time</div>
          </div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden" style={{ height: '600px' }}>
        <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}>
          <Background />
          <Controls />
        </ReactFlow>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-yellow-400 rounded"></div>
            <span className="text-sm font-medium text-gray-900">Critical Path</span>
          </div>
          <p className="text-xs text-gray-600 mt-1">Drives overall project duration</p>
        </div>
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-blue-500 rounded"></div>
            <span className="text-sm font-medium text-gray-900">Submitted</span>
          </div>
          <p className="text-xs text-gray-600 mt-1">Application submitted</p>
        </div>
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-gray-400 rounded"></div>
            <span className="text-sm font-medium text-gray-900">Not Started</span>
          </div>
          <p className="text-xs text-gray-600 mt-1">No application yet</p>
        </div>
      </div>
    </div>
  )
}

export default ApprovalDependencyGraph