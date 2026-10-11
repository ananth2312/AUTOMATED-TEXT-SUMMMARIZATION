// src/pages/SettingsPage.jsx

import { useState } from 'react'
import { User, Lock, AlertTriangle, Check, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { authApi } from '../services/api'

function Section({ title, children }) {
  return (
    <div className="card p-5 space-y-4">
      <h2 className="text-base font-semibold text-white border-b border-slate-800 pb-3">{title}</h2>
      {children}
    </div>
  )
}

export default function SettingsPage() {
  const { user, updateUser, logout } = useAuth()

  const [name,    setName]    = useState(user?.name || '')
  const [saving,  setSaving]  = useState(false)

  const [pwForm, setPwForm]   = useState({ current: '', next: '', confirm: '' })
  const [pwErr,  setPwErr]    = useState({})
  const [pwLoad, setPwLoad]   = useState(false)

  const handleSaveProfile = async (e) => {
    e.preventDefault()
    if (!name.trim() || name.trim().length < 2) {
      toast.error('Name must be at least 2 characters.'); return
    }
    setSaving(true)
    try {
      await authApi.updateProfile({ name: name.trim() })
      updateUser({ name: name.trim() })
      toast.success('Profile updated.')
    } catch {
      toast.error('Could not update profile.')
    } finally { setSaving(false) }
  }

  const handleChangePassword = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!pwForm.current)                              errs.current = 'Required.'
    if (pwForm.next.length < 8)                       errs.next    = 'At least 8 characters.'
    if (!/[A-Z]/.test(pwForm.next))                   errs.next    = 'Must contain an uppercase letter.'
    if (!/\d/.test(pwForm.next))                      errs.next    = 'Must contain a digit.'
    if (pwForm.next !== pwForm.confirm)               errs.confirm = 'Passwords do not match.'
    if (Object.keys(errs).length) { setPwErr(errs); return }
    setPwErr({})
    setPwLoad(true)
    try {
      await authApi.changePassword({ current_password: pwForm.current, new_password: pwForm.next })
      toast.success('Password changed.')
      setPwForm({ current: '', next: '', confirm: '' })
    } catch (err) {
      const msg = err.response?.data?.detail || 'Password change failed.'
      toast.error(msg)
      setPwErr({ current: msg })
    } finally { setPwLoad(false) }
  }

  return (
    <div className="max-w-xl space-y-5 animate-fade-in">
      <h1 className="text-2xl font-bold text-white">Settings</h1>

      {/* Profile */}
      <Section title="Profile">
        <form onSubmit={handleSaveProfile} className="space-y-4">
          <div>
            <label className="label" htmlFor="settings-name">Name</label>
            <input id="settings-name" type="text" className="input" value={name}
              onChange={e => setName(e.target.value)} />
          </div>
          <div>
            <label className="label">Email</label>
            <input type="email" className="input opacity-60 cursor-not-allowed" value={user?.email} readOnly />
            <p className="text-xs text-slate-500 mt-1">Email cannot be changed in this version.</p>
          </div>
          <button type="submit" disabled={saving} className="btn btn-primary btn-sm">
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
            Save Changes
          </button>
        </form>
      </Section>

      {/* Password */}
      <Section title="Change Password">
        <form onSubmit={handleChangePassword} className="space-y-4">
          {[
            ['settings-pw-current', 'Current Password', 'current'],
            ['settings-pw-new',     'New Password',     'next'],
            ['settings-pw-confirm', 'Confirm New',      'confirm'],
          ].map(([id, label, key]) => (
            <div key={key}>
              <label className="label" htmlFor={id}>{label}</label>
              <input id={id} type="password" className={`input ${pwErr[key] ? 'input-error' : ''}`}
                value={pwForm[key]} onChange={e => setPwForm(f => ({ ...f, [key]: e.target.value }))} />
              {pwErr[key] && <p className="error-msg">{pwErr[key]}</p>}
            </div>
          ))}
          <button type="submit" disabled={pwLoad} className="btn btn-primary btn-sm">
            {pwLoad ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Lock className="w-3.5 h-3.5" />}
            Update Password
          </button>
        </form>
      </Section>

      {/* Data & Privacy */}
      <Section title="Privacy & Data">
        <div className="text-sm text-slate-400 space-y-2 leading-relaxed">
          <p>Your uploaded documents and analysis results are stored locally in MongoDB on your machine.</p>
          <p>No data is sent to external servers unless you configure a MongoDB Atlas connection.</p>
          <p>JWT access tokens are stored in your browser's localStorage and expire after the configured duration.</p>
          <div className="flex items-start gap-2 text-amber-300 text-xs mt-3">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            NLP outputs are machine-generated estimates. Review original papers before citing.
          </div>
        </div>
      </Section>

      {/* Logout */}
      <Section title="Account">
        <button onClick={logout} className="btn btn-danger btn-sm">Sign Out</button>
      </Section>
    </div>
  )
}
