'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  Building2,
  LayoutDashboard,
  FileText,
  FolderOpen,
  Bot,
  ShieldCheck,
  Gift,
  LogOut,
  Plus,
  Compass,
  ClipboardList,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { getSessionUser, isTokenExpired, logout } from '@/lib/auth'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/dashboard/explore', label: 'Explore Services', icon: Compass },
  { href: '/dashboard/applications', label: 'Applications', icon: ClipboardList },
  { href: '/dashboard/new-project', label: 'New Project', icon: Plus },
]

// Top-level dashboard segments that are NOT a project id.
const reservedSegments = new Set(['new-project', 'explore', 'applications'])

const projectNavItems = [
  { key: '', label: 'Overview', icon: FolderOpen },
  { key: 'approvals', label: 'Approvals', icon: FileText },
  { key: 'documents', label: 'Documents', icon: FileText },
  { key: 'compliance', label: 'Compliance', icon: ShieldCheck },
  { key: 'copilot', label: 'Regulatory Copilot', icon: Bot },
  { key: 'schemes', label: 'Schemes & Support', icon: Gift },
]

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const [user, setUser] = useState<{ name: string; role: string } | null>(null)
  const [projects, setProjects] = useState<any[]>([])

  const projectMatch = pathname.match(/^\/dashboard\/([^/]+)(?:\/([^/]+))?/)
  const currentProjectId =
    projectMatch && !reservedSegments.has(projectMatch[1]) ? projectMatch[1] : undefined
  const currentProjectTab = currentProjectId ? projectMatch?.[2] || '' : ''

  useEffect(() => {
    if (isTokenExpired()) {
      logout()
      return
    }
    const sessionUser = getSessionUser()
    if (sessionUser) {
      setUser({ name: sessionUser.name, role: sessionUser.role })
    }
  }, [router])

  const handleLogout = () => {
    logout()
  }

  const isProjectContext = !!currentProjectId

  return (
    <div className="min-h-screen bg-gray-50">
      <aside className="fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="inline-flex items-center justify-center w-10 h-10 bg-blue-600 rounded-xl">
              <Building2 className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900">UDYOGSETU</span>
          </Link>
        </div>

        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const active = item.href === '/dashboard'
              ? pathname === '/dashboard'
              : pathname === item.href || pathname.startsWith(`${item.href}/`)
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition',
                  active
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-100',
                )}
              >
                <Icon className="w-4.5 h-4.5" />
                {item.label}
              </Link>
            )
          })}

          {isProjectContext && (
            <>
              <div className="pt-4 pb-2">
                <p className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Project
                </p>
              </div>
              {projectNavItems.map((item) => {
                const active = currentProjectTab === item.key
                const Icon = item.icon
                return (
                  <Link
                    key={item.key}
                    href={`/dashboard/${currentProjectId}${item.key ? `/${item.key}` : ''}`}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition',
                      active
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-700 hover:bg-gray-100',
                    )}
                  >
                    <Icon className="w-4.5 h-4.5" />
                    {item.label}
                  </Link>
                )
              })}
            </>
          )}
        </nav>

        <div className="p-4 border-t border-gray-200 space-y-2">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-9 h-9 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-semibold">
              {(user?.name?.[0] || 'U').toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate capitalize">{user?.name}</p>
              <p className="text-xs text-gray-500">
                {user?.role === 'OFFICER' ? 'Officer' : 'Entrepreneur'}
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start text-gray-600"
            onClick={handleLogout}
          >
            <LogOut className="w-4 h-4 mr-2" />
            Logout
          </Button>
        </div>
      </aside>

      <main className="ml-64 p-8 min-h-screen">
        <ErrorBoundary>{children}</ErrorBoundary>
      </main>
    </div>
  )
}