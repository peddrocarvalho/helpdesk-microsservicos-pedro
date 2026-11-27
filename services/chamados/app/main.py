
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import httpx
import jwt
from fastapi import (
    FastAPI,
    Depends,
    Request,
    HTTPException,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import JWT_SEGREDO, USUARIOS_URL, INVENTARIO_URL
from app.database import Base, engine, get_db
from app.modelos import Chamado, Comentario, Notificacao
from app.esquemas import (
    ChamadoCriar,
    ChamadoSaida,
    Atribuicao,
    MudancaStatus,
    ComentarioCriar,
    ComentarioSaida,
    Painel,
    NotificacaoSaida,
)


HORAS_SLA = {
    "critica": 4,
    "alta": 8,
    "media": 24,
    "baixa": 72,
}

TRANSICOES = {
    "aberto": {"em_atendimento"},
    "em_atendimento": {"resolvido"},
    "resolvido": {"fechado", "em_atendimento"},
    "fechado": set(),
}

EQUIPE = ("tecnico", "admin")

esquema = HTTPBearer(auto_error=False)


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="MicrosserviÃ§o de Chamados",
    description="Gerenciamento de chamados, SLA, comentÃ¡rios e notificaÃ§Ãµes.",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)


def usuario_atual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(esquema),
):
    if credenciais is None:
        raise HTTPException(401, "FaÃ§a login para continuar.")

    authorization = f"{credenciais.scheme} {credenciais.credentials}"
    token = credenciais.credentials

    if not JWT_SEGREDO:
        raise HTTPException(500, "JWT_SEGREDO nÃ£o configurado.")

    try:
        payload = jwt.decode(
            token,
            JWT_SEGREDO,
            algorithms=["HS256"],
            issuer="helpdesk-ti",
            options={
                "require": ["exp", "iat", "sub", "iss", "perfil"]
            },
        )

        usuario_id = int(payload["sub"])

    except Exception:
        raise HTTPException(401, "Token invÃ¡lido ou expirado.")

    try:
        resposta = httpx.get(
            f"{USUARIOS_URL}/usuarios/{usuario_id}",
            headers={"Authorization": authorization},
            timeout=5,
        )
        resposta.raise_for_status()
        dados = resposta.json()

    except httpx.HTTPStatusError as erro:
        if erro.response.status_code in (401, 403, 404):
            raise HTTPException(401, "UsuÃ¡rio nÃ£o autorizado.")

        raise HTTPException(503, "ServiÃ§o de UsuÃ¡rios indisponÃ­vel.")

    except (httpx.RequestError, ValueError):
        raise HTTPException(
            503,
            "NÃ£o foi possÃ­vel consultar o serviÃ§o de UsuÃ¡rios.",
        )

    perfil = dados.get("perfil") or payload.get("perfil")

    if not perfil:
        raise HTTPException(401, "Perfil do usuÃ¡rio nÃ£o identificado.")

    return {
        "id": usuario_id,
        "perfil": perfil,
    }


def exigir_equipe(usuario):
    if usuario["perfil"] not in EQUIPE:
        raise HTTPException(
            403,
            "Apenas tÃ©cnicos e administradores podem realizar esta aÃ§Ã£o.",
        )


def notificar(db, tipo, destinatario_id, mensagem):
    aviso = Notificacao(
        tipo=tipo,
        destinatario_id=destinatario_id,
        mensagem=mensagem,
        criada_em=datetime.now(),
    )

    db.add(aviso)
    db.commit()
    db.refresh(aviso)

    return aviso


def buscar_chamado(db, chamado_id):
    return db.scalar(
        select(Chamado)
        .options(selectinload(Chamado.comentarios))
        .where(Chamado.id == chamado_id)
    )


def obter_visivel(db, chamado_id, usuario):
    chamado = buscar_chamado(db, chamado_id)

    if chamado is None or (
        usuario["perfil"] not in EQUIPE
        and chamado.solicitante_id != usuario["id"]
    ):
        raise HTTPException(
            404,
            f"Chamado {chamado_id} nÃ£o encontrado.",
        )

    return chamado


