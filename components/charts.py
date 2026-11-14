
"""
HortaSense — Gráficos de monitoramento.

Visualização da evolução da umidade do solo.

Funcionalidades:
- Filtros por tempo e quantidade de medições.
- Eixo X adaptado ao filtro selecionado.
- Tratamento de intervalos sem medições.
- Marcadores e linhas visíveis em 0% e 100%.
- Destaque da última leitura.
- Resumo estatístico das medições.

Os dados armazenados no SQLite não são alterados.
"""

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ==========================================================
# IDENTIDADE VISUAL
# ==========================================================

COR_LINHA = "#366B73"
COR_TEXTO = "#25312B"
COR_SECUNDARIA = "#718078"
COR_GRADE = "#E5EBE6"
COR_ULTIMO = "#2D6F73"

# O ESP32 envia medições aproximadamente a cada 5 segundos.
# Intervalos superiores a 20 segundos interrompem a linha
# nos filtros temporais.
INTERVALO_MAXIMO_SEGUNDOS = 20


# ==========================================================
# FILTROS DISPONÍVEIS
# ==========================================================

PERIODOS = {
    "Últimos 5 minutos": {
        "tipo": "tempo",
        "valor": 5,
    },
    "Últimos 15 minutos": {
        "tipo": "tempo",
        "valor": 15,
    },
    "Últimos 30 minutos": {
        "tipo": "tempo",
        "valor": 30,
    },
    "Últimas 20 medições": {
        "tipo": "quantidade",
        "valor": 20,
    },
    "Últimas 100 medições": {
        "tipo": "quantidade",
        "valor": 100,
    },
}


# ==========================================================
# PREPARAÇÃO DOS DADOS
# ==========================================================

def preparar_medicoes(registros):
    """Valida e organiza as medições cronologicamente."""

    dados = pd.DataFrame(registros).copy()

    dados["horario"] = pd.to_datetime(
        dados["received_at"],
        utc=True,
        errors="coerce",
    ).dt.tz_convert("America/Fortaleza")

    dados["soil_moisture_pct"] = pd.to_numeric(
        dados["soil_moisture_pct"],
        errors="coerce",
    )

    dados = dados.dropna(
        subset=["horario", "soil_moisture_pct"]
    )

    dados = dados.sort_values(
        ["horario", "id"]
    ).reset_index(drop=True)

    return dados


def filtrar_medicoes(dados, periodo):
    """Seleciona as medições conforme o filtro."""

    configuracao = PERIODOS[periodo]

    tipo = configuracao["tipo"]
    valor = configuracao["valor"]

    if tipo == "quantidade":
        return dados.tail(valor).copy(), tipo

    # Usa a última medição como referência temporal.
    # Assim, o histórico permanece acessível offline.
    horario_final = dados["horario"].max()

    horario_inicial = (
        horario_final - pd.Timedelta(minutes=valor)
    )

    dados_filtrados = dados[
        dados["horario"] >= horario_inicial
    ].copy()

    return dados_filtrados, tipo


# ==========================================================
# TRATAMENTO DE INTERVALOS SEM MEDIÇÕES
# ==========================================================

def montar_segmentos_tempo(dados):
    """
    Separa as medições em segmentos.

    Quando o intervalo entre duas leituras ultrapassa
    20 segundos, uma nova linha é iniciada.

    Os registros originais não são modificados.
    """

    segmentos = []
    segmento_atual = []

    horario_anterior = None

    for registro in dados.itertuples(index=False):

        horario_atual = registro.horario

        if horario_anterior is not None:

            intervalo = (
                horario_atual - horario_anterior
            ).total_seconds()

            if intervalo > INTERVALO_MAXIMO_SEGUNDOS:

                if segmento_atual:
                    segmentos.append(segmento_atual)

                segmento_atual = []

        segmento_atual.append(
            {
                "horario": horario_atual,
                "valor": registro.soil_moisture_pct,
            }
        )

        horario_anterior = horario_atual

    if segmento_atual:
        segmentos.append(segmento_atual)

    return segmentos


# ==========================================================
# GRÁFICO COM EIXO TEMPORAL
# ==========================================================

