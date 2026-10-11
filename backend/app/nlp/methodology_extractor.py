"""
app/nlp/methodology_extractor.py
─────────────────────────────────
Evidence-based research methodology and findings extractor.

Analyzes preprocessed academic text and detected sections to identify
key structured dimensions:
  1. Research Problem & Challenge
  2. Primary Objectives & Contributions
  3. Proposed Methodology & Architecture
  4. Datasets & Benchmarks
  5. Tools, Frameworks & Hardware
  6. Evaluation Metrics
  7. Main Findings & Quantitative Results
  8. Limitations & Constraints
  9. Future Work & Open Directions

Quality safeguard:
- If a dimension is not clearly supported by source text, it is marked as
  found=False with 'Not explicitly stated in the document', rather than inventing answers.
- All extracted items link directly to verbatim evidence sentences with section tags.
"""

import logging
import re
from dataclasses import asdict, dataclass
from typing import Optional

from .section_detector import Section

logger = logging.getLogger(__name__)


@dataclass
class ExtractedDimension:
    dimension: str
    label: str
    found: bool
    summary: str
    evidence: Optional[str] = None
    section: Optional[str] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None


@dataclass
class MethodologyFindingsResult:
    dimensions: list[ExtractedDimension]
    total_found: int
    total_dimensions: int

    def to_dict(self) -> dict:
        return {
            "dimensions": [asdict(d) for d in self.dimensions],
            "total_found": self.total_found,
            "total_dimensions": self.total_dimensions,
        }


# ── Dimension Definitions & Linguistic Patterns ──────────────────────────────

