from dataclasses import dataclass, field, asdict
from typing import Literal

@dataclass
class Span:
    id: str
    text: str
    page: int
    bbox: list[float]  # PDF points, top-left origin, in the original page
    score: float | None = None

@dataclass
class Document:
    name: str
    sha256: str
    method: str
    pages: list[dict] = field(default_factory=list)
    paragraphs: list[Span] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

@dataclass
class Finding:
    id: str
    category: str
    critical: bool
    reference: Span | None
    revision: Span | None
    uncertainty: list[str]
    status: Literal['unreviewed', 'verified_change', 'ocr_artifact', 'unresolved'] = 'unreviewed'
    reviewer_note: str = ''

@dataclass
class Report:
    reference: Document
    revision: Document
    findings: list[Finding]
    issues: list[str]
    schema_version: str = '1.0'
    rules_version: str = '1.1'

    @property
    def requires_review(self):
        return bool(self.issues or self.findings)

    def to_dict(self):
        return {**asdict(self), 'requires_review': self.requires_review,
                'interpretation': 'Observed extraction differences; authoring changes require human verification.',
                'coordinates': 'PDF points; top-left origin; boxes refer to original pages',
                'score_note': 'OCR recognition score is not a calibrated probability.'}
