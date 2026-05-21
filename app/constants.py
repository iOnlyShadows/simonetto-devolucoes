from enum import Enum


class StatusProcesso(str, Enum):
    DEFEITO_IDENTIFICADO = "defeito_identificado"
    SINALIZADO = "sinalizado"
    PENDENTE_RESSARCIMENTO = "pendente_ressarcimento"
    RESSARCIDO = "ressarcido"


class DestinoFisico(str, Enum):
    NA_LOJA = "na_loja"
    RECOLHIDO = "recolhido"
    ENVIADO = "enviado"
    DESCARTADO = "descartado"


class FormaRessarcimento(str, Enum):
    ABATE_NOTA = "abate_nota"
    DINHEIRO = "dinheiro"
    TROCA = "troca"
    CREDITO = "credito"
    OUTRO = "outro"


STATUS_PROCESSO_LABELS = {
    StatusProcesso.DEFEITO_IDENTIFICADO: ("Defeito identificado", "red", "⚠️"),
    StatusProcesso.SINALIZADO: ("Sinalizado", "yellow", "📨"),
    StatusProcesso.PENDENTE_RESSARCIMENTO: ("Pendente ressarcimento", "orange", "⏳"),
    StatusProcesso.RESSARCIDO: ("Ressarcido", "green", "✅"),
}

DESTINO_FISICO_LABELS = {
    DestinoFisico.NA_LOJA: ("Na loja", "grey", "📦"),
    DestinoFisico.RECOLHIDO: ("Recolhido", "blue", "🛠️"),
    DestinoFisico.ENVIADO: ("Enviado", "purple", "📤"),
    DestinoFisico.DESCARTADO: ("Descartado", "black", "🗑️"),
}

FORMA_RESSARCIMENTO_LABELS = {
    FormaRessarcimento.ABATE_NOTA: ("Abate na nota", "💸"),
    FormaRessarcimento.DINHEIRO: ("Dinheiro", "💵"),
    FormaRessarcimento.TROCA: ("Troca", "🔄"),
    FormaRessarcimento.CREDITO: ("Crédito", "🎟️"),
    FormaRessarcimento.OUTRO: ("Outro", "❓"),
}

EXTENSOES_PERMITIDAS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
TAMANHO_MAXIMO_BYTES = 20 * 1024 * 1024  # 20 MB
LIXEIRA_DIAS = 30
BACKUP_RETENCAO_DEFAULT = 30
BANNER_BACKUP_ALERTA_DIAS = 7