_DIMENSION_CONFIG = [
    {
        "id": "research_problem",
        "label": "Research Problem & Challenge",
        "target_sections": ["Abstract", "Introduction", "Literature Review", "Related Work"],
        "cue_patterns": [
            r"\b(?:address(?:es|ed)?|tackle[s]?|focus(?:es|ed)? on|investigate[s]?|deal[s]? with)\s+(?:the\s+)?(?:problem|challenge|issue|task)\s+of\b",
            r"\b(?:a\s+major\s+(?:challenge|limitation|drawback)|critical\s+bottleneck|existing\s+(?:methods|approaches|models)\s+(?:suffer|fail|struggle|lack))\b",
            r"\b(?:despite\s+(?:recent\s+)?(?:advances|progress|success),?\s+.*?(?:remains|is\s+still))\b",
            r"\b(?:the\s+fundamental\s+(?:problem|issue|question)\s+is)\b",
            r"\b(?:aims?\s+to\s+solve|motivated\s+by\s+the\s+need)\b",
        ],
    },
    {
        "id": "objectives",
        "label": "Primary Objectives & Contributions",
        "target_sections": ["Abstract", "Introduction"],
        "cue_patterns": [
            r"\b(?:we\s+(?:propose|introduce|present|develop|design|formulate)\s+(?:a|an|the|our|novel))\b",
            r"\b(?:the\s+(?:primary\s+)?(?:goal|objective|purpose|aim)\s+of\s+this\s+(?:paper|study|work|research)\s+is)\b",
            r"\b(?:in\s+this\s+(?:paper|work),?\s+we\s+(?:introduce|present|propose|demonstrate|show))\b",
            r"\b(?:our\s+(?:main\s+)?contribution(?:s)?\s+(?:is|are|include))\b",
            r"\b(?:this\s+paper\s+(?:proposes|presents|investigates|focuses\s+on))\b",
        ],
    },
    {
        "id": "methodology",
        "label": "Proposed Methodology & Architecture",
        "target_sections": ["Methodology", "Methods", "Proposed Approach", "Abstract", "Introduction"],
        "cue_patterns": [
            r"\b(?:the\s+(?:proposed|overall)\s+(?:architecture|framework|method|approach|model|system|pipeline))\b",
            r"\b(?:our\s+(?:method|model|approach|framework)\s+consists\s+of)\b",
            r"\b(?:we\s+(?:employ|utilize|apply|formulate|train|construct|adopt|leverage))\b",
            r"\b(?:is\s+based\s+on\s+(?:a|the)\s+(?:transformer|neural|deep|graph|convolutional|recurrent|probabilistic|self-attention))\b",
            r"\b(?:each\s+model\s+was\s+trained|training\s+procedure|algorithm\s+\d+|optimization\s+objective)\b",
        ],
    },
    {
        "id": "datasets",
        "label": "Datasets & Benchmarks",
        "target_sections": ["Methodology", "Results", "Experimental Setup", "Discussion", "Introduction"],
        "cue_patterns": [
            r"\b(?:evaluated|trained|tested|benchmarked|conducted\s+experiments?)\s+on\s+(?:the\s+)?([A-Z0-9][A-Za-z0-9_.-]*(?:\s+[A-Z0-9][A-Za-z0-9_.-]*)*)\b",
            r"\b(?:dataset[s]?|benchmark[s]?|corpus|corpora|samples?|cohort)\b",
            r"\b(?:collected\s+\d+[\d,]*\s+(?:samples|examples|documents|instances|images|pairs|records))\b",
            r"\b(?:ImageNet|GLUE|SQuAD|WMT|MNIST|CIFAR|COCO|CoNLL|TREC|PubMed|SemEval|BLEU|SuperGLUE|Llama|Kaggle)\b",
        ],
    },
    {
        "id": "tools_and_hardware",
        "label": "Tools, Frameworks & Hardware",
        "target_sections": ["Methodology", "Experimental Setup", "Results", "Implementation"],
        "cue_patterns": [
            r"\b(?:PyTorch|TensorFlow|Keras|JAX|Hugging\s*Face|Scikit-learn|NumPy|SciPy|spaCy|NLTK|OpenCV|Transformers)\b",
            r"\b(?:NVIDIA|GPU[s]?|TPU[s]?|CUDA|V100|A100|H100|RTX\s*\d+|Titan\s*X|Tesla)\b",
            r"\b(?:Adam(?:W)?(?:\s+optimizer)?|SGD|RMSprop|AdaGrad|learning\s+rate|weight\s+decay|batch\s+size|epochs?)\b",
            r"\b(?:implemented\s+(?:in|using)|trained\s+on\s+\d+\s+(?:GPUs?|nodes?|clusters?))\b",
        ],
    },
    {
        "id": "metrics",
        "label": "Evaluation Metrics",
        "target_sections": ["Methodology", "Results", "Experimental Setup", "Discussion"],
        "cue_patterns": [
            r"\b(?:accuracy|precision|recall|F1(?:\s*score)?|BLEU(?:-[1-4])?|ROUGE(?:-[12L])?|AUC(?:-ROC)?|ROC)\b",
            r"\b(?:perplexity|mean\s+squared\s+error|MSE|RMSE|MAE|loss|cross-entropy|latency|throughput|p-value)\b",
            r"\b(?:evaluated\s+using|measured\s+(?:by|using|in\s+terms\s+of)|metric[s]?\s+such\s+as)\b",
        ],
    },
    {
        "id": "main_findings",
        "label": "Main Findings & Quantitative Results",
        "target_sections": ["Results", "Discussion", "Conclusion", "Abstract"],
        "cue_patterns": [
            r"\b(?:outperform[s]?|surpass(?:es)?|exceed[s]?|achieve[s]?|yield[s]?|demonstrate[s]?)\s+(?:state-of-the-art|SOTA|superior|better|significant|competitive)\b",
            r"\b(?:results?\s+(?:show|demonstrate|indicate|reveal|confirm)\s+that)\b",
            r"\b(?:achieved\s+(?:an?\s+)?\d+(?:\.\d+)?%?\s+(?:accuracy|improvement|gain|BLEU|F1|score))\b",
            r"\b(?:peaked\s+at\s+\d+(?:\.\d+)?%?|improves?\s+(?:by|upon)\s+\d+(?:\.\d+)?%?)\b",
            r"\b(?:experiments?\s+show\s+that\s+.*?\s+outperform)\b",
            r"\b(?:experiments?|evaluation|results?)\s+.*?\s+(?:showed|shows?|demonstrated?|revealed?)\s+(?:an?\s+)?(?:average\s+)?.*?(?:score|accuracy|ROUGE|BLEU|F1)\b",
            r"\b(?:ROUGE|BLEU|accuracy|F1|score)\s+of\s+\d+(?:\.\d+)?\b",
            r"\b(?:demonstrate[s]?\s+that\s+.*?\s+produces?\s+competitive)\b",
            r"\b(?:processed\s+each\s+document\s+in|under\s+\d+\s+seconds)\b",
        ],
    },
    {
        "id": "limitations",
        "label": "Limitations & Constraints",
        "target_sections": ["Discussion", "Limitations", "Conclusion", "Methodology"],
        "cue_patterns": [
            r"\b(?:a\s+limitation\s+of|the\s+limitations?\s+of|is\s+limited\s+by|primary\s+limitation)\b",
            r"\b(?:drawback[s]?|bottleneck|computational\s+(?:overhead|cost|expense|complexity))\b",
            r"\b(?:one\s+caveat|fails\s+to|struggles?\s+with|trade-off\s+between|vulnerable\s+to)\b",
            r"\b(?:does\s+not\s+(?:account\s+for|scale|generalize|handle))\b",
            r"\b(?:requires?\s+(?:significant|substantial|large\s+amounts\s+of)\s+(?:memory|data|compute))\b",
        ],
    },
    {
        "id": "future_work",
        "label": "Future Directions & Open Questions",
        "target_sections": ["Future Work", "Conclusion", "Discussion"],
        "cue_patterns": [
            r"\b(?:future\s+work\s+(?:will|includes?|plans?|can|aims?))\b",
            r"\b(?:in\s+the\s+future,?\s+we\s+(?:plan|intend|hope|aim)\s+to)\b",
            r"\b(?:we\s+leave\s+.*?\s+(?:for|to)\s+future\s+work)\b",
            r"\b(?:promising\s+direction\s+for\s+future|avenue\s+for\s+future\s+(?:research|investigation))\b",
            r"\b(?:remains\s+an\s+open\s+(?:question|challenge|problem)|further\s+investigation\s+is\s+warranted)\b",
        ],
    },
]


