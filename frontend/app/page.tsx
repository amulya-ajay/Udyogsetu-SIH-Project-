'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  Building2,
  FileSearch,
  ShieldCheck,
  Landmark,
  Bot,
  Gift,
  ArrowRight,
  Sparkles,
} from 'lucide-react'
import { Button } from '@/components/ui/button'

const features = [
  { icon: FileSearch, title: 'Intelligent Approvals', description: 'Get personalized approval checklists based on your project' },
  { icon: ShieldCheck, title: 'Document Intelligence', description: 'AI-powered document validation and cross-checking' },
  { icon: Landmark, title: 'Compliance Tracking', description: 'Stay on top of post-approval compliance requirements' },
  { icon: Building2, title: 'Government Integration', description: 'Real-time status updates from government systems' },
  { icon: Bot, title: 'Regulatory Copilot', description: 'Ask questions about regulations and get grounded answers' },
  { icon: Gift, title: 'Incentive Discovery', description: 'Find and apply for government schemes you qualify for' },
]

export default function Home() {
  const [isScrolled, setIsScrolled] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 0)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <nav
        className={`sticky top-0 z-50 transition-all ${
          isScrolled ? 'bg-white/95 backdrop-blur shadow-md' : 'bg-transparent'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="inline-flex items-center justify-center w-9 h-9 bg-blue-600 rounded-xl">
                <Building2 className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-bold text-blue-600">UDYOGSETU</h1>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => router.push('/login')}>
                Login
              </Button>
              <Button onClick={() => router.push('/register')}>Get Started</Button>
            </div>
          </div>
        </div>
      </nav>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-sm font-medium mb-8">
            <Sparkles className="w-4 h-4" />
            Government of Maharashtra · Smart India Hackathon
          </div>
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            From Idea to Industry
            <span className="text-blue-600"> One Intelligent Journey</span>
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Understand approvals, prepare documents, track applications, stay compliant and
            discover government support — from one place.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" onClick={() => router.push('/register')}>
              Start Your Project
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}
            >
              Explore How It Works
            </Button>
          </div>
        </div>
      </section>

      <section className="bg-white py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h3 className="text-3xl font-bold text-center mb-4 text-gray-900">Key Features</h3>
          <p className="text-center text-gray-600 mb-12 max-w-2xl mx-auto">
            Everything you need to set up and run an industrial unit in Maharashtra
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, i) => {
              const Icon = feature.icon
              return (
                <div
                  key={i}
                  className="group border border-gray-200 rounded-xl p-6 hover:shadow-lg hover:border-blue-200 transition"
                >
                  <div className="w-12 h-12 rounded-lg bg-blue-50 flex items-center justify-center mb-4 group-hover:bg-blue-600 transition">
                    <Icon className="w-6 h-6 text-blue-600 group-hover:text-white transition" />
                  </div>
                  <h4 className="text-lg font-semibold mb-2 text-gray-900">{feature.title}</h4>
                  <p className="text-gray-600">{feature.description}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      <section id="how-it-works" className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h3 className="text-3xl font-bold text-center mb-12 text-gray-900">How It Works</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[
              { step: 1, title: 'Tell Us About Your Project', desc: 'Answer a few questions about your business' },
              { step: 2, title: 'Get Approval Roadmap', desc: 'AI builds your personalized approval checklist' },
              { step: 3, title: 'Upload Documents', desc: 'Validate and verify documents automatically' },
              { step: 4, title: 'Track & Comply', desc: 'Monitor deadlines and stay compliant' },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="bg-blue-600 text-white rounded-2xl w-12 h-12 flex items-center justify-center mx-auto mb-4 text-lg font-bold shadow-lg shadow-blue-200">
                  {item.step}
                </div>
                <p className="text-gray-900 font-semibold mb-1">{item.title}</p>
                <p className="text-sm text-gray-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-blue-600 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h3 className="text-3xl font-bold mb-4">Ready to Streamline Your Approvals?</h3>
          <p className="text-xl mb-8 opacity-90">
            Join entrepreneurs across Maharashtra already using UDYOGSETU
          </p>
          <Button size="lg" variant="secondary" onClick={() => router.push('/register')}>
            Get Started Now
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </section>

      <footer className="bg-gray-900 text-gray-300 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="inline-flex items-center justify-center w-8 h-8 bg-blue-600 rounded-lg">
                  <Building2 className="w-4 h-4 text-white" />
                </div>
                <h4 className="text-white font-semibold">UDYOGSETU</h4>
              </div>
              <p className="text-sm">
                An intelligent platform helping entrepreneurs navigate industrial approvals and compliance.
              </p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Quick Links</h4>
              <ul className="text-sm space-y-2">
                <li><Link href="#" className="hover:text-white">Documentation</Link></li>
                <li><Link href="#" className="hover:text-white">API Reference</Link></li>
                <li><Link href="#" className="hover:text-white">Support</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Legal</h4>
              <ul className="text-sm space-y-2">
                <li><Link href="#" className="hover:text-white">Privacy Policy</Link></li>
                <li><Link href="#" className="hover:text-white">Terms of Service</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Contact</h4>
              <p className="text-sm">Email: support@udyogsetu.gov.in</p>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8">
            <p className="text-center text-sm">© 2026 UDYOGSETU. Government of Maharashtra.</p>
          </div>
        </div>
      </footer>
    </main>
  )
}