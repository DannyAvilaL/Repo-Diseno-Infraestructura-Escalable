"""Valida un laboratorio Azure SIN cuenta cloud, contra mock_openai_tools.py.

Reemplaza la credencial de Azure por un token falso y apunta el endpoint al
simulador. Comprueba que el código completa el bucle modelo -> herramienta ->
modelo. No valida cuotas, permisos ni comportamiento del modelo real.

Uso (desde el entorno virtual del laboratorio):
    python ../../common/mock_openai_tools.py --port 8900 &
    python ../../common/validar_agente_azure.py agente_autogen.py main
    python ../../common/validar_agente_azure.py grafo_langgraph.py graph
Semantic Kernel exige HTTPS: ver labs/VALIDACION.md.
"""
import asyncio, importlib.util, os, sys
path, func = sys.argv[1], sys.argv[2]
os.environ.update({
    "FOUNDRY_MODEL_DEPLOYMENT": "gpt-5-mini",
    "AZURE_OPENAI_ENDPOINT": os.environ.get("MOCK_ENDPOINT", "http://127.0.0.1:8900"),
    "AZURE_OPENAI_API_VERSION": "2024-10-21",
})
spec = importlib.util.spec_from_file_location("lab", path)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
mod.get_bearer_token_provider = lambda *a, **k: (lambda: "token-falso")
mod.DefaultAzureCredential = lambda *a, **k: None
if func == "graph":
    from langchain_core.messages import HumanMessage, SystemMessage
    g = mod.build_graph()
    out = g.invoke({"messages": [SystemMessage("x"), HumanMessage("¿Hasta cuándo homologaciones?")]}, config={"recursion_limit": mod.MAX_PASOS})
    print("RESULTADO:", out["messages"][-1].content)
else:
    asyncio.run(mod.main("¿Hasta cuándo se reciben homologaciones?"))