def adicionar_tracos_tempo(figura, dados_filtrados):
    """Desenha as medições utilizando o horário real."""

    segmentos = montar_segmentos_tempo(
        dados_filtrados
    )

    for segmento in segmentos:

        horarios = [
            ponto["horario"]
            for ponto in segmento
        ]

        valores = [
            ponto["valor"]
            for ponto in segmento
        ]

        figura.add_trace(
            go.Scatter(
                x=horarios,
                y=valores,

                mode="lines+markers",

                line=dict(
                    color=COR_LINHA,
                    width=3,
                ),

                marker=dict(
                    size=8,
                    color=COR_LINHA,
                    line=dict(
                        color="#FFFFFF",
                        width=1.5,
                    ),
                ),

                # Evita cortar marcadores nas bordas.
                cliponaxis=False,

                connectgaps=False,

                hovertemplate=(
                    "<b>%{x|%d/%m/%Y}</b>"
                    "<br>Horário: %{x|%H:%M:%S}"
                    "<br>Umidade: <b>%{y:.0f}%</b>"
                    "<extra></extra>"
                ),

                showlegend=False,
            )
        )


# ==========================================================
# GRÁFICO COM EIXO SEQUENCIAL
# ==========================================================

def adicionar_traco_quantidade(figura, dados_filtrados):
    """
    Desenha as últimas N medições com espaçamento igual.

    Os horários reais permanecem disponíveis no hover.
    """

    dados_plot = (
        dados_filtrados.copy()
        .reset_index(drop=True)
    )

    dados_plot["indice"] = range(
        1,
        len(dados_plot) + 1,
    )

    figura.add_trace(
        go.Scatter(
            x=dados_plot["indice"],
            y=dados_plot["soil_moisture_pct"],

            mode="lines+markers",

            line=dict(
                color=COR_LINHA,
                width=3,
            ),

            marker=dict(
                size=8,
                color=COR_LINHA,
                line=dict(
                    color="#FFFFFF",
                    width=1.5,
                ),
            ),

            customdata=dados_plot["horario"],

            cliponaxis=False,

            hovertemplate=(
                "<b>Medição %{x}</b>"
                "<br>Horário: "
                "%{customdata|%d/%m/%Y às %H:%M:%S}"
                "<br>Umidade: <b>%{y:.0f}%</b>"
                "<extra></extra>"
            ),

            showlegend=False,
        )
    )


# ==========================================================
# ESTILO GERAL DO GRÁFICO
# ==========================================================

def configurar_layout_base(figura):
    """Aplica a identidade visual do HortaSense."""

    figura.update_layout(
        height=380,

        margin=dict(
            l=20,
            r=30,
            t=30,
            b=20,
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        font=dict(
            family="Inter, sans-serif",
            color=COR_TEXTO,
            size=12,
        ),

        hovermode="closest",

        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor=COR_GRADE,

            font=dict(
                family="Inter, sans-serif",
                color=COR_TEXTO,
                size=12,
            ),
        ),

        showlegend=False,
        dragmode=False,
    )

    # Folga visual abaixo de 0% e acima de 100%.
    # Os valores reais permanecem inalterados.
    figura.update_yaxes(
        title_text="Umidade do solo (%)",

        range=[-5, 105],

        tickvals=[
            0, 20, 40, 60, 80, 100
        ],

        ticksuffix="%",

        gridcolor=COR_GRADE,
        gridwidth=1,

        zeroline=False,
        showline=False,

        tickfont=dict(
            color=COR_SECUNDARIA,
        ),

        title_font=dict(
            color=COR_SECUNDARIA,
        ),
    )


# ==========================================================
# CONFIGURAÇÃO DO EIXO X
# ==========================================================

def configurar_eixo_x_tempo(figura, dados_filtrados):
    """Configura os horários no eixo horizontal."""

    duracao = (
        dados_filtrados["horario"].max()
        - dados_filtrados["horario"].min()
    )

    if duracao > pd.Timedelta(hours=12):
        formato = "%d/%m\n%H:%M"
    else:
        formato = "%H:%M:%S"

    figura.update_xaxes(
        title_text="Horário",

        tickformat=formato,
        nticks=8,

        showgrid=False,
        zeroline=False,
        showline=False,

        tickfont=dict(
            color=COR_SECUNDARIA,
        ),

        title_font=dict(
            color=COR_SECUNDARIA,
        ),
    )


def configurar_eixo_x_quantidade(figura, quantidade):
    """Configura o eixo horizontal por sequência."""

    passo = max(
        1,
        math.ceil(quantidade / 8),
    )

    figura.update_xaxes(
        title_text="Sequência das medições",

        tickmode="linear",
        tick0=1,
        dtick=passo,

        # Pequena folga nas extremidades.
        range=[0.5, quantidade + 0.5],

        showgrid=False,
        zeroline=False,
        showline=False,

        tickfont=dict(
            color=COR_SECUNDARIA,
        ),

        title_font=dict(
            color=COR_SECUNDARIA,
        ),
    )


