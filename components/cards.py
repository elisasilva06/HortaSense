"""HortaSense — componentes visuais de indicadores (identidade visual v4).

Camada apenas de apresentação. Preserva os campos, a formatação dos valores,
as classificações do firmware e a API pública:
    exibir_indicadores(medicao)
    exibir_estado_hidrico(estado)
"""

from html import escape

import streamlit as st


CORES = {
    "verde_profundo": "#2F5A3A",
    "matcha": "#668B4A",
    "papel": "#FFFDF6",
    "texto": "#27382B",
    "texto_secundario": "#57664F",
    "borda": "#D8DFC9",
}


INDICADORES = [
    {
        "titulo": "Temperatura do ar",
        "campo": "air_temperature_c",
        "unidade": "°C",
        "casas": 1,
        "cor": "#B87955",
        "fundo_detalhe": "#F6E6D8",
        "etiqueta": "AMBIENTE",
        "numero": "01",
    },
    {
        "titulo": "Umidade do ar",
        "campo": "air_humidity_pct",
        "unidade": "%",
        "casas": 1,
        "cor": "#4E8768",
        "fundo_detalhe": "#E4F0E5",
        "etiqueta": "ATMOSFERA",
        "numero": "02",
    },
    {
        "titulo": "Temperatura do solo",
        "campo": "soil_temperature_c",
        "unidade": "°C",
        "casas": 1,
        "cor": "#967147",
        "fundo_detalhe": "#F3E9D8",
        "etiqueta": "SOLO",
        "numero": "03",
    },
    {
        "titulo": "Umidade do solo",
        "campo": "soil_moisture_pct",
        "unidade": "%",
        "casas": 1,
        "cor": "#668B4A",
        "fundo_detalhe": "#E3EED7",
        "etiqueta": "HIDRATAÇÃO",
        "numero": "04",
    },
]


# Mantém os textos de classificação da versão anterior.
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
    """Renderiza os mesmos quatro indicadores, sem ícones invisíveis."""

    colunas = st.columns(4, gap="medium")

    for coluna, indicador in zip(colunas, INDICADORES):
        valor = escape(_formatar_valor(medicao[indicador["campo"]], indicador["casas"]))
        titulo = escape(indicador["titulo"])
        unidade = escape(indicador["unidade"])
        etiqueta = escape(indicador["etiqueta"])
        numero = escape(indicador["numero"])
        cor = indicador["cor"]
        fundo_detalhe = indicador["fundo_detalhe"]

        with coluna:
            st.html(
                f"""
                <div style="
                    position:relative; overflow:hidden; box-sizing:border-box;
                    background:{CORES['papel']}; border:1px solid {CORES['borda']};
                    border-radius:24px 24px 24px 9px; min-height:188px;
                    padding:20px 19px 19px;
                    font-family:'Manrope','Segoe UI',sans-serif;
                    box-shadow:0 7px 22px rgba(47,90,58,.045);
                ">
                    <div aria-hidden="true" style="
                        position:absolute; width:122px; height:122px;
                        right:-57px; top:-54px; border-radius:50%;
                        background:{fundo_detalhe}; opacity:.70;
                    "></div>
                    <div style="position:relative;display:flex;align-items:center;
                        justify-content:space-between;gap:9px;">
                        <span style="font-size:10px;font-weight:800;
                            letter-spacing:.12em;color:{cor};">{etiqueta}</span>
                        <span style="font-size:11px;font-weight:800;
                            color:{CORES['texto_secundario']};">{numero}</span>
                    </div>
                    <div style="position:relative;margin-top:20px;
                        font-size:13px;font-weight:650;line-height:1.45;
                        color:{CORES['texto_secundario']};">{titulo}</div>
                    <div style="position:relative;margin-top:12px;
                        display:flex;align-items:baseline;gap:5px;
                        color:{CORES['verde_profundo']};">
                        <span style="font-family:'Bricolage Grotesque',
                            'Trebuchet MS',sans-serif;
                            font-size:clamp(26px,2.1vw,35px);
                            font-weight:800;line-height:1.15;letter-spacing:-.05em;">
                            {valor}
                        </span>
                        <span style="font-size:15px;font-weight:700;">{unidade}</span>
                    </div>
                    <div aria-hidden="true" style="position:relative;
                        width:58px;height:5px;background:{cor};
                        border-radius:12px;margin-top:18px;"></div>
                </div>
                """
            )


