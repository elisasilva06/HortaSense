"""
HortaSense — Página Visão Geral.

Apresenta as condições ambientais atuais, a classificação
hídrica e o histórico recente do dispositivo ESP32.

As informações são consultadas diretamente no SQLite.
"""

from datetime import datetime, timezone
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
# O limite de 15 segundos será utilizado inicialmente
# para identificar dados desatualizados.
LIMITE_CONEXAO_SEGUNDOS = 15


def aplicar_estilo_customizado():
    """Injeta paleta limpa em branco e tons de verde."""
    st.markdown(
        """
        <style>
        /* Fundo geral limpo em branco suave com leve toque botânico */
        .stApp {
            background-color: #F7FAF8;
        }

        .block-container {
            padding-top: 2.2rem;
            padding-bottom: 3rem;
            max-width: 1120px;
        }

        /* Cabeçalho da página */
        .hs-page-header {
            margin-bottom: 1.75rem;
            padding-bottom: 1.1rem;
            border-bottom: 1px solid #E2ECE6;
        }
        .hs-page-title {
            font-size: 1.95rem;
            font-weight: 700;
            color: #132A1E;
            letter-spacing: -0.025em;
            margin: 0;
            line-height: 1.2;
        }
        .hs-page-subtitle {
            font-size: 0.95rem;
            color: #526B5D;
            margin-top: 0.35rem;
        }

        /* Card branco do dispositivo com acento lateral verde */
        .hs-device-card {
            background-color: #FFFFFF;
            border: 1px solid #DCE8E1;
            border-left: 4px solid #1B6B46;
            border-radius: 12px;
            padding: 1.2rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
            box-shadow: 0 2px 8px rgba(19, 42, 30, 0.03);
            margin-bottom: 0.5rem;
        }
        .hs-device-title {
            font-size: 1.18rem;
            font-weight: 700;
            color: #132A1E;
            margin: 0 0 0.3rem 0;
        }
        .hs-device-meta {
            font-size: 0.85rem;
            color: #526B5D;
            display: flex;
            align-items: center;
            gap: 0.65rem;
            flex-wrap: wrap;
        }
        .hs-device-meta strong {
            color: #1B6B46;
            font-weight: 600;
        }

        /* Badges de status minimalistas */
        .hs-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.4rem 0.95rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.01em;
        }
        .hs-badge-online {
            background-color: #ECF7F1;
            color: #166534;
            border: 1px solid #BCE3CC;
        }
        .hs-badge-offline {
            background-color: #F4F6F5;
            color: #4B5E54;
            border: 1px solid #D5DFD9;
        }
        .hs-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            display: inline-block;
        }
        .hs-dot-online {
            background-color: #16A34A;
            box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.18);
        }
        .hs-dot-offline {
            background-color: #7C8F85;
        }

        /* Títulos de seção em verde-musgo discreto */
        .hs-section-label {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            color: #2E6F4E;
            margin: 1.75rem 0 0.75rem 0;
        }

        /* Containers brancos unificados (Classificação Hídrica e Gráfico) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FFFFFF !important;
            border-radius: 12px !important;
            border: 1px solid #DCE8E1 !important;
            box-shadow: 0 2px 8px rgba(19, 42, 30, 0.03) !important;
            padding: 0.5rem !important;
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

    # Calcula há quanto tempo a última medição foi recebida.
    horario_ultima = datetime.fromisoformat(
        ultima["received_at"]
    )

    agora = datetime.now(timezone.utc)

    segundos_sem_dados = max(
        0,
        (agora - horario_ultima).total_seconds(),
    )

    conectado = (
        segundos_sem_dados <= LIMITE_CONEXAO_SEGUNDOS
    )

    horario_local = obter_horario_local(
        ultima["received_at"]
    )

    # Identificação e estado do dispositivo.
    if conectado:
        badge_html = (
            '<span class="hs-badge hs-badge-online">'
            '<span class="hs-dot hs-dot-online"></span>'
            "ESP32 conectado"
            "</span>"
        )
        nota_status = ""
    else:
        badge_html = (
            '<span class="hs-badge hs-badge-offline">'
            '<span class="hs-dot hs-dot-offline"></span>'
            "ESP32 sem dados recentes"
            "</span>"
        )
        nota_status = " • Exibindo última leitura armazenada"

    st.markdown(
        f"""
        <div class="hs-device-card">
            <div>
                <div class="hs-device-title">Horta 01</div>
                <div class="hs-device-meta">
                    <span>Dispositivo: <strong>{ultima['device']}</strong></span>
                    <span>•</span>
                    <span>Última medição: {horario_local.strftime('%d/%m/%Y às %H:%M:%S')}{nota_status}</span>
                </div>
            </div>
            <div>{badge_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Indicadores ambientais.
    st.markdown(
        '<div class="hs-section-label">Indicadores Ambientais</div>',
        unsafe_allow_html=True,
    )

    exibir_indicadores(ultima)

    # Estado de atenção hídrica.
    st.markdown(
        '<div class="hs-section-label">Classificação Hídrica</div>',
        unsafe_allow_html=True,
    )

    exibir_estado_hidrico(
        ultima["irrigation_status"]
    )

    # Histórico resumido da umidade do solo.
    st.markdown(
        '<div class="hs-section-label">Histórico Recente</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown("#### Evolução da umidade do solo")
        st.caption(
            "Acompanhe as variações da umidade do solo "
            "e selecione o período desejado."
        )

        exibir_grafico_umidade(registros)


def main():
    """Define a estrutura principal da Visão Geral."""

    aplicar_estilo_customizado()

    st.markdown(
        """
        <div class="hs-page-header">
            <h1 class="hs-page-title">Visão Geral</h1>
            <p class="hs-page-subtitle">
                Acompanhe as condições ambientais da horta e o funcionamento do dispositivo ESP32.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    atualizar_monitoramento()


main()