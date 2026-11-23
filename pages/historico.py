"""HortaSense | Histórico e Irrigação.

Consulta histórica local, análise de sessões de monitoramento e gráficos didáticos.
A página apenas lê o SQLite; nenhum dado original é alterado.
"""

from datetime import datetime, time, timedelta
from html import escape
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database import consultar_medicoes_intervalo, consultar_ultimas_medicoes


FUSO_LOCAL = ZoneInfo("America/Fortaleza")
PAUSA_ENTRE_SESSOES_MIN = 2
LACUNA_LINHA_SEG = 20
AGRUPAMENTOS = {"15 minutos": 15, "30 minutos": 30, "1 hora": 60}

C = {
    "verde_escuro": "#2F5A3A",
    "petroleo": "#438D4D",
    "verde": "#438553",
    "amarelo": "#E5A127",
    "vermelho": "#D64F42",
    "texto": "#27382B",
    "cinza": "#57664F",
    "borda": "#D8DFC9",
    "fundo": "#F8F1DC",
}

STATUS = {
    "UMIDADE_ADEQUADA": "Adequada",
    "ATENCAO_HIDRICA": "Atenção",
    "NECESSIDADE_IRRIGACAO": "Necessita irrigação",
}
STATUS_CORES = {
    "Adequada": C["verde"],
    "Atenção": C["amarelo"],
    "Necessita irrigação": C["vermelho"],
}


