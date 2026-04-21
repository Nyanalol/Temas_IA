"""
models.py — Modelos Pydantic para todas las skills del asistente de trabajo.
"""

from pydantic import BaseModel, Field


# ── Recruiter Reply ────────────────────────────────────────────────────────────

class RecruiterReply(BaseModel):
    reply: str = Field(
        description="Texto completo de la respuesta al recruiter, lista para copiar y pegar en LinkedIn"
    )
    tone: str = Field(
        description="Tono de la respuesta: professional | enthusiastic | neutral | polite_decline"
    )
    key_points: list[str] = Field(
        description="Puntos clave del perfil del candidato que se destacan en la respuesta"
    )


# ── LinkedIn Optimization ──────────────────────────────────────────────────────

class SectionImprovement(BaseModel):
    section: str = Field(
        description="Nombre de la sección: headline | about | experience | skills | certifications | etc."
    )
    suggested_text: str = Field(description="Texto mejorado completo para esa sección")
    reason: str = Field(description="Por qué esta versión es mejor para ATS y recruiters")
    ats_keywords: list[str] = Field(
        default_factory=list,
        description="Keywords ATS relevantes que se incorporan en la mejora",
    )


class LinkedInOptimization(BaseModel):
    estimated_score: int = Field(description="Puntuación estimada del perfil actual del 1 al 10")
    missing_keywords: list[str] = Field(
        description="Keywords importantes del sector que faltan en el perfil actual"
    )
    improvements: list[SectionImprovement] = Field(
        description="Lista de mejoras concretas por sección"
    )
    general_tips: list[str] = Field(
        description="Consejos generales adicionales de visibilidad y networking"
    )


# ── CV Document (para actualización y exportación a Word) ─────────────────────

class ContactInfo(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None


class ExperienceEntry(BaseModel):
    company: str
    role: str
    period: str
    location: str | None = None
    achievements: list[str] = Field(
        description="Lista de logros y responsabilidades en formato bullet, con métricas cuando sea posible"
    )


class EducationEntry(BaseModel):
    institution: str
    degree: str
    period: str
    details: str | None = None


class CVDocument(BaseModel):
    language: str = Field(description="Idioma del CV: es | en")
    contact: ContactInfo
    summary: str = Field(description="Resumen/perfil profesional (3-5 frases)")
    experience: list[ExperienceEntry]
    education: list[EducationEntry]
    skills: list[str] = Field(description="Lista de habilidades técnicas y herramientas")
    languages: list[str] = Field(
        description="Idiomas con nivel, p. ej. 'Español (nativo)', 'Inglés (C1 – Advanced)'"
    )
    certifications: list[str] = Field(default_factory=list)
