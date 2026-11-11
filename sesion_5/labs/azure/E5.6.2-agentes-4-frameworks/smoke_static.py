"""Prueba SIN red: construye los agentes con endpoints ficticios para validar APIs/imports/firmas."""
from __future__ import annotations

import os

os.environ.update({
    "AZURE_AI_PROJECT_ENDPOINT": "https://x.services.ai.azure.com/api/projects/p",
    "AZURE_AI_MODEL_DEPLOYMENT": "d", "AZURE_OPENAI_ENDPOINT": "https://x.openai.azure.com/",
    "AZURE_OPENAI_DEPLOYMENT": "d", "AZURE_OPENAI_MODEL": "gpt-4o", "AZURE_OPENAI_API_VERSION": "2024-10-21",
})
import a_maf
import b_semantic_kernel
import c_autogen
import d_langgraph  # noqa: E402

for name, mod in [("MAF", a_maf), ("SK", b_semantic_kernel), ("AutoGen", c_autogen), ("LangGraph", d_langgraph)]:
    agent = mod.build_agent()
    print(f"{name}: construido -> {type(agent).__name__}")