def aplicar_estilo():
    """Aplica somente a identidade visual à página Histórico e Irrigação."""
    st.html("""
    <style>
      /* Escopo: somente a página de Histórico. Não interfere na Visão Geral. */
      .stApp:has(#hs-historico-root) [data-testid="stMain"] .block-container {
        max-width: 1320px;
        padding-top: 2rem;
        padding-bottom: 4rem;
      }
      .stApp:has(#hs-historico-root) [data-testid="stMain"] h4 {
        color: #2F5A3A !important;
        font-family: 'Bricolage Grotesque', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: -0.035em;
      }
      .hs-hist-hero {
        position: relative;
        isolation: isolate;
        overflow: hidden;
        background: linear-gradient(112deg, #2F5A3A 0%, #35663F 57%, #668B4A 100%);
        border-radius: 32px 32px 32px 9px;
        padding: 46px 48px 42px;
        margin-bottom: 27px;
        box-shadow: 0 14px 34px rgba(47,90,58,.09);
        color: #FFFDF6;
        font-family: 'Manrope', sans-serif;
      }
      .hs-hist-hero:before {
        content: '';
        position: absolute;
        width: 310px; height: 310px;
        border-radius: 50%;
        right: -130px; top: -195px;
        background: rgba(220,232,210,.14);
        z-index: -1;
      }
      .hs-hist-hero:after {
        content: '';
        position: absolute;
        width: 165px; height: 165px;
        border: 2px solid rgba(220,232,210,.24);
        border-radius: 50%;
        right: 42px; bottom: -120px;
        z-index: -1;
      }
      .hs-hist-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 9px;
        padding: 8px 14px;
        background: rgba(248,241,220,.10);
        border: 1px solid rgba(248,241,220,.23);
        border-radius: 99px;
        color: #FFFDF6;
        font-size: 11px;
        letter-spacing: .085em;
        font-weight: 800;
      }
      .hs-hist-eyebrow:before {
        content: '';
        width: 9px; height: 9px;
        border-radius: 50%;
        background: #C5DF9D;
      }
      .hs-hist-hero-title {
        color: #FFFDF6 !important;
        font-family: 'Bricolage Grotesque', sans-serif;
        font-weight: 800;
        font-size: clamp(32px,4.1vw,53px);
        line-height: 1.10;
        letter-spacing: -.055em;
        margin: 31px 0 19px;
      }
      .hs-hist-hero-subtitle {
        color: #F8F1DC !important;
        max-width: 670px;
        font-size: 15px;
        line-height: 1.75;
        margin: 0 0 27px;
      }
      .hs-hist-signature {
        display: flex; align-items: center; gap: 12px;
        color: #F8F1DC;
        font-size: 11px; font-weight: 700;
      }
      .hs-hist-signature:before {
        content: '';
        width: 34px; height: 3px;
        border-radius: 99px;
        background: #C5DF9D;
      }
      .hs-hist-section {
        display: flex; align-items: center; gap: 13px;
        margin: 31px 0 17px;
        color: #2F5A3A;
        font: 800 12px/1.4 'Manrope',sans-serif;
        letter-spacing: .10em;
        text-transform: uppercase;
      }
      .hs-hist-section:before {
        content: '';
        width: 7px; height: 23px;
        border-radius: 99px;
        background: #8AA730;
      }
      .hs-hist-card {
        position: relative;
        overflow: hidden;
        min-height: 188px;
        padding: 24px 23px 22px;
        border: 1px solid #D8DFC9;
        border-radius: 30px 30px 30px 10px;
        background: #FFFDF6;
        box-shadow: 0 10px 24px rgba(47,90,58,.055);
        font-family: 'Manrope', sans-serif;
      }
      .hs-hist-card:before {
        content: '';
        position: absolute;
        width: 112px; height: 112px;
        top: -48px; right: -32px;
        background: var(--hs-hist-tint);
        border-radius: 50%;
      }
      .hs-hist-card-top {
        position: relative;
        display: flex; justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 17px;
      }
      .hs-hist-card-index {
        color: var(--hs-hist-accent);
        font-size: 11px; font-weight: 800;
        letter-spacing: .11em;
      }
      .hs-hist-card-number {
        color: #2F5A3A;
        font: 800 clamp(26px,2.8vw,39px)/1.15 'Bricolage Grotesque',sans-serif;
        letter-spacing: -.035em;
        margin: 10px 0 2px;
      }
      .hs-hist-card-name {color: #354B36;font-size: 13px;font-weight: 700;}
      .hs-hist-card-detail {color: #57664F;font-size: 11px;margin-top: 7px;}
      .hs-hist-card-accent {
        width: 64px;height: 5px;background: var(--hs-hist-accent);
        border-radius: 10px;margin-top: 19px;
      }
      .hs-hist-period {
        display: inline-flex;align-items: center;gap: 9px;
        padding: 10px 15px;
        margin: 13px 0 4px;
        background: #E8F1DE;
        color: #2F5A3A;
        border: 1px solid #C9DDB9;
        border-radius: 999px;
        font: 700 12px 'Manrope',sans-serif;
      }
      .hs-hist-period:before {
        content: '';width: 8px;height: 8px;
        border-radius: 50%;background: #668B4A;
      }
      /* Cartões Streamlit desta página: superfícies iguais às da Visão Geral. */
      .stApp:has(#hs-historico-root) [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"]:has(> div) {
        border-radius: 25px !important;
        border-color: #D8DFC9 !important;
      }
      .stApp:has(#hs-historico-root) [data-testid="stMain"] [data-testid="stForm"] {
        background: #FFFDF6 !important;
        border: 1px solid #D8DFC9 !important;
        border-radius: 24px !important;
      }
      /* Correção prioritária: botões de envio com texto sempre legível. */
      .stApp:has(#hs-historico-root) [data-testid="stMain"] [data-testid="stFormSubmitButton"] button,
      .stApp:has(#hs-historico-root) [data-testid="stMain"] [data-testid="stFormSubmitButton"] button[kind="primary"] {
        background: #2F5A3A !important;
        border: 1px solid #2F5A3A !important;
        border-radius: 14px !important;
        min-height: 46px;
        color: #FFFDF6 !important;
        font-weight: 800 !important;
      }
      .stApp:has(#hs-historico-root) [data-testid="stMain"] [data-testid="stFormSubmitButton"] button * {
        color: #FFFDF6 !important;
      }
      .stApp:has(#hs-historico-root) [data-testid="stMain"] [data-testid="stFormSubmitButton"] button:hover {
        background: #668B4A !important;
        border-color: #668B4A !important;
      }
      .stApp:has(#hs-historico-root) [data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"] > div,
      .stApp:has(#hs-historico-root) [data-testid="stMain"] [data-testid="stDateInput"] input,
      .stApp:has(#hs-historico-root) [data-testid="stMain"] [data-testid="stTimeInput"] input {
        background-color: #FFFDF6 !important;
        border-color: #B9D0A6 !important;
        border-radius: 14px !important;
      }
      .stApp:has(#hs-historico-root) [data-testid="stMain"] [data-testid="stExpander"] {
        background: #FFFDF6;
        border: 1px solid #D8DFC9;
        border-radius: 19px !important;
      }
      @media(max-width:800px) {
        .hs-hist-hero {padding:30px 23px;border-radius:24px 24px 24px 8px;}
        .hs-hist-card {min-height:166px;padding:20px;}
        .hs-hist-hero-title {margin-top:22px;}
      }
    </style>
    <span id="hs-historico-root" style="display:none"></span>
    """)