# ==========================================================
# DESTAQUE DA ÚLTIMA MEDIÇÃO
# ==========================================================

def destacar_ultima_medicao(
    figura,
    dados_filtrados,
    tipo_eixo,
):
    """Destaca a última leitura sem alterar a série."""

    ultima = dados_filtrados.iloc[-1]

    valor = float(
        ultima["soil_moisture_pct"]
    )

    if tipo_eixo == "quantidade":
        x_ultima = len(dados_filtrados)
    else:
        x_ultima = ultima["horario"]

    # Se o valor estiver próximo de 100%,
    # coloca o texto abaixo do marcador.
    posicao_texto = (
        "bottom center"
        if valor >= 95
        else "top center"
    )

    figura.add_trace(
        go.Scatter(
            x=[x_ultima],
            y=[valor],

            mode="markers+text",

            text=[
                f"{valor:.0f}%"
            ],

            textposition=posicao_texto,

            textfont=dict(
                color=COR_TEXTO,
                size=12,
            ),

            marker=dict(
                color=COR_ULTIMO,
                size=13,

                line=dict(
                    color="#FFFFFF",
                    width=3,
                ),
            ),

            cliponaxis=False,

            hovertemplate=(
                "<b>Última medição</b>"
                "<br>Umidade: <b>%{y:.0f}%</b>"
                "<extra></extra>"
            ),

            showlegend=False,
        )
    )


# ==========================================================
# RESUMO ESTATÍSTICO
# ==========================================================

def exibir_resumo(dados_filtrados):
    """Exibe estatísticas das medições selecionadas."""

    quantidade = len(dados_filtrados)

    valores = dados_filtrados[
        "soil_moisture_pct"
    ]

    valor_minimo = float(
        valores.min()
    )

    valor_maximo = float(
        valores.max()
    )

    valor_medio = float(
        valores.mean()
    )

    ultima = dados_filtrados.iloc[-1]

    valor_atual = float(
        ultima["soil_moisture_pct"]
    )

    horario_atual = ultima["horario"]

    st.caption(
        f"{quantidade} medições exibidas | "
        f"Mín: {valor_minimo:.0f}% | "
        f"Máx: {valor_maximo:.0f}% | "
        f"Média: {valor_medio:.0f}% | "
        f"Última leitura: {valor_atual:.0f}% | "
        f"Atualizado em: "
        f"{horario_atual:%d/%m/%Y às %H:%M:%S}"
    )


# ==========================================================
# FUNÇÃO PRINCIPAL
# ==========================================================

def exibir_grafico_umidade(registros):
    """Renderiza o gráfico de evolução da umidade."""

    if not registros:
        st.info(
            "Ainda não existem medições para exibir."
        )
        return

    dados = preparar_medicoes(registros)

    if dados.empty:
        st.info(
            "Não há medições válidas para o gráfico."
        )
        return

    # Filtro interativo.
    periodo = st.selectbox(
        "Período de visualização",

        options=list(
            PERIODOS.keys()
        ),

        index=1,

        key="filtro_periodo_umidade",
    )

    dados_filtrados, tipo_eixo = filtrar_medicoes(
        dados,
        periodo,
    )

    if dados_filtrados.empty:
        st.info(
            "Nenhuma medição encontrada nesse período."
        )
        return

    # Criação da figura.
    figura = go.Figure()

    configurar_layout_base(
        figura
    )

    # Seleção do tipo de representação.
    if tipo_eixo == "quantidade":

        adicionar_traco_quantidade(
            figura,
            dados_filtrados,
        )

        configurar_eixo_x_quantidade(
            figura,
            len(dados_filtrados),
        )

    else:

        adicionar_tracos_tempo(
            figura,
            dados_filtrados,
        )

        configurar_eixo_x_tempo(
            figura,
            dados_filtrados,
        )

    # Última leitura destacada.
    destacar_ultima_medicao(
        figura,
        dados_filtrados,
        tipo_eixo,
    )

    # Exibição no Streamlit.
    st.plotly_chart(
        figura,

        width="stretch",

        config={
            "displayModeBar": False,
            "scrollZoom": False,
        },
    )

    # Estatísticas abaixo do gráfico.
    exibir_resumo(
        dados_filtrados
    )