def validar_tecnico(tecnico_id, authorization):
    try:
        resposta = httpx.get(
            f"{USUARIOS_URL}/usuarios/{tecnico_id}",
            headers={"Authorization": authorization},
            timeout=5,
        )
        resposta.raise_for_status()
        dados = resposta.json()

    except httpx.HTTPStatusError as erro:
        if erro.response.status_code == 404:
            raise HTTPException(404, "TÃ©cnico nÃ£o encontrado.")

        raise HTTPException(
            503,
            "Falha ao consultar serviÃ§o de UsuÃ¡rios.",
        )

    except httpx.RequestError:
        raise HTTPException(
            503,
            "ServiÃ§o de UsuÃ¡rios indisponÃ­vel.",
        )

    if dados.get("perfil") not in EQUIPE:
        raise HTTPException(
            400,
            "O usuÃ¡rio informado nÃ£o Ã© tÃ©cnico nem administrador.",
        )


def validar_ativo(ativo_id, authorization):
    try:
        resposta = httpx.get(
            f"{INVENTARIO_URL}/ativos/{ativo_id}",
            headers={"Authorization": authorization},
            timeout=5,
        )
        resposta.raise_for_status()

    except httpx.HTTPStatusError as erro:
        if erro.response.status_code == 404:
            raise HTTPException(
                404,
                "Ativo nÃ£o encontrado no InventÃ¡rio.",
            )

        raise HTTPException(
            503,
            "Falha ao consultar serviÃ§o de InventÃ¡rio.",
        )

    except httpx.RequestError:
        raise HTTPException(
            503,
            "ServiÃ§o de InventÃ¡rio indisponÃ­vel.",
        )


@app.get("/health")
@app.get("/saude")
def health():
    return {
        "servico": "chamados",
        "status": "online",
    }


