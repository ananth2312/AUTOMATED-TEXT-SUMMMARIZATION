import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import LandingPage from '../pages/LandingPage'
import { AuthProvider } from '../context/AuthContext'

describe('LandingPage', () => {
  it('renders the main heading and hero section', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <LandingPage />
        </AuthProvider>
      </MemoryRouter>
    )

    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
    expect(screen.getByText(/Understand Research Papers/i)).toBeInTheDocument()
    expect(screen.getByText(/Faster Than Ever/i)).toBeInTheDocument()
  })

  it('displays call-to-action buttons for getting started and signing in', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <LandingPage />
        </AuthProvider>
      </MemoryRouter>
    )

    const getStartedLinks = screen.getAllByRole('link', { name: /Get Started|Start Analysing/i })
    expect(getStartedLinks.length).toBeGreaterThan(0)

    const signInLinks = screen.getAllByRole('link', { name: /Sign In/i })
    expect(signInLinks.length).toBeGreaterThan(0)
  })

  it('displays the responsible-use disclosure notice for machine-generated results', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <LandingPage />
        </AuthProvider>
      </MemoryRouter>
    )

    expect(screen.getByText(/machine-generated/i)).toBeInTheDocument()
  })
})
