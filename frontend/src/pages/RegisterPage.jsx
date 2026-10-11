// src/pages/RegisterPage.jsx

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { BookOpen, Eye, EyeOff, UserPlus } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate     = useNavigate()

  const [form, setForm]       = useState({ name: '', email: '', password: '', confirm: '' })
  const [errors, setErrors]   = useState({})
  const [showPw, setShowPw]   = useState(false)
  const [loading, setLoading] = useState(false)

  const validate = () => {
    const e = {}
    if (!form.name  || form.name.trim().length < 2) e.name = 'Name must be at least 2 characters.'
    if (!form.email)                                  e.email = 'Email is required.'
    if (form.password.length < 8) {
      e.password = 'Password must be at least 8 characters.'
    } else if (!/[A-Z]/.test(form.password)) {
      e.password = 'Password must contain an uppercase letter.'
    } else if (!/\d/.test(form.password)) {
      e.password = 'Password must contain a digit.'
    }
    if (form.password !== form.confirm) e.confirm = 'Passwords do not match.'
    return e
  }

  const handleSubmit = async (ev) => {
    ev.preventDefault()
    const e = validate()
    if (Object.keys(e).length) { setErrors(e); return }
    setErrors({})
    setLoading(true)
    try {
      await register(form.name.trim(), form.email, form.password)
      toast.success('Account created! Welcome to ResearchLens.')
      navigate('/dashboard')
    } catch (err) {
      let msg = 'Registration failed.'
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail
        msg = Array.isArray(detail) ? detail.map(d => d.msg || JSON.stringify(d)).join(', ') : String(detail)
      } else if (!err.response) {
        msg = 'Cannot connect to backend server. Please make sure the backend is running on http://127.0.0.1:8000.'
      }
      toast.error(msg)
      setErrors({ form: msg })
    } finally {
      setLoading(false)
    }
  }

  const field = (id, label, type, key, placeholder, autocomplete) => (
    <div>
      <label className="label" htmlFor={id}>{label}</label>
      <div className="relative">
        <input
          id={id}
          type={type === 'password' ? (showPw ? 'text' : 'password') : type}
          autoComplete={autocomplete}
          className={`input ${type === 'password' ? 'pr-10' : ''} ${errors[key] ? 'input-error' : ''}`}
          placeholder={placeholder}
          value={form[key]}
          onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
        />
        {type === 'password' && key === 'password' && (
          <button
            type="button"
            className="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-200"
            onClick={() => setShowPw(v => !v)}
            tabIndex={-1}
          >
            {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        )}
      </div>
      {errors[key] && <p className="error-msg">{errors[key]}</p>}
    </div>
  )

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-primary-600 flex items-center justify-center mx-auto mb-4">
            <BookOpen className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Create your account</h1>
          <p className="text-slate-400 text-sm mt-1">Start analysing academic papers for free</p>
        </div>

        <div className="card p-6">
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {errors.form && (
              <div className="p-3 rounded-lg bg-red-900/30 border border-red-800/50 text-red-300 text-sm">
                {errors.form}
              </div>
            )}

            {field('reg-name',     'Full name',        'text',     'name',     'Dr. Jane Smith',       'name')}
            {field('reg-email',    'Email address',    'email',    'email',    'you@university.edu',    'email')}
            {field('reg-password', 'Password',         'password', 'password', '8+ chars, A-Z, 0-9',    'new-password')}

            <div>
              <label className="label" htmlFor="reg-confirm">Confirm password</label>
              <input
                id="reg-confirm"
                type={showPw ? 'text' : 'password'}
                autoComplete="new-password"
                className={`input ${errors.confirm ? 'input-error' : ''}`}
                placeholder="Repeat your password"
                value={form.confirm}
                onChange={e => setForm(f => ({ ...f, confirm: e.target.value }))}
              />
              {errors.confirm && <p className="error-msg">{errors.confirm}</p>}
            </div>

            <div className="text-xs text-slate-500 bg-slate-800/50 rounded-lg p-3 leading-relaxed">
              Password must be ≥ 8 characters and contain at least one uppercase letter and one digit.
            </div>

            <button
              id="register-submit"
              type="submit"
              disabled={loading}
              className="btn btn-primary w-full"
            >
              {loading ? <span className="spinner" /> : <UserPlus className="w-4 h-4" />}
              {loading ? 'Creating account…' : 'Create Account'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-slate-500 mt-5">
          Already have an account?{' '}
          <Link to="/login" className="text-primary-400 hover:text-primary-300 font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
