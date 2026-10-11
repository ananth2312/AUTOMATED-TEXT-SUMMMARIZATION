import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'
import LoginPage from '../pages/LoginPage'
import { AuthProvider } from '../context/AuthContext'

describe('LoginPage', () => {
  it('renders login form with inputs and submit button', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>
    )

    expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument()
  })

  it('validates empty inputs on submit', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: /Sign In/i }))

    await waitFor(() => {
      expect(screen.getByText(/Email is required/i)).toBeInTheDocument()
      expect(screen.getByText(/Password is required/i)).toBeInTheDocument()
    })
  })

  it('allows typing into email and password inputs', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>
    )

    const emailInput = screen.getByLabelText(/Email address/i)
    const pwInput = screen.getByLabelText(/Password/i)

    fireEvent.change(emailInput, { target: { value: 'user@example.com' } })
    fireEvent.change(pwInput, { target: { value: 'Secret123' } })

    expect(emailInput.value).toBe('user@example.com')
    expect(pwInput.value).toBe('Secret123')
  })
})
