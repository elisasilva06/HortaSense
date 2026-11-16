"""HortaSense — Página Visão Geral.

Apresenta as condições ambientais atuais, a classificação
hídrica e o histórico recente do dispositivo ESP32.

Apenas a camada visual foi redesenhada. Consultas ao SQLite,
atualização periódica e gráficos permanecem com sua lógica original.
"""

from datetime import datetime, timezone
from html import escape
from zoneinfo import ZoneInfo

import streamlit as st

from database import consultar_ultimas_medicoes
from components.cards import (
    exibir_estado_hidrico,
    exibir_indicadores,
)
from components.charts import exibir_grafico_umidade


FUSO_LOCAL = ZoneInfo("America/Fortaleza")

# O ESP32 envia medições aproximadamente a cada 5 segundos.
# Esta verificação indica a RECÊNCIA dos dados recebidos,
# e não uma conexão de rede diretamente medida no ESP32.
LIMITE_CONEXAO_SEGUNDOS = 15


def aplicar_estilo_customizado():
    """Estiliza somente os elementos desta página, sem alterar lógica."""
    st.markdown(
        """
        <style>
        /* Dimensionamento geral preserva o padrão multipágina. */
        [data-testid="stMain"] .block-container {
            max-width: 1280px;
            padding-top: 2.1rem;
            padding-bottom: 3.5rem;
        }

        /* Abertura da Visão Geral — verde como protagonista. */
        .hs-vg-header {
            position: relative;
            isolation: isolate;
            overflow: hidden;
            background: linear-gradient(115deg, #2F5A3A 0%, #3E6B42 62%, #668B4A 100%);
            color: #F8F1DC;
            border-radius: 28px 28px 28px 9px;
            padding: clamp(24px, 4vw, 44px);
            margin-bottom: 1.55rem;
            box-shadow: 0 12px 28px rgba(47, 90, 58, .13);
            border: 1px solid rgba(255, 253, 246, .14);
        }
        .hs-vg-header::before,
        .hs-vg-header::after {
            content: "";
            position: absolute;
            pointer-events: none;
            border-radius: 50%;
            z-index: -1;
        }
        .hs-vg-header::before {
            width: 270px;
            height: 270px;
            background: rgba(220, 232, 210, .11);
            right: -88px;
            top: -150px;
        }
        .hs-vg-header::after {
            width: 155px;
            height: 155px;
            border: 2px solid rgba(248, 241, 220, .24);
            right: 35px;
            bottom: -100px;
        }
        .hs-vg-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 9px;
            padding: 7px 13px;
            border: 1px solid rgba(248, 241, 220, .26);
            background: rgba(248, 241, 220, .13);
            border-radius: 100px;
            font: 800 10px/1.25 'Manrope', sans-serif;
            text-transform: uppercase;
            letter-spacing: .12em;
            color: #FFFDF6;
            margin-bottom: 15px;
        }
        .hs-vg-eyebrow-dot {
            width: 8px;
            height: 8px;
            border-radius: 100%;
            background: #C5DF9D;
            flex: 0 0 auto;
        }
        .hs-vg-header .hs-vg-title {
            font-family: 'Bricolage Grotesque', 'Trebuchet MS', sans-serif !important;
            font-size: clamp(32px, 4vw, 50px) !important;
            line-height: 1.05 !important;
            letter-spacing: -.05em !important;
            font-weight: 800 !important;
            color: #FFFDF6 !important;
            margin: 0 !important;
        }
        .hs-vg-header .hs-vg-subtitle {
            font-family: 'Manrope', 'Segoe UI', sans-serif !important;
            font-size: clamp(13px, 1.4vw, 15px) !important;
            line-height: 1.7;
            max-width: 600px;
            color: #EAF2E1 !important;
            margin: 11px 0 0 !important;
        }
        .hs-vg-header-bottom {
            display: flex;
            align-items: center;
            gap: 9px;
            color: #DCE8D2;
            font: 700 11px/1.5 'Manrope', sans-serif;
            margin-top: 23px;
            letter-spacing: .015em;
        }
        .hs-vg-header-bottom span {
            display: block;
            width: 30px;
            height: 3px;
            border-radius: 10px;
            background: #C5DF9D;
        }

        /* Identificação da unidade em superfície de papel com formato orgânico. */
        .hs-vg-device {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 22px;
            flex-wrap: wrap;
            border: 1px solid #D8DFC9;
            background: #FFFDF6;
            border-radius: 23px 23px 23px 8px;
            padding: 21px 24px;
            box-shadow: 0 7px 23px rgba(47, 90, 58, .055);
            margin: .15rem 0 1.1rem;
        }
        .hs-vg-device-left {
            display: flex;
            align-items: center;
            gap: 16px;
            min-width: 0;
            flex: 1 1 320px;
        }
        .hs-vg-device-symbol {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 56px;
            height: 56px;
            border-radius: 19px 19px 19px 6px;
            background: #DCE8D2;
            color: #2F5A3A;
            font: 800 27px/1 'Bricolage Grotesque', sans-serif;
            flex: 0 0 auto;
        }
        .hs-vg-device-tag {
            color: #668B4A;
            font: 800 10px/1.4 'Manrope', sans-serif;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin-bottom: 3px;
        }
        .hs-vg-device-title {
            font: 800 24px/1.13 'Bricolage Grotesque', sans-serif;
            letter-spacing: -.04em;
            color: #2F5A3A;
            margin-bottom: 7px;
        }
        .hs-vg-device-meta {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 6px 10px;
            color: #57664F;
            font: 500 12px/1.65 'Manrope', sans-serif;
        }
        .hs-vg-device-meta strong { color: #2F5A3A; font-weight: 800; }
        .hs-vg-meta-sep { opacity: .55; }
        .hs-vg-status {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 14px;
            border-radius: 100px;
            font: 800 11px/1.4 'Manrope', sans-serif;
            white-space: nowrap;
        }
        .hs-vg-status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex: 0 0 auto;
        }
        .hs-vg-status-fresh {
            color: #256E3C;
            background: #E4F3E0;
            border: 1px solid #B5D7B1;
        }
        .hs-vg-status-fresh .hs-vg-status-dot { background: #2C9B4A; }
        .hs-vg-status-stale {
            color: #765B27;
            background: #FFF0CD;
            border: 1px solid #E6CA89;
        }
        .hs-vg-status-stale .hs-vg-status-dot { background: #B78628; }
        .hs-vg-stale-note { color: #765B27; }

        /* Títulos de seção com pequeno detalhe visual de marca. */
        .hs-vg-section {
            display: flex;
            align-items: center;
            gap: 10px;
            color: #2F5A3A;
            font: 800 11px/1.4 'Manrope', sans-serif;
            letter-spacing: .11em;
            text-transform: uppercase;
            margin: 1.85rem 0 .82rem;
        }
        .hs-vg-section::before {
            content: "";
            display: block;
            width: 6px;
            height: 18px;
            border-radius: 8px;
            background: #8AA730;
        }

        /* Palco do gráfico: destaques apenas nesta página. */
        .hs-vg-chart-intro {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px 16px;
            align-items: flex-start;
            margin-bottom: 5px;
        }
        .hs-vg-chart-eyebrow {
            display: inline-block;
            color: #668B4A;
            font: 800 10px/1.4 'Manrope', sans-serif;
            text-transform: uppercase;
            letter-spacing: .12em;
            margin-bottom: 5px;
        }
        .hs-vg-chart-intro .hs-vg-chart-title {
            color: #2F5A3A !important;
            font: 800 clamp(23px, 2.4vw, 30px)/1.2 'Bricolage Grotesque', sans-serif !important;
            letter-spacing: -.04em;
            margin: 0;
        }
        .hs-vg-chart-intro .hs-vg-chart-subtitle {
            color: #57664F !important;
            font: 500 13px/1.6 'Manrope', sans-serif !important;
            margin: 7px 0 0;
        }
        .hs-vg-chart-pill {
            border: 1px solid #C9DBB7;
            background: #EDF3E5;
            color: #2F5A3A;
            border-radius: 100px;
            padding: 9px 13px;
            font: 800 11px/1.35 'Manrope', sans-serif;
            white-space: nowrap;
        }

        /* Escopo exclusivo: contêiner do gráfico, não outros st.container. */
        .st-key-hs_visao_grafico_principal {
            background: linear-gradient(135deg, #FFFDF6 0%, #F4F7E9 100%);
            border: 1px solid #C9D9BF;
            border-radius: 26px 26px 26px 9px;
            box-shadow: 0 12px 32px rgba(47, 90, 58, .065);
            padding: clamp(15px, 2.3vw, 26px);
            margin-bottom: 1.1rem;
        }
        .st-key-hs_visao_grafico_principal [data-testid="stPlotlyChart"] {
            margin-top: .25rem;
        }
        .st-key-hs_visao_grafico_principal [data-testid="stCaptionContainer"] p {
            color: #57664F !important;
            font-weight: 600;
        }
        @media (max-width: 680px) {
            .hs-vg-header { border-radius: 22px 22px 22px 8px; }
            .hs-vg-device { padding: 18px; }
            .hs-vg-device-symbol { width: 48px; height: 48px; }
            .hs-vg-status { white-space: normal; }
            .hs-vg-meta-sep { display: none; }
            .hs-vg-chart-pill { display: none; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def obter_horario_local(valor):
    """Converte o horário de recebimento para o fuso local."""
    horario_utc = datetime.fromisoformat(valor)
    return horario_utc.astimezone(FUSO_LOCAL)


@st.fragment(run_every="5s")
def atualizar_monitoramento():
    """Atualiza os componentes com as últimas medições."""
    registros = consultar_ultimas_medicoes(100)

    if not registros:
        with st.container(border=True):
            st.info(
                "Nenhuma medição registrada. "
                "Inicie o Wokwi e o receptor MQTT."
            )
        return

    ultima = registros[0]

    # Mesma regra de recência utilizada na versão anterior.
    horario_ultima = datetime.fromisoformat(ultima["received_at"])
    agora = datetime.now(timezone.utc)
    segundos_sem_dados = max(
        0,
        (agora - horario_ultima).total_seconds(),
    )
    conectado = segundos_sem_dados <= LIMITE_CONEXAO_SEGUNDOS
    horario_local = obter_horario_local(ultima["received_at"])

    # Apenas o conteúdo visual do status foi redesenhado.
    if conectado:
        badge_html = (
            '<span class="hs-vg-status hs-vg-status-fresh">'
            '<span class="hs-vg-status-dot"></span>'
            'Dados recentes'
            '</span>'
        )
        nota_status = ""
    else:
        badge_html = (
            '<span class="hs-vg-status hs-vg-status-stale">'
            '<span class="hs-vg-status-dot"></span>'
            'Sem dados recentes'
            '</span>'
        )
        nota_status = ' <span class="hs-vg-stale-note">· Última leitura armazenada</span>'

    # Evita interpretar conteúdo de origem externa como HTML.
    dispositivo = escape(str(ultima["device"]))
    ultima_medicao_texto = escape(
        horario_local.strftime("%d/%m/%Y às %H:%M:%S")
    )

    st.html(
        f"""
        <div class="hs-vg-device">
            <div class="hs-vg-device-left">
                <div class="hs-vg-device-symbol" aria-hidden="true">01</div>
                <div>
                    <div class="hs-vg-device-tag">Unidade monitorada</div>
                    <div class="hs-vg-device-title">Horta 01</div>
                    <div class="hs-vg-device-meta">
                        <span>Dispositivo: <strong>{dispositivo}</strong></span>
                        <span class="hs-vg-meta-sep">·</span>
                        <span>Última medição: {ultima_medicao_texto}</span>
                        {nota_status}
                    </div>
                </div>
            </div>
            <div>{badge_html}</div>
        </div>
        """,
    )

    st.markdown(
        '<div class="hs-vg-section">Indicadores ambientais</div>',
        unsafe_allow_html=True,
    )
    exibir_indicadores(ultima)

    st.markdown(
        '<div class="hs-vg-section">Classificação hídrica</div>',
        unsafe_allow_html=True,
    )
    exibir_estado_hidrico(ultima["irrigation_status"])

    st.markdown(
        '<div class="hs-vg-section">Histórico recente</div>',
        unsafe_allow_html=True,
    )

    # Só mudou o contêiner e o cabeçalho. A chamada do Plotly é a mesma.
    with st.container(key="hs_visao_grafico_principal"):
        st.markdown(
            """
            <div class="hs-vg-chart-intro">
                <div>
                    <span class="hs-vg-chart-eyebrow">Monitoramento do solo</span>
                    <h2 class="hs-vg-chart-title">Evolução da umidade do solo</h2>
                    <p class="hs-vg-chart-subtitle">
                        Acompanhe as medições registradas e selecione o período desejado.
                    </p>
                </div>
                <span class="hs-vg-chart-pill">Histórico recente</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        exibir_grafico_umidade(registros)


def main():
    """Define a estrutura principal da Visão Geral."""
    aplicar_estilo_customizado()

    st.markdown(
        """
        <header class="hs-vg-header">
            <div class="hs-vg-eyebrow">
                <span class="hs-vg-eyebrow-dot"></span>
                Painel de monitoramento
            </div>
            <h1 class="hs-vg-title">Visão Geral</h1>
            <p class="hs-vg-subtitle">
                As condições da sua horta em um só lugar: sensores,
                umidade do solo e histórico de monitoramento.
            </p>
            <div class="hs-vg-header-bottom">
                <span></span> HortaSense · Cultivo inteligente
            </div>
        </header>
        """,
        unsafe_allow_html=True,
    )
    atualizar_monitoramento()


main()