@app.post(
    "/chamados",
    response_model=ChamadoSaida,
    status_code=201,
)
def abrir_chamado(
    dados: ChamadoCriar,
    request: Request,
    usuario=Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    authorization = request.headers.get("Authorization", "")

    if dados.ativo_id is not None:
        validar_ativo(dados.ativo_id, authorization)

    agora = datetime.now()

    chamado = Chamado(
        titulo=dados.titulo,
        descricao=dados.descricao,
        prioridade=dados.prioridade,
        status="aberto",
        solicitante_id=usuario["id"],
        tecnico_id=None,
        ativo_id=dados.ativo_id,
        criado_em=agora,
        prazo_sla=agora + timedelta(
            hours=HORAS_SLA[dados.prioridade]
        ),
    )

    db.add(chamado)
    db.commit()
    db.refresh(chamado)

    notificar(
        db,
        "ChamadoAberto",
        usuario["id"],
        f"Seu chamado #{chamado.id} foi aberto. Prazo: "
        f"{chamado.prazo_sla:%d/%m %H:%M}.",
    )

    return buscar_chamado(db, chamado.id)


@app.get(
    "/chamados",
    response_model=list[ChamadoSaida],
)
def listar_chamados(
    status: str | None = None,
    tecnico_id: int | None = None,
    usuario=Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    consulta = (
        select(Chamado)
        .options(selectinload(Chamado.comentarios))
        .order_by(Chamado.id)
    )

    if usuario["perfil"] not in EQUIPE:
        consulta = consulta.where(
            Chamado.solicitante_id == usuario["id"]
        )

    if status:
        consulta = consulta.where(Chamado.status == status)

    if tecnico_id:
        consulta = consulta.where(
            Chamado.tecnico_id == tecnico_id
        )

    return list(db.scalars(consulta).unique())


@app.get(
    "/chamados/painel",
    response_model=Painel,
)
def painel(
    usuario=Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    consulta = select(Chamado)

    if usuario["perfil"] not in EQUIPE:
        consulta = consulta.where(
            Chamado.solicitante_id == usuario["id"]
        )

    chamados = list(db.scalars(consulta))
    agora = datetime.now()

    atrasados = sum(
        1
        for chamado in chamados
        if chamado.status in ("aberto", "em_atendimento")
        and chamado.prazo_sla < agora
    )

    return {
        "total": len(chamados),
        "por_status": dict(
            Counter(chamado.status for chamado in chamados)
        ),
        "atrasados": atrasados,
    }


@app.get(
    "/chamados/{chamado_id}",
    response_model=ChamadoSaida,
)
def obter_chamado(
    chamado_id: int,
    usuario=Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    return obter_visivel(db, chamado_id, usuario)


@app.patch(
    "/chamados/{chamado_id}/atribuir",
    response_model=ChamadoSaida,
)
def atribuir_chamado(
    chamado_id: int,
    dados: Atribuicao,
    request: Request,
    usuario=Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    authorization = request.headers.get("Authorization", "")

    exigir_equipe(usuario)
    chamado = obter_visivel(db, chamado_id, usuario)

    if chamado.status in ("resolvido", "fechado"):
        raise HTTPException(
            400,
            "NÃ£o Ã© possÃ­vel atribuir chamado resolvido ou fechado.",
        )

    validar_tecnico(dados.tecnico_id, authorization)

    chamado.tecnico_id = dados.tecnico_id

    if chamado.status == "aberto":
        chamado.status = "em_atendimento"

    db.commit()
    db.refresh(chamado)

    notificar(
        db,
        "ChamadoAtribuido",
        dados.tecnico_id,
        f"O chamado #{chamado.id} foi atribuÃ­do a vocÃª.",
    )

    return buscar_chamado(db, chamado.id)


@app.patch(
    "/chamados/{chamado_id}/status",
    response_model=ChamadoSaida,
)
def mudar_status(
    chamado_id: int,
    dados: MudancaStatus,
    usuario=Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    chamado = obter_visivel(db, chamado_id, usuario)
    novo_status = dados.status

    pode_solicitante = (
        chamado.status == "resolvido"
        and novo_status in ("fechado", "em_atendimento")
    )

    if usuario["perfil"] not in EQUIPE and not pode_solicitante:
        raise HTTPException(
            403,
            "VocÃª nÃ£o pode mudar o status deste chamado.",
        )

    if novo_status not in TRANSICOES[chamado.status]:
        raise HTTPException(
            400,
            f"NÃ£o Ã© possÃ­vel ir de '{chamado.status}' "
            f"para '{novo_status}'.",
        )

    if novo_status == "em_atendimento" and chamado.tecnico_id is None:
        raise HTTPException(
            400,
            "Atribua um tÃ©cnico antes de iniciar o atendimento.",
        )

    chamado.status = novo_status

    db.commit()
    db.refresh(chamado)

    if novo_status == "resolvido":
        notificar(
            db,
            "ChamadoResolvido",
            chamado.solicitante_id,
            f"Seu chamado #{chamado.id} foi resolvido. "
            "Confirme se estÃ¡ tudo certo.",
        )

    return buscar_chamado(db, chamado.id)


@app.post(
    "/chamados/{chamado_id}/comentarios",
    response_model=ComentarioSaida,
    status_code=201,
)
def comentar(
    chamado_id: int,
    dados: ComentarioCriar,
    usuario=Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    chamado = obter_visivel(db, chamado_id, usuario)

    if chamado.status == "fechado":
        raise HTTPException(
            400,
            "Chamados fechados nÃ£o recebem comentÃ¡rios.",
        )

    comentario = Comentario(
        chamado_id=chamado.id,
        autor_id=usuario["id"],
        texto=dados.texto,
        criado_em=datetime.now(),
    )

    db.add(comentario)
    db.commit()
    db.refresh(comentario)

    return comentario


@app.get(
    "/notificacoes",
    response_model=list[NotificacaoSaida],
)
def minhas_notificacoes(
    usuario=Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    consulta = (
        select(Notificacao)
        .where(
            Notificacao.destinatario_id == usuario["id"]
        )
        .order_by(Notificacao.id)
    )

    return list(db.scalars(consulta))