def extract_methodology_and_findings(
    clean_text: str,
    sentences: list[str],
    sections: list[Section],
    sentence_spans: Optional[list[tuple[int, int]]] = None,
) -> MethodologyFindingsResult:
    """
    Extract 9 structured dimensions from preprocessed academic text.
    Associates evidence with source sentences, section names, and character spans.
    """
    if not clean_text or not sentences:
        empty_dims = [
            ExtractedDimension(
                dimension=cfg["id"],
                label=cfg["label"],
                found=False,
                summary="Not explicitly stated in the document",
                evidence=None,
                section=None,
            )
            for cfg in _DIMENSION_CONFIG
        ]
        return MethodologyFindingsResult(
            dimensions=empty_dims,
            total_found=0,
            total_dimensions=len(_DIMENSION_CONFIG),
        )

    # Compute sentence spans if not provided
    if not sentence_spans or len(sentence_spans) != len(sentences):
        sentence_spans = _locate_spans(clean_text, sentences)

    # Pre-map each sentence to its section and character span
    sentence_metadata = []
    for i, s in enumerate(sentences):
        span = sentence_spans[i] if i < len(sentence_spans) else (0, 0)
        sec_name = _find_section_for_offset(span[0], sections)
        sentence_metadata.append({
            "index": i,
            "text": s,
            "span": span,
            "section": sec_name,
        })

    compiled_configs = []
    for cfg in _DIMENSION_CONFIG:
        patterns = [re.compile(p, re.IGNORECASE) for p in cfg["cue_patterns"]]
        compiled_configs.append({
            "id": cfg["id"],
            "label": cfg["label"],
            "target_sections": set(cfg["target_sections"]),
            "patterns": patterns,
        })

    dimensions: list[ExtractedDimension] = []
    total_found = 0

    for cfg in compiled_configs:
        best_candidate = _find_best_candidate(sentence_metadata, cfg)

        if best_candidate is not None:
            total_found += 1
            # Clean up the summary sentence for display
            clean_summary = _format_summary(best_candidate["text"])
            dimensions.append(
                ExtractedDimension(
                    dimension=cfg["id"],
                    label=cfg["label"],
                    found=True,
                    summary=clean_summary,
                    evidence=best_candidate["text"],
                    section=best_candidate["section"],
                    char_start=best_candidate["span"][0],
                    char_end=best_candidate["span"][1],
                )
            )
        else:
            dimensions.append(
                ExtractedDimension(
                    dimension=cfg["id"],
                    label=cfg["label"],
                    found=False,
                    summary="Not explicitly stated in the document",
                    evidence=None,
                    section=None,
                    char_start=None,
                    char_end=None,
                )
            )

    return MethodologyFindingsResult(
        dimensions=dimensions,
        total_found=total_found,
        total_dimensions=len(_DIMENSION_CONFIG),
    )


# ── Internal Helpers ──────────────────────────────────────────────────────────

def _locate_spans(text: str, sentences: list[str]) -> list[tuple[int, int]]:
    """Compute character spans for each sentence in text."""
    spans: list[tuple[int, int]] = []
    curr = 0
    for s in sentences:
        pos = text.find(s, curr)
        if pos != -1:
            spans.append((pos, pos + len(s)))
            curr = pos + len(s)
        else:
            # Fallback with leading prefix
            prefix = s[:min(30, len(s))]
            pos = text.find(prefix, curr)
            if pos != -1:
                spans.append((pos, pos + len(s)))
                curr = pos + len(s)
            else:
                spans.append((0, 0))
    return spans


def _find_section_for_offset(offset: int, sections: list[Section]) -> str:
    """Find section name enclosing the character offset."""
    for s in sections:
        if s.start_char <= offset < s.end_char:
            return s.name
    return "General / Body"


def _find_best_candidate(sentence_metadata: list[dict], cfg: dict) -> Optional[dict]:
    """
    Score candidate sentences for a dimension based on pattern match count,
    section alignment, and informative sentence length.
    """
    candidates = []

    for item in sentence_metadata:
        s_text = item["text"]
        words = s_text.split()
        if len(words) < 5 or len(words) > 120:
            continue

        match_count = 0
        for pat in cfg["patterns"]:
            if pat.search(s_text):
                match_count += 1

        if match_count > 0:
            # Score bonus if in preferred section
            section_bonus = 2.5 if item["section"] in cfg["target_sections"] else 0.5
            # Preference for well-formed sentences between 10 and 45 words
            length_factor = 1.0 if 10 <= len(words) <= 45 else 0.8
            score = (match_count * 2.0 + section_bonus) * length_factor
            candidates.append((score, item))

    if not candidates:
        return None

    # Pick candidate with highest score
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def _format_summary(sentence: str) -> str:
    """Format and clean sentence for concise display."""
    s = sentence.strip()
    # Normalize internal spaces
    s = " ".join(s.split())
    # Ensure it ends with a period if missing
    if s and s[-1] not in ".!?":
        s += "."
    return s
