// src/App.jsx
// ────────────
// Root application component.
// Wraps everything in AuthProvider and defines all routes.
// Protected routes redirect to /login if unauthenticated.

import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'

// Pages
import LandingPage    from './pages/LandingPage'
import LoginPage      from './pages/LoginPage'
import RegisterPage   from './pages/RegisterPage'
import DashboardPage  from './pages/DashboardPage'
import UploadPage     from './pages/UploadPage'
import AnalysisPage   from './pages/AnalysisPage'
import LibraryPage    from './pages/LibraryPage'
import SettingsPage   from './pages/SettingsPage'

// Layout
import AppLayout from './layouts/AppLayout'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="spinner w-8 h-8" />
    </div>
  )
  if (!user) return <Navigate to="/login" replace />
  return children
}

function GuestOnly({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (user) return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login"    element={<GuestOnly><LoginPage /></GuestOnly>} />
        <Route path="/register" element={<GuestOnly><RegisterPage /></GuestOnly>} />

        {/* Protected – wrapped in sidebar layout */}
        <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
          <Route path="/dashboard"            element={<DashboardPage />} />
          <Route path="/upload"               element={<UploadPage />} />
          <Route path="/analyses/:analysisId" element={<AnalysisPage />} />
          <Route path="/library"              element={<LibraryPage />} />
          <Route path="/settings"             element={<SettingsPage />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
