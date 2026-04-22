"""
main.py — CLI interactiva para el asistente de trabajo.

Ejecución (desde la raíz del proyecto):
    python -m work.main

Coloca tus CVs en work/inputs/cv/ antes de usar cualquier skill.
"""

import sys
from pathlib import Path

# Permite ejecutar directamente (botón play) o como módulo (python -m work.main)
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from work.chain_factory import (
    build_cv_qa_chain,
    build_cv_updater_chain,
    build_linkedin_optimizer_chain,
    build_recruiter_reply_chain,
    invalidate_cv_cache,
)
from work.cv_indexer import build_cv_vectorstore
from work.cv_writer import write_cv_docx
from work.sheets_loader import load_sheet_as_text

OUTPUTS_PATH = Path(__file__).resolve().parent / "outputs"
OUTPUTS_PATH.mkdir(exist_ok=True)


# ── Helpers de UI ──────────────────────────────────────────────────────────────

def _sep() -> None:
    print("\n" + "─" * 60)


def _read_multiline(prompt: str) -> str:
    """Lee texto multilínea del usuario. Termina escribiendo 'FIN' en una línea sola."""
    print(prompt)
    print("(Escribe FIN en una línea sola y pulsa Enter para terminar)\n")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "FIN":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def _save_text(filename: str, content: str) -> None:
    out = OUTPUTS_PATH / filename
    out.write_text(content, encoding="utf-8")
    print(f"Guardado en: {out}")


# ── Skills ─────────────────────────────────────────────────────────────────────

def run_index_cv() -> None:
    print("\nReconstruyendo índice de CVs (esto tarda un momento si usas embeddings remotos)...")
    build_cv_vectorstore(force_rebuild=True)
    invalidate_cv_cache()
    print("Listo. CVs indexados correctamente.")


def run_cv_qa() -> None:
    _sep()
    print("  CV Q&A — Pregunta lo que quieras sobre tu perfil")
    _sep()
    chain = build_cv_qa_chain()
    while True:
        question = input("\nPregunta (o 'salir'): ").strip()
        if question.lower() in ("salir", "exit", ""):
            break
        result = chain.invoke({"question": question})
        print(f"\n{result.content}")


def run_recruiter_reply(projects_context: str) -> None:
    _sep()
    print("  Recruiter Reply — Genera una respuesta para un mensaje de LinkedIn")
    _sep()

    recruiter_message = _read_multiline("Pega el mensaje del recruiter:")
    if not recruiter_message:
        print("Mensaje vacío, cancelando.")
        return

    print("\nReglas especiales para esta respuesta (Enter para usar las por defecto):")
    user_rules = input("> ").strip()

    chain = build_recruiter_reply_chain()
    result = chain.invoke({
        "recruiter_message": recruiter_message,
        "projects_context": projects_context,
        "user_rules": user_rules,
    })

    _sep()
    print("  RESPUESTA GENERADA")
    _sep()
    print(result.reply)
    _sep()
    print(f"Tono: {result.tone}")
    print(f"Puntos destacados: {', '.join(result.key_points)}")

    if input("\n¿Guardar respuesta en outputs/? [s/N]: ").strip().lower() in ("s", "si", "sí", "y"):
        _save_text("recruiter_reply.txt", result.reply)