def rotulo_secao(texto):
    """Usa a mesma etiqueta com acento verde da Visão Geral."""
    st.html(f'<div class="hs-hist-section">{escape(texto)}</div>')


def cartao(titulo, valor, detalhe, cor):
    """Card visual; valores e cálculos continuam vindo de indicadores()."""
    tons = {
        C["verde"]: "#E2EEDD",
        C["petroleo"]: "#E1F0DE",
        C["vermelho"]: "#FCE6E0",
        C["amarelo"]: "#FFF0C8",
    }
    tons_tint = tons.get(cor, "#EDF3E5")
    st.html(
        f'<div class="hs-hist-card" style="--hs-hist-accent:{cor};'
        f'--hs-hist-tint:{tons_tint}">'
        '<div class="hs-hist-card-top">'
        f'<span class="hs-hist-card-index">{escape(titulo.upper())}</span>'
        '</div>'
        f'<div class="hs-hist-card-number">{escape(valor)}</div>'
        f'<div class="hs-hist-card-name">{escape(titulo)}</div>'
        f'<div class="hs-hist-card-detail">{escape(detalhe)}</div>'
        '<div class="hs-hist-card-accent"></div>'
        '</div>'
    )


def configurar_plot(figura, altura=330, legenda=False):
    """Aplica identidade visual aos gráficos, sem modificar dados nem eixos."""
    figura.update_layout(
        height=altura,
        margin=dict(l=10, r=18, t=28, b=18),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color=C["texto"], size=13),
        showlegend=legenda,
        legend=dict(orientation="h", y=-0.20, x=0.0,
                    font=dict(family="Manrope, sans-serif", size=11, color=C["texto"])),
        hovermode="closest",
        hoverlabel=dict(bgcolor="#FFFDF6", bordercolor="#B9D0A6",
                        font=dict(family="Manrope, sans-serif", color=C["verde_escuro"])),
    )
    figura.update_xaxes(showgrid=False, zeroline=False,
                        linecolor=C["borda"], tickfont=dict(color="#57664F", size=12),
                        title_font=dict(color=C["verde_escuro"], size=13))
    figura.update_yaxes(gridcolor="#D8DFC9", gridwidth=1,
                        zeroline=False, tickfont=dict(color="#57664F", size=12),
                        title_font=dict(color=C["verde_escuro"], size=13))
    return figura


def plot(figura, key):
    st.plotly_chart(
        figura,
        width="stretch",
        key=key,
        config={"displayModeBar": False, "scrollZoom": False},
    )


def data_mais_recente():
    registros = consultar_ultimas_medicoes(1)
    if registros:
        try:
            horario = datetime.fromisoformat(registros[0]["received_at"])
            return horario.astimezone(FUSO_LOCAL).date()
        except (ValueError, KeyError, TypeError):
            pass
    return datetime.now(FUSO_LOCAL).date()


def definir_intervalo(dia, inicio, fim):
    dt_inicio = datetime.combine(dia, inicio, tzinfo=FUSO_LOCAL)
    dt_fim = datetime.combine(dia, fim, tzinfo=FUSO_LOCAL)
    if dt_inicio > dt_fim:
        raise ValueError("O horário inicial deve ser anterior ou igual ao final.")
    # O minuto final informado no seletor faz parte da consulta.
    return dt_inicio, dt_fim + timedelta(minutes=1)


def filtros():
    rotulo_secao("Consulta histórica")
    with st.container(border=True):
        col_titulo, col_aux = st.columns([3, 1], vertical_alignment="center")
        with col_titulo:
            st.markdown("#### Selecione o período")
        with col_aux:
            st.caption("Horário de Fortaleza")
        with st.form("hortasense_historico_filtros"):
            coluna_data, coluna_inicio, coluna_fim = st.columns([2, 1, 1])
            with coluna_data:
                dia = st.date_input(
                    "Data do monitoramento", value=data_mais_recente(), format="DD/MM/YYYY"
                )
            with coluna_inicio:
                hora_inicio = st.time_input("De", value=time(0, 0), step=60)
            with coluna_fim:
                hora_fim = st.time_input("Até", value=time(23, 59), step=60)
            aplicar = st.form_submit_button(
                "Consultar histórico", type="primary", use_container_width=True
            )

    chave = "hortasense_historico_periodo_aplicado"
    if aplicar or chave not in st.session_state:
        try:
            periodo = definir_intervalo(dia, hora_inicio, hora_fim)
        except ValueError as erro:
            st.error(str(erro))
            return None
        st.session_state[chave] = periodo
    return st.session_state[chave]


