import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import AnalysisPage from '../pages/AnalysisPage'
import { analysesApi } from '../services/api'

vi.mock('../services/api', () => ({
  analysesApi: {
    get: vi.fn(),
    exportTxt: vi.fn(),
    exportPdf: vi.fn(),
  },
}))

const MOCK_ANALYSIS = {
  _id: 'test-123',
  title: 'Attention Is All You Need',
  created_at: '2026-03-15T10:00:00Z',
  summary_type: 'medium',
  processing_status: 'success',
  summary_text: 'This paper proposes the Transformer architecture based on attention mechanisms.',
  concise_summary: 'We propose the Transformer model.',
  medium_summary: 'This paper proposes the Transformer architecture based on attention mechanisms.',
  detailed_summary: 'This paper proposes the Transformer architecture based on attention mechanisms. It outperforms recurrent models.',
  statistics: {
    word_count: 4500,
    character_count: 28000,
    sentence_count: 210,
    paragraph_count: 35,
    estimated_reading_time_minutes: 22.5,
    summary_word_count: 350,
    summary_to_source_ratio: 0.08,
    words_per_minute_assumption: 200,
  },
  key_phrases: [
    { rank: 1, phrase: 'transformer architecture', score: 0.95 },
    { rank: 2, phrase: 'multi-head attention', score: 0.88 },
  ],
  detected_sections: [
    { name: 'Abstract', word_count: 220, start_char: 0, end_char: 1200 },
    { name: 'Introduction', word_count: 850, start_char: 1201, end_char: 5500 },
  ],
  section_summaries: [
    {
      name: 'Abstract',
      summary_text: 'The Transformer is a novel architecture based solely on attention.',
      word_count: 220,
      start_char: 0,
      end_char: 1200,
      sentences: [
        { index: 0, text: 'The Transformer is a novel architecture based solely on attention.', score: 0.45, start_char: 0, end_char: 66, section: 'Abstract' },
      ],
    },
    {
      name: 'Introduction',
      summary_text: 'Recurrent models compute hidden states sequentially, which impedes parallelization.',
      word_count: 850,
      start_char: 1201,
      end_char: 5500,
      sentences: [
        { index: 5, text: 'Recurrent models compute hidden states sequentially.', score: 0.38, start_char: 1201, end_char: 1253, section: 'Introduction' },
      ],
    },
  ],
  summary_sentences_with_evidence: [
    {
      index: 0,
      text: 'This paper proposes the Transformer architecture based on attention mechanisms.',
      score: 0.52,
      start_char: 0,
      end_char: 80,
      section: 'Abstract',
    },
  ],
  evidence_by_level: {
    concise: [
      { index: 0, text: 'We propose the Transformer model.', score: 0.6, start_char: 0, end_char: 33, section: 'Abstract' },
    ],
    medium: [
      { index: 0, text: 'This paper proposes the Transformer architecture based on attention mechanisms.', score: 0.52, start_char: 0, end_char: 80, section: 'Abstract' },
    ],
    detailed: [
      { index: 0, text: 'This paper proposes the Transformer architecture based on attention mechanisms.', score: 0.52, start_char: 0, end_char: 80, section: 'Abstract' },
      { index: 1, text: 'It outperforms recurrent models.', score: 0.48, start_char: 81, end_char: 113, section: 'Abstract' },
    ],
  },
  methodology_findings: {
    total_found: 4,
    total_dimensions: 9,
    dimensions: [
      {
        dimension: 'objectives',
        label: 'Primary Objectives & Contributions',
        found: true,
        summary: 'We propose the Transformer, a model architecture eschewing recurrence.',
        evidence: 'We propose the Transformer, a model architecture eschewing recurrence.',
        section: 'Abstract',
      },
      {
        dimension: 'methodology',
        label: 'Proposed Methodology & Architecture',
        found: true,
        summary: 'The model relies entirely on self-attention to compute input and output representations.',
        evidence: 'The model relies entirely on self-attention.',
        section: 'Abstract',
      },
      {
        dimension: 'main_findings',
        label: 'Main Findings & Quantitative Results',
        found: true,
        summary: 'Achieves 28.4 BLEU on the WMT 2014 English-to-German translation task.',
        evidence: 'Achieves 28.4 BLEU on the WMT 2014 English-to-German task.',
        section: 'Results',
      },
      {
        dimension: 'limitations',
        label: 'Limitations & Constraints',
        found: false,
        summary: 'Not explicitly stated in the document',
        evidence: null,
        section: null,
      },
    ],
  },
  warnings: [],
}

describe('AnalysisPage Stage 1 Features', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    analysesApi.get.mockResolvedValue({ data: MOCK_ANALYSIS })
  })

  it('renders the analysis title, quick stats, and navigation tabs', async () => {
    render(
      <MemoryRouter initialEntries={['/analyses/test-123']}>
        <Routes>
          <Route path="/analyses/:analysisId" element={<AnalysisPage />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Attention Is All You Need')).toBeInTheDocument()
    })

    expect(screen.getByText('Overview')).toBeInTheDocument()
    expect(screen.getByText(/Summary & Evidence/i)).toBeInTheDocument()
    expect(screen.getByText(/Findings & Methods/i)).toBeInTheDocument()
    expect(screen.getByText(/Section Summaries/i)).toBeInTheDocument()
    expect(screen.getByText('Key Phrases')).toBeInTheDocument()
  })

  it('renders research methodology and findings with verified evidence', async () => {
    render(
      <MemoryRouter initialEntries={['/analyses/test-123']}>
        <Routes>
          <Route path="/analyses/:analysisId" element={<AnalysisPage />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Attention Is All You Need')).toBeInTheDocument()
    })

    // Click Findings & Methods tab
    const methTab = screen.getByRole('button', { name: /Findings & Methods/i })
    fireEvent.click(methTab)

    expect(screen.getByText(/Research Methodology & Empirical Findings/i)).toBeInTheDocument()
    expect(screen.getByText('Primary Objectives & Contributions')).toBeInTheDocument()
    expect(screen.getByText('Proposed Methodology & Architecture')).toBeInTheDocument()
    expect(screen.getByText('Main Findings & Quantitative Results')).toBeInTheDocument()
    expect(screen.getAllByText(/Achieves 28.4 BLEU/i).length).toBeGreaterThanOrEqual(1)
  })

  it('renders section-wise intelligent summaries with word counts', async () => {
    render(
      <MemoryRouter initialEntries={['/analyses/test-123']}>
        <Routes>
          <Route path="/analyses/:analysisId" element={<AnalysisPage />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Attention Is All You Need')).toBeInTheDocument()
    })

    // Click Section Summaries tab
    const sectionsTab = screen.getByRole('button', { name: /Section Summaries/i })
    fireEvent.click(sectionsTab)

    expect(screen.getByText(/Section-Wise Intelligent Summaries/i)).toBeInTheDocument()
    expect(screen.getByText('The Transformer is a novel architecture based solely on attention.')).toBeInTheDocument()
    expect(screen.getByText(/220 words/i)).toBeInTheDocument()
  })
})
