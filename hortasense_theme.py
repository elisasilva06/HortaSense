"""HortaSense — identidade visual global (v3).

Camada exclusivamente visual. Importar aplicar_tema() no app.py,
depois de st.set_page_config(). Não altera navegação, leituras,
consultas, estado de sessão ou figuras Plotly.

Nota: menus de seleção e calendários são renderizados em portais
separados do conteúdo da página; seus seletores são intencionais.
"""

import streamlit as st


PALETA = {
    "matcha": "#668B4A",
    "matcha_vivo": "#8AA730",
    "verde_profundo": "#2F5A3A",
    "verde_folha": "#456D45",
    "verde_suave": "#DCE8D2",
    "verde_palido": "#EDF3E5",
    "creme": "#F8F1DC",
    "papel": "#FFFDF6",
    "branco": "#FFFFFF",
    "mocha": "#5A4636",
    "chocolate": "#331915",
    "texto": "#27382B",
    "texto_secundario": "#57664F",
    "borda": "#D8DFC9",
    "adequado": "#4E7A3E",
    "atencao": "#98651F",
    "critico": "#A24D3B",
}


def aplicar_tema():
    """Injeta estilos globais sem modificar a lógica da aplicação."""
    st.markdown(
        """<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700;12..96,800&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
  --hs-matcha: #668B4A;
  --hs-matcha-vivo: #8AA730;
  --hs-verde-profundo: #2F5A3A;
  --hs-verde-folha: #456D45;
  --hs-verde-suave: #DCE8D2;
  --hs-verde-palido: #EDF3E5;
  --hs-creme: #F8F1DC;
  --hs-papel: #FFFDF6;
  --hs-branco: #FFFFFF;
  --hs-mocha: #5A4636;
  --hs-chocolate: #331915;
  --hs-texto: #27382B;
  --hs-texto-secundario: #57664F;
  --hs-borda: #D8DFC9;
  --hs-adequado: #4E7A3E;
  --hs-atencao: #98651F;
  --hs-critico: #A24D3B;
  --hs-display: 'Bricolage Grotesque', 'Trebuchet MS', sans-serif;
  --hs-interface: 'Manrope', 'Segoe UI', sans-serif;
}

/* Superfícies da marca. */
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
  background-color: var(--hs-creme) !important;
  color: var(--hs-texto);
}
.stApp, .stApp button, .stApp input, .stApp textarea,
.stApp label, .stApp p, .stApp li {
  font-family: var(--hs-interface) !important;
}
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3,
[data-testid="stMain"] h4 {
  font-family: var(--hs-display) !important;
  color: var(--hs-verde-profundo) !important;
  font-weight: 800 !important;
  letter-spacing: -.035em;
}
[data-testid="stMain"] h1 {
  letter-spacing: -.055em;
  line-height: 1.12;
}
[data-testid="stMain"] p,
[data-testid="stMain"] li,
[data-testid="stMain"] label {
  color: var(--hs-texto);
}
[data-testid="stMain"] [data-testid="stCaptionContainer"],
[data-testid="stMain"] [data-testid="stCaptionContainer"] p {
  color: var(--hs-texto-secundario) !important;
}
[data-testid="stMain"] hr {
  border-color: var(--hs-borda) !important;
}

/* Navegação: verde profundo e estado ativo com assinatura matcha. */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child {
  background-color: var(--hs-verde-profundo) !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] a,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
  color: var(--hs-creme) !important;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
  opacity: .86;
}
[data-testid="stSidebar"] svg { color: var(--hs-creme); }
[data-testid="stSidebar"] hr { border-color: rgba(248,241,220,.27) !important; }
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"],
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
  border-radius: 16px !important;
  border-left: 3px solid transparent;
  transition: background-color .15s ease, border-color .15s ease;
}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover,
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
  background-color: rgba(248,241,220,.13) !important;
}
[data-testid="stSidebar"] a[aria-current="page"],
[data-testid="stSidebar"] [data-testid="stPageLink"] [aria-current="page"] {
  background-color: rgba(248,241,220,.18) !important;
  border-left-color: #C5DF9D !important;
}

/* Containers Streamlit: contornos e curvas, sem alterar HTML customizado. */
[data-testid="stMain"] [data-testid="stForm"] {
  border: 1px solid var(--hs-borda) !important;
  border-radius: 22px !important;
  background: rgba(255,253,246,.54) !important;
}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 22px !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--hs-display) !important;
  color: var(--hs-verde-profundo) !important;
  font-weight: 800 !important;
}

/* Botões: tratar também spans internos, para impedir texto escuro sobre verde. */
.stApp div.stButton > button[kind="primary"],
.stApp div.stFormSubmitButton > button[kind="primary"],
.stApp div.stDownloadButton > button[kind="primary"] {
  background: var(--hs-verde-profundo) !important;
  border: 1px solid var(--hs-verde-profundo) !important;
  border-radius: 16px !important;
  color: var(--hs-papel) !important;
  font-weight: 800 !important;
  box-shadow: 0 5px 13px rgba(47,90,58,.12) !important;
}
.stApp div.stButton > button[kind="primary"] *,
.stApp div.stFormSubmitButton > button[kind="primary"] *,
.stApp div.stDownloadButton > button[kind="primary"] * {
  color: var(--hs-papel) !important;
}
.stApp div.stButton > button[kind="primary"]:hover,
.stApp div.stFormSubmitButton > button[kind="primary"]:hover,
.stApp div.stDownloadButton > button[kind="primary"]:hover {
  background: var(--hs-matcha) !important;
  border-color: var(--hs-matcha) !important;
}
.stApp div.stButton > button[kind="secondary"],
.stApp div.stDownloadButton > button[kind="secondary"] {
  background: var(--hs-papel) !important;
  color: var(--hs-verde-profundo) !important;
  border: 1px solid var(--hs-borda) !important;
  border-radius: 16px !important;
}
.stApp button:focus-visible,
.stApp input:focus-visible,
.stApp textarea:focus-visible {
  outline: 2px solid var(--hs-matcha) !important;
  outline-offset: 2px;
}

/* Campos: branco quente, foco matcha e texto bem contrastado. */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stTimeInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div {
  background-color: var(--hs-papel) !important;
  color: var(--hs-texto) !important;
  border-color: var(--hs-borda) !important;
  border-radius: 16px !important;
  box-shadow: none !important;
}
[data-testid="stMain"] [data-baseweb="select"] span,
[data-testid="stMain"] [data-baseweb="select"] input {
  color: var(--hs-texto) !important;
}
[data-testid="stMain"] [data-baseweb="select"] svg,
[data-testid="stDateInput"] svg,
[data-testid="stTimeInput"] svg {
  color: var(--hs-verde-profundo) !important;
  fill: currentColor;
}
[data-testid="stMain"] input::placeholder,
[data-testid="stMain"] textarea::placeholder {
  color: var(--hs-texto-secundario) !important;
  opacity: .9;
}
[data-testid="stMain"] [data-baseweb="select"] > div:focus-within,
[data-testid="stDateInput"] input:focus,
[data-testid="stTimeInput"] input:focus {
  border-color: var(--hs-matcha) !important;
  box-shadow: 0 0 0 2px rgba(102,139,74,.15) !important;
}

/* Popovers vivem fora do stMain: estilizar com escopo nos papéis corretos. */
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] [data-baseweb="menu"],
[data-baseweb="popover"] [data-baseweb="calendar"],
[data-baseweb="popover"] [data-baseweb="datepicker"] {
  background: var(--hs-papel) !important;
  color: var(--hs-texto) !important;
  border-radius: 18px !important;
  box-shadow: 0 12px 28px rgba(47,90,58,.14) !important;
}
[data-baseweb="popover"] [role="option"] {
  font-family: var(--hs-interface) !important;
  color: var(--hs-texto) !important;
  border-radius: 10px !important;
}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [role="option"][aria-selected="true"] {
  background: var(--hs-verde-suave) !important;
  color: var(--hs-verde-profundo) !important;
}
[data-baseweb="popover"] [data-baseweb="calendar"] button[aria-selected="true"] {
  background-color: var(--hs-verde-profundo) !important;
  color: var(--hs-papel) !important;
  border-radius: 50% !important;
}

/* Tabela e áreas expandíveis. */
[data-testid="stDataFrame"],
[data-testid="stExpander"] {
  border-color: var(--hs-borda) !important;
  border-radius: 18px !important;
}
[data-testid="stExpander"] summary {
  color: var(--hs-verde-profundo) !important;
  font-weight: 700;
}

@media (max-width: 768px) {
  [data-testid="stMain"] h1 { font-size: 2rem !important; }
}
</style>""",
        unsafe_allow_html=True,
    )