def exibir_estado_hidrico(estado):
    """Exibe o estado recebido, com alerta visual de contraste reforçado."""

    titulo, tipo, descricao = ESTADOS_HIDRICOS.get(
        estado,
        (
            "Estado desconhecido",
            "info",
            "Não foi possível interpretar a condição hídrica.",
        ),
    )

    # Cores semânticas mais perceptíveis; nenhum limite ou estado é alterado.
    estilos = {
        "success": {
            "cor": "#236842",
            "fundo": "#E3F2E5",
            "borda": "#A3CDAE",
            "marcador": "CONDIÇÃO ADEQUADA",
            "simbolo": "✓",
        },
        "warning": {
            "cor": "#975000",
            "fundo": "#FFE2A3",
            "borda": "#D99428",
            "marcador": "ATENÇÃO · ACOMPANHAR UMIDADE",
            "simbolo": "!",
        },
        "error": {
            "cor": "#AC3028",
            "fundo": "#FFD8D0",
            "borda": "#D45E4D",
            "marcador": "ALERTA · IRRIGAÇÃO NECESSÁRIA",
            "simbolo": "!",
        },
        "info": {
            "cor": "#2F5A3A",
            "fundo": "#E6EEDC",
            "borda": "#B0C8AB",
            "marcador": "ESTADO NÃO IDENTIFICADO",
            "simbolo": "?",
        },
    }

    visual = estilos[tipo]
    cor = visual["cor"]
    fundo = visual["fundo"]
    borda = visual["borda"]
    marcador = escape(visual["marcador"])
    simbolo = escape(visual["simbolo"])
    titulo = escape(titulo)
    descricao = escape(descricao)

    st.html(
        f"""
        <section aria-label="Condição hídrica" style="
            position:relative;overflow:hidden;box-sizing:border-box;
            background:{CORES['papel']};
            border:1px solid {borda};
            border-radius:24px 24px 24px 10px;
            padding:23px 25px;
            font-family:'Manrope','Segoe UI',sans-serif;
            box-shadow:0 7px 22px rgba(47,90,58,.04);
        ">
            <div aria-hidden="true" style="position:absolute;top:0;left:0;
                height:100%;width:7px;background:{cor};"></div>
            <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
                <div aria-hidden="true" style="
                    width:53px;height:53px;flex:none;
                    display:flex;align-items:center;justify-content:center;
                    background:{fundo};border:2px solid {borda};
                    color:{cor};font-family:Arial,sans-serif;
                    font-size:30px;font-weight:900;line-height:1;
                    border-radius:50%;">{simbolo}</div>
                <div style="flex:1;min-width:220px;">
                    <div style="color:{cor};font-size:11px;font-weight:850;
                        letter-spacing:.11em;margin-bottom:5px;">{marcador}</div>
                    <div style="color:{cor};
                        font-family:'Bricolage Grotesque', 'Trebuchet MS',sans-serif;
                        font-size:clamp(20px,2vw,26px);font-weight:800;
                        line-height:1.2;">{titulo}</div>
                    <div style="color:{CORES['texto']};font-size:13px;
                        line-height:1.6;margin-top:5px;">{descricao}</div>
                </div>
                <span style="display:inline-block;max-width:100%;
                    font-size:11px;font-weight:850;color:{cor};
                    background:{fundo};border:1px solid {borda};
                    border-radius:999px;padding:9px 14px;">
                    {titulo}
                </span>
            </div>
        </section>
        """
    )
