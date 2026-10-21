# ADR-0003 · Filtrar la recuperación por los permisos del usuario final

- **Estado:** propuesta académica
- **Fecha:** 2026-10-13

## Contexto

El corpus institucional mezcla documentos públicos y restringidos (actas, información de personal). Un índice sin control de acceso permite que el modelo cite información que el usuario no puede ver (OWASP LLM02, LLM08).

## Decisión

Cada fragmento indexado lleva metadatos de visibilidad; la búsqueda aplica un filtro derivado del token de identidad del usuario final, no de la identidad del backend.

## Consecuencias

Mayor complejidad de ingesta y de pruebas; el vector store elegido debe soportar filtrado por metadatos. Es un criterio de selección prioritario sobre el rendimiento bruto de búsqueda.