def preparar_dados(registros):
    dados = pd.DataFrame(registros).copy()
    dados["horario"] = pd.to_datetime(
        dados["received_at"], utc=True, errors="coerce"
    ).dt.tz_convert(FUSO_LOCAL)
    for coluna in (
        "soil_moisture_pct", "soil_adc", "air_temperature_c",
        "air_humidity_pct", "soil_temperature_c"
    ):
        if coluna in dados.columns:
            dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")
    dados = dados.dropna(subset=["horario"])
    return dados.sort_values(["horario", "id"]).reset_index(drop=True)


def indicadores(dados):
    rotulo_secao("Resumo do período")
    umidades = dados["soil_moisture_pct"].dropna()
    if umidades.empty:
        st.info("Não há valores válidos de umidade neste período.")
        return

    umidades_positivas = umidades[umidades > 0]
    umidade_min = umidades_positivas.min() if not umidades_positivas.empty else 0

    cards = st.columns(4, gap="small")
    conteudo = [
        ("Umidade média", f"{umidades.mean():.1f}%".replace(".", ","), "Média das leituras", C["petroleo"]),
        ("Umidade mínima", f"{umidade_min:.0f}%", "Menor leitura", C["vermelho"]),
        ("Umidade máxima", f"{umidades.max():.0f}%", "Maior leitura", C["verde"]),
        ("Total de leituras", f"{len(umidades)}", "Medições válidas", C["amarelo"]),
    ]
    for coluna, (titulo, valor, detalhe, cor) in zip(cards, conteudo):
        with coluna:
            cartao(titulo, valor, detalhe, cor)


def separar_sessoes(dados):
    validos = dados.dropna(subset=["soil_moisture_pct"]).copy()
    validos = validos.sort_values("horario").reset_index(drop=True)
    if validos.empty:
        validos["sessao"] = pd.Series(dtype="int64")
        return validos
    diferencas = validos["horario"].diff()
    validos["sessao"] = (
        diferencas.isna()
        | diferencas.gt(pd.Timedelta(minutes=PAUSA_ENTRE_SESSOES_MIN))
    ).cumsum().astype(int)
    return validos


def selecionar_dados_graficos(dados):
    """Sessão é apenas um recorte visual; os indicadores usam o dia consultado."""
    validos = separar_sessoes(dados)
    if validos.empty:
        return validos, 30
    opcoes = {"Todas as sessões": None}
    for numero, grupo in validos.groupby("sessao", sort=False):
        de, ate = grupo["horario"].iloc[0], grupo["horario"].iloc[-1]
        texto = f"Sessão {numero}  ·  {de:%H:%M:%S}–{ate:%H:%M:%S}  ·  {len(grupo)} leituras"
        opcoes[texto] = int(numero)
    nomes = list(opcoes)
    nomes = [nomes[0]] + list(reversed(nomes[1:]))
    coluna_sessao, coluna_agrupar = st.columns([2.2, 1])
    with coluna_sessao:
        escolha = st.selectbox(
            "Sessão de monitoramento", nomes,
            index=1 if len(nomes) > 1 else 0,
            key="hortasense_nova_sessao",
        )
    with coluna_agrupar:
        nome_intervalo = st.selectbox(
            "Médias por", list(AGRUPAMENTOS), index=1,
            key="hortasense_novo_agrupamento",
        )
    numero = opcoes[escolha]
    selecionados = (
        validos if numero is None
        else validos.loc[validos["sessao"] == numero].copy()
    ).reset_index(drop=True)
    st.caption(
        f"{len(selecionados)} leituras nos gráficos · "
        f"{validos['sessao'].nunique()} sessões identificadas no período. "
        "Os indicadores e a tabela mostram o período completo."
    )
    return selecionados, AGRUPAMENTOS[nome_intervalo]


