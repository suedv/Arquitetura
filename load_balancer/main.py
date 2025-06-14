from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import itertools
from dotenv import load_dotenv
from starlette.responses import Response

load_dotenv()

app = FastAPI(title="Load Balancer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVIDORES = os.getenv("SERVIDORES", "http://localhost:8002,http://localhost:8003").split(",")
servidor_atual = itertools.cycle(SERVIDORES)

@app.get("/saude")
def saude():
    return {"status": "saudavel", "servico": "load-balancer", "servidores": SERVIDORES}

@app.middleware("http")
async def proxy_to_server(request: Request, call_next):
    if request.url.path in ["/saude", "/docs", "/openapi.json"]:
        return await call_next(request)
    servidor = next(servidor_atual)
    try:
        resp = requests.request(
            method=request.method,
            url=f"{servidor}{request.url.path}",
            headers={k: v for k, v in request.headers.items() if k != 'host'},
            params=dict(request.query_params),
            data=await request.body()
        )
        return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
    except Exception:
        raise HTTPException(status_code=503, detail="Serviço indisponível") 