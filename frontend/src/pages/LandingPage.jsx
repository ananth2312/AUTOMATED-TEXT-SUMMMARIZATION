// src/pages/LandingPage.jsx
// ──────────────────────────
// Public landing page with hero, features, and workflow sections.

import { Link } from 'react-router-dom'
import {
  ArrowRight, BookOpen, Brain, CheckCircle, FileSearch,
  Key, Layers, Shield, Zap,
} from 'lucide-react'

const FEATURES = [
  { icon: FileSearch, title: 'PDF Extraction',   desc: 'Upload academic PDFs and extract structured text automatically.' },
  { icon: Brain,      title: 'Smart Summarisation', desc: 'TextRank-powered extractive summaries at concise, medium, and detailed levels.' },
  { icon: Key,        title: 'Key Phrases',      desc: 'YAKE algorithm ranks and deduplicates the most relevant academic phrases.' },
  { icon: Layers,     title: 'Section Detection', desc: 'Automatically identifies Abstract, Methodology, Results, Conclusion and more.' },
  { icon: Zap,        title: 'Instant Results',  desc: 'Fast local NLP pipeline — no cloud API needed, no data leaves your machine.' },
  { icon: Shield,     title: 'Private & Secure', desc: 'Your papers are stored locally. JWT authentication keeps your library private.' },
]

const STEPS = [
  { num: '01', title: 'Register & Log In',  desc: 'Create a free account to access your personal research library.' },
  { num: '02', title: 'Upload or Paste',    desc: 'Upload a PDF or paste your research paper text directly.' },
  { num: '03', title: 'Analyse',            desc: 'Our NLP pipeline extracts, cleans, and processes your document.' },
  { num: '04', title: 'Explore Results',    desc: 'Review summaries, key phrases, statistics, and detected sections.' },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* ── Header ── */}
      <header className="border-b border-slate-800/50 backdrop-blur-sm sticky top-0 z-10 bg-slate-950/80">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center">
              <BookOpen className="w-4 h-4 text-white" />
            </div>
            <span className="text-white font-bold text-lg">ResearchLens</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login"    className="btn btn-ghost btn-sm">Sign In</Link>
            <Link to="/register" className="btn btn-primary btn-sm">Get Started</Link>
          </div>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="relative overflow-hidden py-24 px-4 sm:px-6">
        <div className="absolute inset-0 bg-grid opacity-30 pointer-events-none" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px]
                        bg-primary-600/20 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full
                          bg-primary-900/50 border border-primary-700/50 text-primary-300
                          text-xs font-medium mb-6">
            <Zap className="w-3 h-3" />
            Powered by TextRank + YAKE NLP
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold leading-tight mb-6">
            Understand Research Papers
            <span className="block text-gradient">Faster Than Ever</span>
          </h1>

          <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-8 leading-relaxed">
            Upload any academic PDF or paste text to get instant extractive summaries,
            ranked key phrases, section detection, and rich document statistics.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
            <Link to="/register" className="btn btn-primary btn-lg">
              Start Analysing for Free
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/login" className="btn btn-secondary btn-lg">
              Sign In to Your Library
            </Link>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-20 px-4 sm:px-6 border-t border-slate-800/50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-white mb-3">Everything You Need</h2>
            <p className="text-slate-400">A complete academic reading assistant, running entirely on your machine.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="card p-5 group hover:border-primary-700/50 transition-all duration-200">
                <div className="w-10 h-10 rounded-lg bg-primary-900/50 border border-primary-800/50
                                flex items-center justify-center mb-4 group-hover:bg-primary-800/50 transition-colors">
                  <Icon className="w-5 h-5 text-primary-400" />
                </div>
                <h3 className="text-base font-semibold text-white mb-1.5">{title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ── */}
      <section className="py-20 px-4 sm:px-6 bg-slate-900/30 border-t border-slate-800/50">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-white mb-3">How It Works</h2>
            <p className="text-slate-400">From PDF to insight in four simple steps.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {STEPS.map(({ num, title, desc }) => (
              <div key={num} className="flex gap-4">
                <div className="text-4xl font-black text-primary-700 leading-none">{num}</div>
                <div>
                  <h3 className="font-semibold text-white mb-1">{title}</h3>
                  <p className="text-sm text-slate-400">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Responsible Use Notice ── */}
      <section className="py-10 px-4 sm:px-6 border-t border-slate-800/50">
        <div className="max-w-2xl mx-auto text-center">
          <div className="card p-5 border-amber-800/30 bg-amber-900/10">
            <p className="text-sm text-amber-300 leading-relaxed">
              <strong>Important:</strong> Summaries and key phrases are generated by automated NLP algorithms.
              They are machine-estimated outputs and may miss nuances, context, or important details.
              Always review the original paper before citing or relying on these results.
            </p>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-20 px-4 sm:px-6 border-t border-slate-800/50">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to Get Started?</h2>
          <p className="text-slate-400 mb-8">Create your free account and start analysing papers today.</p>
          <Link to="/register" className="btn btn-primary btn-lg">
            Create Free Account
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-slate-800/50 py-6 px-4 text-center text-slate-600 text-sm">
        <p>ResearchLens — Final Year Project · Academic Research Summarizer</p>
        <p className="mt-1 text-xs">
          NLP outputs are machine-generated estimates. Not a substitute for professional review.
        </p>
      </footer>
    </div>
  )
}
