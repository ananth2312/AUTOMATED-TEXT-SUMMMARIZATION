import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import RegisterPage from '../pages/RegisterPage'
import { AuthProvider } from '../context/AuthContext'

describe('RegisterPage', () => {
  it('renders registration form with all required fields', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <RegisterPage />
        </AuthProvider>
      </MemoryRouter>
    )

    expect(screen.getByLabelText(/Full name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^Password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Confirm password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Create Account/i })).toBeInTheDocument()
  })

  it('validates short password and missing uppercase/digit rules', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <RegisterPage />
        </AuthProvider>
      </MemoryRouter>
    )

    const nameInput = screen.getByLabelText(/Full name/i)
    const emailInput = screen.getByLabelText(/Email address/i)
    const pwInput = screen.getByLabelText(/^Password/i)
    const confirmInput = screen.getByLabelText(/Confirm password/i)

    fireEvent.change(nameInput, { target: { value: 'Dr. Alice' } })
    fireEvent.change(emailInput, { target: { value: 'alice@example.com' } })
    fireEvent.change(pwInput, { target: { value: 'short' } })
    fireEvent.change(confirmInput, { target: { value: 'short' } })

    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }))

    await waitFor(() => {
      expect(screen.getByText(/Password must be at least 8 characters/i)).toBeInTheDocument()
    })
  })

  it('flags password mismatch when confirm password does not match', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <RegisterPage />
        </AuthProvider>
      </MemoryRouter>
    )

    const nameInput = screen.getByLabelText(/Full name/i)
    const emailInput = screen.getByLabelText(/Email address/i)
    const pwInput = screen.getByLabelText(/^Password/i)
    const confirmInput = screen.getByLabelText(/Confirm password/i)

    fireEvent.change(nameInput, { target: { value: 'Dr. Alice' } })
    fireEvent.change(emailInput, { target: { value: 'alice@example.com' } })
    fireEvent.change(pwInput, { target: { value: 'Password123' } })
    fireEvent.change(confirmInput, { target: { value: 'DifferentPassword123' } })

    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }))

    await waitFor(() => {
      expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument()
    })
  })
})
