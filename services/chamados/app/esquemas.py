from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Prioridade = Literal["baixa", "media", "alta", "critica"]
Status = Literal["aberto", "em_atendimento", "resolvido", "fechado"]

class ChamadoCriar(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    titulo: str = Field(min_length=3, max_length=120)
    descricao: str = Field(min_length=3, max_length=2000)
    prioridade: Prioridade
    ativo_id: int | None = Field(default=None, gt=0)

class Atribuicao(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tecnico_id: int = Field(gt=0)

class MudancaStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Status

class ComentarioCriar(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    texto: str = Field(min_length=1, max_length=2000)

class ComentarioSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    autor_id: int
    texto: str
    criado_em: datetime

class ChamadoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    titulo: str
    descricao: str
    prioridade: Prioridade
    status: Status
    solicitante_id: int
    tecnico_id: int | None
    ativo_id: int | None
    criado_em: datetime
    prazo_sla: datetime
    comentarios: list[ComentarioSaida] = Field(default_factory=list)

class Painel(BaseModel):
    total: int
    por_status: dict[str, int]
    atrasados: int

class NotificacaoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tipo: str
    destinatario_id: int
    mensagem: str
    criada_em: datetime