def run_linkedin_optimizer() -> None:
    _sep()
    print("  LinkedIn Optimizer — Análisis y mejoras orientadas a ATS y recruiters")
    _sep()

    linkedin_profile = _read_multiline("Pega el contenido de tu perfil de LinkedIn:")
    if not linkedin_profile:
        print("Perfil vacío, cancelando.")
        return

    chain = build_linkedin_optimizer_chain()
    result = chain.invoke({"linkedin_profile": linkedin_profile})

    _sep()
    print("  ANÁLISIS Y OPTIMIZACIÓN DE LINKEDIN")
    _sep()
    print(f"Puntuación actual estimada: {result.estimated_score}/10")
    print(f"Keywords faltantes: {', '.join(result.missing_keywords)}")

    print("\nMejoras por sección:")
    for imp in result.improvements:
        print(f"\n  [{imp.section.upper()}]")
        preview = imp.suggested_text[:300]
        if len(imp.suggested_text) > 300:
            preview += "..."
        print(f"  Texto sugerido:\n    {preview}")
        print(f"  Por qué: {imp.reason}")
        if imp.ats_keywords:
            print(f"  Keywords ATS: {', '.join(imp.ats_keywords)}")

    print("\nConsejos generales:")
    for tip in result.general_tips:
        print(f"  • {tip}")

    if input("\n¿Guardar análisis completo en outputs/? [s/N]: ").strip().lower() in ("s", "si", "sí", "y"):
        lines = [
            f"PUNTUACIÓN: {result.estimated_score}/10",
            f"KEYWORDS FALTANTES: {', '.join(result.missing_keywords)}",
            "",
            "MEJORAS POR SECCIÓN:",
        ]
        for imp in result.improvements:
            lines += [
                f"\n[{imp.section.upper()}]",
                f"Texto sugerido:\n{imp.suggested_text}",
                f"Razón: {imp.reason}",
                f"Keywords ATS: {', '.join(imp.ats_keywords)}",
            ]
        lines += ["", "CONSEJOS GENERALES:"] + [f"• {t}" for t in result.general_tips]
        _save_text("linkedin_optimization.txt", "\n".join(lines))


def run_cv_updater(projects_context: str) -> None:
    _sep()
    print("  CV Updater — Actualiza tu CV y expórtalo a Word (.docx)")
    _sep()

    update_instructions = _read_multiline(
        "Describe qué quieres actualizar (proyectos nuevos, logros, skills, etc.):"
    )
    if not update_instructions:
        print("Instrucciones vacías, cancelando.")
        return

    print("\nGenerando CV actualizado (puede tardar unos segundos)...")
    chain = build_cv_updater_chain()
    cv_doc = chain.invoke({
        "update_instructions": update_instructions,
        "projects_context": projects_context,
    })

    lang_label = cv_doc.language.upper()
    output_file = OUTPUTS_PATH / f"cv_updated_{lang_label}.docx"
    write_cv_docx(cv_doc, output_file)
    print(f"\nCV de {cv_doc.contact.name} guardado en: {output_file}")


def run_load_sheet() -> str:
    _sep()
    print("  Google Sheets — Carga proyectos y tareas desde tu hoja de cálculo")
    _sep()
    print("Pega la URL de tu Google Sheet pública (Anyone with the link can view):")
    url = input("> ").strip()
    if not url:
        print("URL vacía, cancelando.")
        return ""
    try:
        content = load_sheet_as_text(url)
        row_count = len(content.splitlines()) - 2  # subtract header + separator
        print(f"\nHoja cargada correctamente ({row_count} filas de datos).")
        _sep()
        print("Preview (primeras 5 filas):")
        for line in content.splitlines()[:7]:
            print(f"  {line}")
        return content
    except Exception as e:
        print(f"\nError cargando la hoja: {e}")
        return ""


# ── Menú principal ─────────────────────────────────────────────────────────────

def _menu(projects_loaded: bool) -> None:
    _sep()
    print("  ASISTENTE DE TRABAJO")
    _sep()
    print("  1. Indexar / actualizar CVs")
    print("  2. Preguntar sobre mi CV")
    print("  3. Responder mensaje de recruiter")
    print("  4. Optimizar perfil de LinkedIn")
    print("  5. Actualizar CV y exportar a Word (.docx)")
    sheet_status = "✓ cargada" if projects_loaded else "no cargada"
    print(f"  6. Cargar proyectos desde Google Sheets  [{sheet_status}]")
    print("  0. Salir")
    _sep()


def main() -> None:
    projects_context = ""

    print("\nBienvenido al Asistente de Trabajo.")
    print("Consejo: coloca tus CVs en work/inputs/cv/ y ejecuta la opción 1 antes de empezar.")

    while True:
        _menu(projects_loaded=bool(projects_context))
        choice = input("Opción: ").strip()

        if choice == "0":
            print("Hasta luego.")
            break
        elif choice == "1":
            run_index_cv()
        elif choice == "2":
            run_cv_qa()
        elif choice == "3":
            run_recruiter_reply(projects_context)
        elif choice == "4":
            run_linkedin_optimizer()
        elif choice == "5":
            run_cv_updater(projects_context)
        elif choice == "6":
            result = run_load_sheet()
            if result:
                projects_context = result
        else:
            print("Opción no válida, elige entre 0 y 6.")


if __name__ == "__main__":
    main()