def evolucao(dados):
    with st.container(border=True):
        st.markdown("#### Evolução da umidade do solo")
        st.caption("Cada ponto representa uma leitura. O eixo mostra a ordem das medições.")
        if dados.empty:
            st.info("Nenhuma leitura disponível nesta seleção.")
            return
        dados = dados.sort_values("horario").reset_index(drop=True)
        posicoes = list(range(1, len(dados) + 1))
        # Hora real no hover; o eixo horizontal representa a sequência.
        horarios = dados["horario"].dt.strftime("%d/%m/%Y %H:%M:%S").tolist()
        figura = go.Figure()
        # A linha é interrompida após lacunas, mas os pontos permanecem.
        partes_x, partes_y = [], []
        for i, (posicao, umidade) in enumerate(zip(posicoes, dados["soil_moisture_pct"])):
            if i and (dados.loc[i, "horario"] - dados.loc[i - 1, "horario"]).total_seconds() > LACUNA_LINHA_SEG:
                partes_x.append(None)
                partes_y.append(None)
            partes_x.append(posicao)
            partes_y.append(float(umidade))
        figura.add_trace(go.Scatter(
            x=partes_x, y=partes_y, mode="lines", connectgaps=False,
            line=dict(color=C["petroleo"], width=4), hoverinfo="skip"
        ))
        figura.add_trace(go.Scatter(
            x=posicoes, y=dados["soil_moisture_pct"], mode="markers",
            marker=dict(color=C["petroleo"], size=10, line=dict(color="#FFFDF6", width=1.6)),
            customdata=horarios,
            hovertemplate="<b>%{customdata}</b><br>Umidade: %{y:.0f}%<extra></extra>",
        ))
        configurar_plot(figura, altura=455)
        figura.update_xaxes(
            title_text="Sequência das leituras", dtick=max(1, len(dados) // 10),
            range=[0.5, len(dados) + 0.5],
        )
        figura.update_yaxes(
    title_text="Umidade do solo (%)",
    range=[-5, 105],
    tickmode="array",
    tickvals=[0, 20, 40, 60, 80, 100],
    ticktext=["0", "20", "40", "60", "80", "100"],
    zeroline=False,)
    plot(figura, "historico_evolucao_v3")


def classificacao_por_umidade(umidade):
    """Mesmos limites do firmware; ignora leituras inválidas."""
    if pd.isna(umidade):
        return None
    if umidade <= 30:
        return "Necessita irrigação"
    if umidade <= 50:
        return "Atenção"
    return "Adequada"


def distribuicao(dados):
    """Gráfico de rosca das classificações, sem inferir tempo de permanência."""
    with st.container(border=True):
        st.markdown("#### Condições hídricas")
        st.caption("Distribuição das leituras da sessão selecionada.")
        if dados.empty:
            st.info("Sem leituras para classificar.")
            return
        classes = dados["soil_moisture_pct"].apply(classificacao_por_umidade)
        contagem = classes.value_counts()
        categorias = ["Adequada", "Atenção", "Necessita irrigação"]
        valores = [int(contagem.get(c, 0)) for c in categorias]
        figura = go.Figure(go.Pie(
            labels=categorias, values=valores, hole=0.65,
            sort=False, direction="clockwise",
            marker=dict(colors=[STATUS_CORES[n] for n in categorias], line=dict(color="#FFFDF6", width=3)),
            textinfo="percent", textposition="inside", insidetextorientation="horizontal",
            hovertemplate="<b>%{label}</b><br>%{value} leituras · %{percent}<extra></extra>",
        ))
        configurar_plot(figura, altura=385, legenda=True)
        figura.update_layout(
            margin=dict(l=25, r=25, t=32, b=75),
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.18, font=dict(size=11, color=C["texto"])),
            annotations=[dict(text=f"<b>{sum(valores)}</b><br>leituras", x=0.5, y=0.5,
                              showarrow=False, font=dict(size=16, color=C["texto"]))],
        )
        figura.update_traces(textfont=dict(size=14, color="#FFFDF6", family="Manrope, sans-serif"))
        plot(figura, "historico_rosca_v3")


def agrupar_medicoes(dados, minutos):
    """Agrupamento real por relógio, mantendo apenas faixas com dados."""
    if dados.empty:
        return pd.DataFrame()
    validos = dados.dropna(subset=["soil_moisture_pct"]).copy()
    validos["janela"] = validos["horario"].dt.floor(f"{minutos}min")
    agrupado = (
        validos.groupby("janela", sort=True)
        .agg(media=("soil_moisture_pct", "mean"), quantidade=("soil_moisture_pct", "size"))
        .reset_index()
    )
    multi_dia = agrupado["janela"].dt.date.nunique() > 1
    formato = "%d/%m %H:%M" if multi_dia else "%H:%M"
    agrupado["rotulo"] = agrupado["janela"].dt.strftime(formato)
    return agrupado


