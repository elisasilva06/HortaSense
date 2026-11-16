
"""
HortaSense — Aplicação principal.

Configura a navegação multipáginas e a identidade
visual da barra lateral do dashboard.

Inicializa o banco de dados SQLite, quando necessário,
antes de executar as páginas da aplicação.

As funcionalidades permanecem separadas nos módulos
da pasta pages.
"""

import streamlit as st

from database import inicializar_banco

from hortasense_theme import aplicar_tema

# Configuração inicial da aplicação.
st.set_page_config(
    page_title="HortaSense | Monitoramento Ambiental",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Inicializa os recursos e configura a navegação."""

    aplicar_tema()

    # Garante que a estrutura do banco SQLite exista.
    #
    # Em uma instalação nova ou no Streamlit Community Cloud,
    # o banco pode ainda não ter sido criado.
    #
    # A função deve criar a tabela somente quando necessário,
    # preservando os registros existentes.
    inicializar_banco()

    # Registro das quatro páginas do dashboard.
    visao_geral = st.Page(
        "pages/visao_geral.py",
        title="Visão Geral",
        icon=":material/dashboard:",
        default=True,
    )

    historico = st.Page(
        "pages/historico.py",
        title="Histórico e Irrigação",
        icon=":material/show_chart:",
    )

    alertas = st.Page(
        "pages/alertas.py",
        title="Alertas e Ocorrências",
        icon=":material/notifications:",
    )

    configuracoes = st.Page(
        "pages/configuracoes.py",
        title="Configurações",
        icon=":material/settings:",
    )

    # Registra as páginas e oculta a navegação automática.
    navegacao = st.navigation(
        [visao_geral, historico, alertas, configuracoes],
        position="hidden",
    )

    # Construção da barra lateral personalizada.
    with st.sidebar:

        # Identidade visual da plataforma.
        st.markdown("## 🌱 HortaSense")
        st.caption("Monitoramento Ambiental")

        st.divider()

        st.caption("MENU PRINCIPAL")

        # Links de navegação entre as páginas.
        st.page_link(
            visao_geral,
            label="Visão Geral",
            icon=":material/dashboard:",
            width="stretch",
        )

        st.page_link(
            historico,
            label="Histórico e Irrigação",
            icon=":material/show_chart:",
            width="stretch",
        )

        st.page_link(
            alertas,
            label="Alertas e Ocorrências",
            icon=":material/notifications:",
            width="stretch",
        )

        st.page_link(
            configuracoes,
            label="Configurações",
            icon=":material/settings:",
            width="stretch",
        )

        st.divider()

        # Informações fixas do dispositivo.
        st.caption("DISPOSITIVO")
        st.markdown("**ESP32 • HortaSense 01**")
        st.caption("MVP IoT — Microcontroladores")

    # Executa a página selecionada.
    navegacao.run()


if __name__ == "__main__":
    main()
