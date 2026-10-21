"""Herramientas del caso universitario, compartidas por todos los agentes cloud.

Son funciones Python puras, tipadas y de SOLO LECTURA sobre datos ficticios
locales: ningún laboratorio da a un agente permisos de escritura (OWASP
LLM06 Excessive Agency). Cada framework (ADK, Agent Framework, Strands,
Semantic Kernel, AutoGen, LangGraph) las registra con su propio mecanismo,
usando el nombre, la firma y la docstring como descripción para el modelo.
"""

from __future__ import annotations

import unicodedata

# Datos ficticios con fines académicos. No representan a ninguna institución real.
_CALENDARIO: dict[str, str] = {
    "inicio de clases": "Las clases del periodo 2027-1 inician el 1 de febrero de 2027.",
    "fin de clases": "Las clases del periodo 2027-1 terminan el 28 de mayo de 2027.",
    "inscripcion de asignaturas": "La inscripción de asignaturas es del 18 al 29 de enero de 2027.",
    "homologaciones": "Las solicitudes de homologación se reciben hasta el 15 de febrero de 2027.",
    "examenes finales": "Los exámenes finales son del 31 de mayo al 11 de junio de 2027.",
}

_REGLAMENTO: dict[str, str] = {
    "homologacion": (
        "Reglamento estudiantil (ficticio), art. 45: la homologación requiere solicitud formal, "
        "certificado de notas y contenidos programáticos; se homologan asignaturas con nota "
        "mínima de 3,5 y equivalencia de contenidos de al menos el 80 %."
    ),
    "cancelacion": (
        "Reglamento estudiantil (ficticio), art. 32: una asignatura puede cancelarse hasta la "
        "semana 8 del periodo sin afectar el promedio."
    ),
    "asistencia": (
        "Reglamento estudiantil (ficticio), art. 27: la inasistencia superior al 20 % de las "
        "horas programadas implica la pérdida de la asignatura."
    ),
}

MAX_QUERY_CHARS = 200


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.lower().split())


def _validar(consulta: str) -> str:
    if not isinstance(consulta, str) or not consulta.strip():
        raise ValueError("La consulta no puede estar vacía")
    if len(consulta) > MAX_QUERY_CHARS:
        raise ValueError(f"La consulta supera {MAX_QUERY_CHARS} caracteres")
    return _normalizar(consulta)


def consultar_calendario_academico(evento: str) -> str:
    """Consulta la fecha de un evento del calendario académico.

    Args:
        evento: evento a consultar, por ejemplo "inicio de clases",
            "inscripcion de asignaturas", "homologaciones" o "examenes finales".

    Returns:
        La fecha del evento o un mensaje indicando que no se encontró.
    """
    clave = _validar(evento)
    for nombre, valor in _CALENDARIO.items():
        if nombre in clave or clave in nombre:
            return valor
    return "No se encontró ese evento en el calendario académico. Eventos disponibles: " + ", ".join(_CALENDARIO)


def buscar_reglamento(tema: str) -> str:
    """Busca el artículo del reglamento estudiantil sobre un tema.

    Args:
        tema: tema del reglamento, por ejemplo "homologacion", "cancelacion" o "asistencia".

    Returns:
        El texto del artículo con su referencia, o un mensaje indicando que no se encontró.
    """
    clave = _validar(tema)
    for nombre, valor in _REGLAMENTO.items():
        if nombre in clave or clave in nombre:
            return valor
    return "No se encontró ese tema en el reglamento. Temas disponibles: " + ", ".join(_REGLAMENTO)


INSTRUCCIONES_ASISTENTE = (
    "Eres el asistente institucional de una universidad. Responde en español, de forma breve. "
    "Usa las herramientas para consultar el calendario académico y el reglamento, y cita el "
    "artículo cuando respondas sobre normas. Si la información no está disponible, dilo; no inventes."
)