def medias_por_intervalo(dados, minutos):
    with st.container(border=True):
        st.markdown("#### Umidade média por intervalo")
        st.caption(f"Média das medições agrupadas a cada {minutos} minutos.")
        agrupado = agrupar_medicoes(dados, minutos)
        if agrupado.empty:
            st.info("Não existem valores para agrupar.")
            return
        figura = go.Figure(go.Bar(
            x=agrupado["rotulo"], y=agrupado["media"],
            marker=dict(color=C["petroleo"], line=dict(color="#2F5A3A", width=0.6), cornerradius=8),
            customdata=agrupado["quantidade"], width=0.54,
            hovertemplate="<b>%{x}</b><br>Média: %{y:.1f}%<br>%{customdata} leituras<extra></extra>",
        ))
        configurar_plot(figura, altura=365)
        figura.update_xaxes(title_text="Início do intervalo", type="category", tickangle=0)
        figura.update_yaxes(title_text="Média (%)", range=[0, 110], dtick=20)
        if len(agrupado) <= 8:
            figura.update_traces(text=[f"{v:.1f}%" for v in agrupado["media"]],
                                 textposition="outside", textfont=dict(size=13, color=C["verde_escuro"], family="Manrope, sans-serif"))
        plot(figura, "historico_medias_v3")
        if len(agrupado) == 1:
            st.caption(
                "Todas as leituras selecionadas estão na mesma faixa de horário. "
                "Experimente agrupar por 15 minutos ou escolher outra sessão."
            )
        else:
            st.caption(f"{len(agrupado)} intervalos com dados; horários sem medições foram omitidos.")


def tabela_medicoes(dados):
    rotulo_secao("Dados registrados")
    with st.expander(f"Ver tabela detalhada · {len(dados)} registros", expanded=False):
        tabela = dados.copy()
        tabela["Data e horário"] = tabela["horario"].dt.strftime("%d/%m/%Y %H:%M:%S")
        tabela["Condição hídrica"] = tabela["irrigation_status"].map(STATUS).fillna("Não informado")
        colunas = [
            "Data e horário", "soil_moisture_pct", "air_temperature_c",
            "air_humidity_pct", "soil_temperature_c", "Condição hídrica",
        ]
        tabela = tabela[colunas].rename(columns={
            "soil_moisture_pct": "Umidade solo (%)",
            "air_temperature_c": "Temp. ar (°C)",
            "air_humidity_pct": "Umidade ar (%)",
            "soil_temperature_c": "Temp. solo (°C)",
        })
        tabela = tabela.iloc[::-1].reset_index(drop=True)
        st.dataframe(tabela, width="stretch", hide_index=True, height=340)
        csv = tabela.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
        st.download_button(
            "Baixar medições em CSV", data=csv,
            file_name="hortasense_historico.csv", mime="text/csv",
            use_container_width=True,
        )


def main():
    aplicar_estilo()
    # Cabeçalho visual com a mesma identidade da página Visão Geral.
    st.html("""
    <div class="hs-hist-hero">
      <span class="hs-hist-eyebrow">ANÁLISE DE MONITORAMENTO</span>
      <div class="hs-hist-hero-title">Histórico e Irrigação</div>
      <p class="hs-hist-hero-subtitle">
        Explore as medições anteriores, acompanhe as condições hídricas
        e descubra como a umidade do solo variou ao longo dos testes.
      </p>
      <div class="hs-hist-signature">HortaSense · Cultivo inteligente</div>
    </div>
    """)

    periodo = filtros()
    if periodo is None:
        return
    inicio, fim = periodo
    st.html(
        '<div class="hs-hist-period">'
        f'Período consultado: {inicio:%d/%m/%Y} · '
        f'{inicio:%H:%M}–{(fim - timedelta(minutes=1)):%H:%M}'
        '</div>'
    )
    registros = consultar_medicoes_intervalo(inicio, fim)
    if not registros:
        st.info("Nenhuma medição nesse período. Altere a data ou os horários da consulta.")
        return
    dados = preparar_dados(registros)
    if dados.empty or dados["soil_moisture_pct"].dropna().empty:
        st.info("Não há medições válidas de umidade neste período.")
        return

    indicadores(dados)
    rotulo_secao("Análise gráfica")
    dados_grafico, minutos = selecionar_dados_graficos(dados)
    evolucao(dados_grafico)

    esquerda, direita = st.columns(2, gap="medium")
    with esquerda:
        distribuicao(dados_grafico)
    with direita:
        medias_por_intervalo(dados_grafico, minutos)

    tabela_medicoes(dados)


if __name__ == "__main__":
    main()
