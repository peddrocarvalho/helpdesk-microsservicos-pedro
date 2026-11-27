from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response

WEB = Path(__file__).resolve().parents[1] / "web"

SERVICOS = {
    "usuarios": "http://usuarios:8001",
    "inventario": "http://inventario:8002",
    "chamados": "http://chamados:8003",
}

METODOS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    app.state.cliente = httpx.AsyncClient(timeout=10.0)
    yield
    await app.state.cliente.aclose()

app = FastAPI(
    title="HelpDesk TI - API Gateway",
    version="1.0.0",
    lifespan=ciclo_de_vida,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

@app.get("/", include_in_schema=False)
def inicio():
    return FileResponse(WEB / "index.html")

@app.get("/app.js", include_in_schema=False)
def javascript():
    return FileResponse(WEB / "app.js", media_type="text/javascript")

@app.get("/estilo.css", include_in_schema=False)
def css():
    return FileResponse(WEB / "estilo.css", media_type="text/css")

@app.get("/saude")
async def saude(request: Request):
    resultados = {}

    for nome, endereco in SERVICOS.items():
        try:
            resposta = await request.app.state.cliente.get(
                f"{endereco}/saude",
                timeout=2.0,
            )
            resultados[nome] = (
                "online" if resposta.status_code == 200 else "indisponivel"
            )
        except httpx.HTTPError:
            resultados[nome] = "indisponivel"

    online = all(valor == "online" for valor in resultados.values())

    return JSONResponse(
        status_code=200 if online else 503,
        content={
            "gateway": "online",
            "status": "online" if online else "degradado",
            "servicos": resultados,
        },
    )

@app.api_route("/{path:path}", methods=METODOS)
async def encaminhar(request: Request, path: str):
    partes = path.split("/", 1)
    prefixo = partes[0]

    if prefixo in ("auth", "usuarios"):
        destino = SERVICOS["usuarios"]
    elif prefixo == "ativos":
        destino = SERVICOS["inventario"]
    elif prefixo in ("chamados", "notificacoes"):
        destino = SERVICOS["chamados"]
    else:
        return JSONResponse(
            status_code=404,
            content={"detail": "Rota não encontrada no API Gateway."},
        )

    url = f"{destino}/{path}"
    if request.url.query:
        url += f"?{request.url.query}"

    cabecalhos = {
        chave: valor
        for chave, valor in request.headers.items()
        if chave.lower() not in {
            "host", "content-length", "connection",
            "keep-alive", "proxy-authenticate",
            "proxy-authorization", "te", "trailers",
            "transfer-encoding", "upgrade",
        }
    }

    try:
        resposta = await request.app.state.cliente.request(
            method=request.method,
            url=url,
            content=await request.body(),
            headers=cabecalhos,
        )

        cabecalhos_resposta = {
            chave: valor
            for chave, valor in resposta.headers.items()
            if chave.lower() in {
                "content-type", "cache-control", "etag", "last-modified"
            }
        }

        return Response(
            content=resposta.content,
            status_code=resposta.status_code,
            headers=cabecalhos_resposta,
        )

    except (httpx.TimeoutException, httpx.ConnectError):
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Serviço temporariamente indisponível. Tente novamente."
            },
        )
