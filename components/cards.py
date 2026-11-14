
"""
HortaSense — Componentes visuais de indicadores.

Centraliza a apresentação das medições ambientais e
dos estados hídricos, mantendo o padrão visual do projeto.

Este módulo não modifica os dados nem as regras de
classificação executadas pelo ESP32.
"""

from html import escape

import streamlit as st


# Paleta complementar da identidade visual HortaSense.
CORES = {
    "temperatura_ar": "#B77B61",
    "umidade_ar": "#366B73",
    "temperatura_solo": "#997343",
    "umidade_solo": "#537963",
    "texto": "#25312B",
    "texto_secundario": "#718078",
    "borda": "#E2E9E3",
}


# Configurações dos cartões ambientais.
INDICADORES = [
    {
        "titulo": "Temperatura do ar",
        "campo": "air_temperature_c",
        "unidade": "°C",
        "cor": CORES["temperatura_ar"],
        "icone": "🌡",
        "casas": 1,
    },
    {
        "titulo": "Umidade do ar",
        "campo": "air_humidity_pct",
        "unidade": "%",
        "cor": CORES["umidade_ar"],
        "icone": "◈",
        "casas": 1,
    },
    {
        "titulo": "Temperatura do solo",
        "campo": "soil_temperature_c",
        "unidade": "°C",
        "cor": CORES["temperatura_solo"],
        "icone": "🌡",
        "casas": 1,
    },
    {
        "titulo": "Umidade do solo",
        "campo": "soil_moisture_pct",
        "unidade": "%",
        "cor": CORES["umidade_solo"],
        "icone": "◉",
        "casas": 1,
    },
]


ESTADOS_HIDRICOS = {
    "UMIDADE_ADEQUADA": (
        "Umidade adequada",
        "success",
        "O solo está dentro da faixa configurada como adequada.",
    ),
    "ATENCAO_HIDRICA": (
        "Atenção hídrica",
        "warning",
        "A umidade do solo exige acompanhamento.",
    ),
    "NECESSIDADE_IRRIGACAO": (
        "Necessidade de irrigação",
        "error",
        "A umidade está na faixa crítica configurada.",
    ),
}


def _formatar_valor(valor, casas=1):
    """Formata valores numéricos no padrão brasileiro."""
    return f"{float(valor):.{casas}f}".replace(".", ",")


def exibir_indicadores(medicao):
    """Apresenta os quatro indicadores com estilo padronizado."""

    colunas = st.columns(4, gap="medium")

    for coluna, indicador in zip(colunas, INDICADORES):
        valor = _formatar_valor(
            medicao[indicador["campo"]],
            indicador["casas"],
        )

        titulo = escape(indicador["titulo"])
        unidade = escape(indicador["unidade"])
        cor = indicador["cor"]
        icone = escape(indicador["icone"])

        with coluna:
            st.html(
                f"""
                <div style="
                    background: #FFFFFF;
                    border: 1px solid {CORES['borda']};
                    border-radius: 14px;
                    padding: 20px;
                    min-height: 145px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    font-family: inherit;
                ">
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        gap: 8px;
                    ">
                        <span style="
                            color: {CORES['texto_secundario']};
                            font-size: 13px;
                            font-weight: 500;
                        ">
                            {titulo}
                        </span>

                        <span style="
                            color: {cor};
                            background: {cor}15;
                            border-radius: 9px;
                            width: 34px;
                            height: 34px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 18px;
                        ">
                            {icone}
                        </span>
                    </div>

                    <div style="
                        color: {CORES['texto']};
                        font-size: 30px;
                        font-weight: 650;
                        letter-spacing: -0.7px;
                        margin-top: 14px;
                    ">
                        {valor}
                        <span style="
                            font-size: 17px;
                            font-weight: 500;
                        ">{unidade}</span>
                    </div>

                    <div style="
                        width: 34px;
                        height: 3px;
                        background: {cor};
                        border-radius: 10px;
                        margin-top: 15px;
                    "></div>
                </div>
                """
            )


def exibir_estado_hidrico(estado):
    """Mantém a classificação e os alertas existentes."""

    titulo, tipo, descricao = ESTADOS_HIDRICOS.get(
        estado,
        (
            "Estado desconhecido",
            "info",
            "Não foi possível interpretar a condição hídrica.",
        ),
    )

    with st.container(border=True):
        st.subheader("Condição hídrica")

        mensagem = f"**{titulo}** — {descricao}"

        if tipo == "success":
            st.success(mensagem, icon=":material/check_circle:")

        elif tipo == "warning":
            st.warning(mensagem, icon=":material/warning:")

        elif tipo == "error":
            st.error(mensagem, icon=":material/error:")

        else:
            st.info(mensagem)
