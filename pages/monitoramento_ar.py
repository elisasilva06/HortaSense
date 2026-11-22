"""HortaSense — Monitoramento do ar.

Página independente para temperatura do ar e umidade relativa do ar.
Consulta somente leitura por meio das funções já existentes em database.py.
Não altera o Supabase, as demais páginas nem os receptores de telemetria.
"""

from datetime import datetime, time, timedelta
from html import escape
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import plotly.graph_objects as go
import streamlit as st

from database import consultar_medicoes_intervalo, consultar_ultimas_medicoes
from hortasense_theme import aplicar_tema


FUSO_LOCAL = ZoneInfo("America/Fortaleza")
LIMITE_LACUNA_SEGUNDOS = 20
MAXIMO_REGISTROS_RECENTES = 1000

CORES = {
    "profundo": "#2F5A3A",
    "verde": "#668B4A",
    "matcha": "#8AA730",
    "creme": "#F8F1DC",
    "papel": "#FFFDF6",
    "texto": "#27382B",
    "secundario": "#57664F",
    "borda": "#D8DFC9",
    "temperatura": "#B87955",
    "temperatura_claro": "#F6E6D8",
    "umidade": "#4E8768",
    "umidade_claro": "#E4F0E5",
}

PERIODOS = {
    "Últimos 5 minutos": ("tempo", 5),
    "Últimos 15 minutos": ("tempo", 15),
    "Últimos 30 minutos": ("tempo", 30),
    "Última 1 hora": ("tempo", 60),
    "Últimas 20 medições": ("quantidade", 20),
    "Últimas 100 medições": ("quantidade", 100),
    "Consultar uma data": ("data", None),
}


def aplicar_estilo():
    """Estilos restritos à página; seguem a identidade da Visão Geral."""
    st.html(
        """
        <style>
        .hs-ar-header {
            position:relative;isolation:isolate;overflow:hidden;
            background:linear-gradient(115deg,#2F5A3A 0%,#3E6B42 62%,#668B4A 100%);
            color:#F8F1DC;border-radius:28px 28px 28px 9px;
            padding:clamp(24px,4vw,44px);margin-bottom:1.55rem;
            box-shadow:0 12px 28px rgba(47,90,58,.13);
            border:1px solid rgba(255,253,246,.14);
        }
        .hs-ar-header::before,.hs-ar-header::after {
            content:"";position:absolute;pointer-events:none;border-radius:50%;z-index:-1;
        }
        .hs-ar-header::before {
            width:270px;height:270px;background:rgba(220,232,210,.11);
            right:-88px;top:-150px;
        }
        .hs-ar-header::after {
            width:155px;height:155px;border:2px solid rgba(248,241,220,.24);
            right:35px;bottom:-100px;
        }
        .hs-ar-tag {
            display:inline-flex;align-items:center;gap:9px;
            padding:7px 13px;border:1px solid rgba(248,241,220,.26);
            background:rgba(248,241,220,.13);border-radius:100px;
            font:800 10px/1.25 'Manrope',sans-serif;
            text-transform:uppercase;letter-spacing:.12em;color:#FFFDF6;margin-bottom:15px;
        }
        .hs-ar-tag-dot {width:8px;height:8px;background:#C5DF9D;border-radius:50%;flex:none;}
        /* Mais específico que o CSS global, que define cores de todos os h1/p. */
        [data-testid="stMain"] .hs-ar-header h1.hs-ar-title {
            font-family:'Bricolage Grotesque','Trebuchet MS',sans-serif !important;
            font-size:clamp(32px,4vw,50px) !important;
            font-weight:800 !important;line-height:1.05 !important;
            letter-spacing:-.05em !important;color:#FFFDF6 !important;margin:0 !important;
        }
        [data-testid="stMain"] .hs-ar-header p.hs-ar-description {
            font-family:'Manrope','Segoe UI',sans-serif !important;
            font-size:clamp(13px,1.4vw,15px) !important;
            font-weight:500 !important;line-height:1.7 !important;
            max-width:660px;color:#EAF2E1 !important;margin:11px 0 0 !important;
        }
        .hs-ar-signature {
            display:flex;gap:9px;align-items:center;margin-top:23px;
            color:#DCE8D2;font:700 11px/1.5 'Manrope',sans-serif;
        }
        .hs-ar-signature::before {
            content:"";width:30px;height:3px;background:#C5DF9D;border-radius:10px;
        }
        .hs-ar-section {
            display:flex;align-items:center;gap:10px;color:#2F5A3A;
            font:800 11px/1.4 'Manrope',sans-serif;
            text-transform:uppercase;letter-spacing:.11em;margin:1.75rem 0 .82rem;
        }
        .hs-ar-section::before {
            content:"";width:6px;height:18px;background:#8AA730;border-radius:8px;
        }
        .hs-ar-panel {
            position:relative;overflow:hidden;background:#FFFDF6;
            border:1px solid #D8DFC9;border-radius:24px 24px 24px 9px;
            padding:20px 22px;box-shadow:0 8px 24px rgba(47,90,58,.05);
            font-family:'Manrope','Segoe UI',sans-serif;
        }
        .hs-ar-panel::after {
            content:"";position:absolute;width:110px;height:110px;border-radius:50%;
            background:#EDF3E5;right:-62px;top:-65px;pointer-events:none;
        }
        .hs-ar-panel-title {
            color:#2F5A3A;font:800 clamp(21px,2.1vw,27px)/1.2
            'Bricolage Grotesque','Trebuchet MS',sans-serif;
            letter-spacing:-.035em;margin:0 0 5px;
        }
        .hs-ar-panel-desc {
            color:#57664F;font:500 12px/1.65 'Manrope',sans-serif;margin:0;
        }
        .hs-ar-card {
            position:relative;box-sizing:border-box;overflow:hidden;
            background:#FFFDF6;border:1px solid #D8DFC9;
            border-radius:24px 24px 24px 9px;min-height:190px;
            padding:22px 22px 20px;
            box-shadow:0 7px 22px rgba(47,90,58,.045);
            font-family:'Manrope','Segoe UI',sans-serif;
        }
        .hs-ar-card-orbit {
            position:absolute;width:132px;height:132px;right:-63px;top:-59px;
            border-radius:50%;opacity:.75;
        }
        .hs-ar-card-top {position:relative;display:flex;justify-content:space-between;gap:8px;}
        .hs-ar-card-tag {font-size:10px;font-weight:800;letter-spacing:.12em;}
        .hs-ar-card-index {font-size:11px;font-weight:800;color:#57664F;}
        .hs-ar-card-label {position:relative;color:#57664F;font-size:13px;font-weight:650;margin-top:19px;}
        .hs-ar-card-value {
            position:relative;color:#2F5A3A;
            font:800 clamp(30px,3vw,41px)/1.15 'Bricolage Grotesque',sans-serif;
            letter-spacing:-.05em;margin-top:10px;
        }
        .hs-ar-card-unit {font:700 16px/1.3 'Manrope',sans-serif;letter-spacing:0;}
        .hs-ar-card-foot {position:relative;color:#57664F;font-size:11px;line-height:1.6;margin-top:7px;}
        .hs-ar-card-rule {width:58px;height:5px;border-radius:12px;margin-top:16px;}
        .hs-ar-statstrip {
            display:flex;gap:10px;flex-wrap:wrap;margin:10px 0 2px;
            font:600 12px/1.5 'Manrope',sans-serif;color:#57664F;
        }
        .hs-ar-statstrip span {
            display:inline-block;padding:6px 11px;border:1px solid #D8DFC9;
            border-radius:999px;background:#F4F7E9;
        }
        .hs-ar-statstrip strong {color:#2F5A3A;}
        .hs-ar-info-rail {
            display:flex;align-items:center;justify-content:space-between;
            gap:15px;flex-wrap:wrap;box-sizing:border-box;
            background:#FFFDF6;border:1px solid #D8DFC9;
            border-radius:22px 22px 22px 8px;padding:17px 22px;
            box-shadow:0 6px 18px rgba(47,90,58,.045);
            font-family:'Manrope','Segoe UI',sans-serif;
        }
        .hs-ar-info-kicker {color:#668B4A;font-size:10px;font-weight:800;
            text-transform:uppercase;letter-spacing:.12em;}
        .hs-ar-info-title {color:#2F5A3A;font-size:17px;font-weight:800;
            font-family:'Bricolage Grotesque',sans-serif;margin-top:4px;}
        .hs-ar-info-sub {color:#57664F;font-size:12px;margin-top:5px;}
        .hs-ar-info-chip {display:inline-flex;align-items:center;gap:8px;
            border-radius:100px;background:#EDF3E5;border:1px solid #C9DBB7;
            padding:9px 13px;font-size:11px;font-weight:800;color:#2F5A3A;}
        .hs-ar-info-chip::before {content:"";width:7px;height:7px;border-radius:50%;background:#668B4A;}
        .hs-ar-mini {
            position:relative;overflow:hidden;min-height:119px;box-sizing:border-box;
            background:#FFFDF6;border:1px solid #D8DFC9;border-radius:20px 20px 20px 7px;
            padding:18px 18px 15px;box-shadow:0 6px 20px rgba(47,90,58,.04);
            font-family:'Manrope','Segoe UI',sans-serif;
        }
        .hs-ar-mini::before {content:"";position:absolute;width:80px;height:80px;
            border-radius:50%;right:-40px;top:-40px;background:var(--accent-bg,#EDF3E5);}
        .hs-ar-mini-label {position:relative;color:#57664F;font-size:11px;font-weight:700;}
        .hs-ar-mini-val {position:relative;font:800 clamp(20px,2.1vw,29px)/1.2
            'Bricolage Grotesque',sans-serif;color:#2F5A3A;margin-top:10px;}
        .hs-ar-mini-foot {position:relative;color:#57664F;font-size:10px;margin-top:6px;}
        .hs-ar-mini-rule {height:4px;width:40px;border-radius:10px;margin-top:10px;background:var(--accent,#668B4A);}
        .hs-ar-insight {
            background:linear-gradient(110deg,#E4EFE2 0%,#F1F5DF 100%);
            border:1px solid #BDD3B7;border-radius:23px 23px 23px 8px;
            padding:19px 22px;color:#2F5A3A;font-family:'Manrope',sans-serif;
        }
        .hs-ar-insight-title {font:800 16px 'Bricolage Grotesque',sans-serif;margin-bottom:7px;}
        .hs-ar-insight-copy {color:#45654A;font-size:12px;line-height:1.7;}
        .st-key-hs_ar_relacao {
            border:1px solid #C9D9BF;border-radius:26px 26px 26px 9px;
            background:linear-gradient(135deg,#FFFDF6 0%,#F4F7E9 100%);
            padding:clamp(15px,2.3vw,26px);margin-bottom:.9rem;
            box-shadow:0 10px 28px rgba(47,90,58,.055);
        }
        .st-key-hs_ar_consulta,
        .st-key-hs_ar_grafico_temperatura,
        .st-key-hs_ar_grafico_umidade {
            border:1px solid #C9D9BF;border-radius:26px 26px 26px 9px;
            background:linear-gradient(135deg,#FFFDF6 0%,#F4F7E9 100%);
            padding:clamp(15px,2.3vw,26px);
            box-shadow:0 10px 28px rgba(47,90,58,.055);
            margin-bottom:.9rem;
        }
        .st-key-hs_ar_consulta [data-testid="stWidgetLabel"] p {
            color:#2F5A3A;font-weight:750;
        }
        .st-key-hs_ar_consulta .stSelectbox,
        .st-key-hs_ar_consulta .stDateInput {max-width:520px;}
        @media(max-width:680px) {
            .hs-ar-header {border-radius:22px 22px 22px 8px;}
            .hs-ar-card {min-height:175px;}
        }
        </style>
        """
    )


def cabecalho():
    st.html(
        """
        <header class="hs-ar-header">
            <div class="hs-ar-tag"><span class="hs-ar-tag-dot"></span>
                Monitoramento ambiental</div>
            <h1 class="hs-ar-title">Condições do Ar</h1>
            <p class="hs-ar-description">
                Acompanhe a temperatura e a umidade relativa do ar na sua horta,
                com indicadores e gráficos das medições registradas.
            </p>
            <div class="hs-ar-signature">HortaSense · Cultivo inteligente</div>
        </header>
        """
    )


def secao(texto):
    st.html(f'<div class="hs-ar-section">{escape(texto)}</div>')


def preparar_medicoes(registros):
    """Converte os dados obtidos pela API sem alterar os registros originais."""
    dados = pd.DataFrame(registros)
    esperadas = {"received_at", "air_temperature_c", "air_humidity_pct"}
    faltantes = esperadas.difference(dados.columns)
    if faltantes:
        return pd.DataFrame(), ", ".join(sorted(faltantes))

    dados = dados.copy()
    dados["horario"] = pd.to_datetime(
        dados["received_at"], utc=True, errors="coerce"
    ).dt.tz_convert(FUSO_LOCAL)
    for coluna in ("air_temperature_c", "air_humidity_pct"):
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")

    dados = dados.dropna(subset=["horario"]).copy()
    ordenacao = ["horario", "id"] if "id" in dados.columns else ["horario"]
    dados = dados.sort_values(ordenacao).reset_index(drop=True)
    return dados, None


def consultar_periodo(periodo, dia):
    """Reutiliza SOMENTE as funções já públicas de database.py."""
    tipo, tamanho = PERIODOS[periodo]
    if tipo == "data":
        inicio = datetime.combine(dia, time.min, tzinfo=FUSO_LOCAL)
        fim = inicio + timedelta(days=1)
        return consultar_medicoes_intervalo(inicio, fim), tipo, tamanho
    return consultar_ultimas_medicoes(MAXIMO_REGISTROS_RECENTES), tipo, tamanho


def filtrar_periodo(dados, tipo, tamanho):
    if dados.empty:
        return dados
    if tipo == "quantidade":
        return dados.tail(tamanho).copy()
    if tipo == "tempo":
        # Referência na medição mais recente, como nos gráficos da Visão Geral.
        limite = dados["horario"].max() - pd.Timedelta(minutes=tamanho)
        return dados.loc[dados["horario"] >= limite].copy()
    return dados.copy()


def cartao(titulo, valor, unidade, etiqueta, indice, cor, fundo, detalhe):
    st.html(
        f"""
        <div class="hs-ar-card">
          <div class="hs-ar-card-orbit" style="background:{fundo};"></div>
          <div class="hs-ar-card-top">
            <span class="hs-ar-card-tag" style="color:{cor};">{escape(etiqueta)}</span>
            <span class="hs-ar-card-index">{escape(indice)}</span>
          </div>
          <div class="hs-ar-card-label">{escape(titulo)}</div>
          <div class="hs-ar-card-value">{escape(valor)}
            <span class="hs-ar-card-unit">{escape(unidade)}</span></div>
          <div class="hs-ar-card-foot">{escape(detalhe)}</div>
          <div class="hs-ar-card-rule" style="background:{cor};"></div>
        </div>
        """
    )


def formatar_numero(valor, casas=1):
    if pd.isna(valor):
        return "—"
    return f"{float(valor):.{casas}f}".replace(".", ",")


def configurar_plot(figura, titulo_eixo, cor, eixo_percentual=False):
    figura.update_layout(
        height=450,
        margin=dict(l=28, r=36, t=33, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color=CORES["texto"], size=13),
        hovermode="closest",
        showlegend=False,
        dragmode=False,
        hoverlabel=dict(
            bgcolor=CORES["papel"],
            bordercolor=CORES["borda"],
            font=dict(family="Manrope, sans-serif", color=CORES["texto"], size=13),
        ),
    )
    figura.update_xaxes(
        showgrid=False,
        zeroline=False,
        title_font=dict(color=CORES["secundario"]),
        tickfont=dict(color=CORES["secundario"]),
    )
    figura.update_yaxes(
        title_text=titulo_eixo,
        gridcolor=CORES["borda"],
        zeroline=False,
        ticksuffix="%" if eixo_percentual else " °C",
        title_font=dict(color=CORES["secundario"]),
        tickfont=dict(color=CORES["secundario"]),
    )
    if eixo_percentual:
        figura.update_yaxes(range=[-6, 106], tickvals=[0, 20, 40, 60, 80, 100])
    return figura


def grafico(dados, campo, titulo, subtitulo, cor, unidade, tipo, chave):
    with st.container(key=chave):
        st.html(
            f"""
            <div class="hs-ar-panel-title">{escape(titulo)}</div>
            <p class="hs-ar-panel-desc">{escape(subtitulo)}</p>
            """
        )
        valores = dados.dropna(subset=[campo]).copy().reset_index(drop=True)
        if valores.empty:
            st.info("Não há leituras válidas dessa variável na seleção.")
            return

        sequencia = tipo == "quantidade"
        x = list(range(1, len(valores) + 1)) if sequencia else valores["horario"].tolist()
        y = valores[campo].astype(float).tolist()
        horarios = valores["horario"].dt.strftime("%d/%m/%Y às %H:%M:%S").tolist()
        linhas_x, linhas_y = [], []
        for i, (posicao, valor) in enumerate(zip(x, y)):
            if not sequencia and i > 0:
                intervalo = (valores.loc[i, "horario"] - valores.loc[i - 1, "horario"]).total_seconds()
                if intervalo > LIMITE_LACUNA_SEGUNDOS:
                    linhas_x.append(None)
                    linhas_y.append(None)
            linhas_x.append(posicao)
            linhas_y.append(valor)

        figura = go.Figure()
        figura.add_trace(go.Scatter(
            x=linhas_x, y=linhas_y, mode="lines", connectgaps=False,
            line=dict(color=cor, width=4), hoverinfo="skip", showlegend=False,
        ))
        figura.add_trace(go.Scatter(
            x=x, y=y, mode="markers", customdata=horarios,
            marker=dict(color=cor, size=9, line=dict(color="#FFFDF6", width=2)),
            cliponaxis=False,
            hovertemplate=(
                "<b>%{customdata}</b><br>" + escape(titulo) +
                ": <b>%{y:.1f}" + escape(unidade) + "</b><extra></extra>"
            ),
            showlegend=False,
        ))
        ultimo = valores.iloc[-1]
        ultima_posicao = x[-1]
        ultimo_valor = float(ultimo[campo])
        figura.add_trace(go.Scatter(
            x=[ultima_posicao], y=[ultimo_valor], mode="markers+text",
            text=[f"{ultimo_valor:.1f}{unidade}"],
            textposition="bottom center" if (campo == "air_humidity_pct" and ultimo_valor >= 95) else "top center",
            textfont=dict(color=CORES["profundo"], size=14),
            marker=dict(size=16, color=cor, line=dict(color="#FFFDF6", width=4)),
            cliponaxis=False, hoverinfo="skip", showlegend=False,
        ))
        configurar_plot(figura, titulo + f" ({unidade})", cor, campo == "air_humidity_pct")
        if sequencia:
            figura.update_xaxes(
                title_text="Sequência das medições", range=[0.4, len(x) + 0.6],
                tickmode="linear", tick0=1, dtick=max(1, (len(x) + 7) // 8),
            )
        else:
            figura.update_xaxes(title_text="Horário", nticks=8,
                                tickformat="%H:%M:%S" if tipo == "tempo" else "%d/%m %H:%M")
        if campo == "air_temperature_c":
            minimo, maximo = min(y), max(y)
            folga = max(1.5, (maximo - minimo) * .15)
            figura.update_yaxes(range=[minimo - folga, maximo + folga])
        st.plotly_chart(
            figura, width="stretch", key=f"plot_{chave}",
            config={"displayModeBar": False, "scrollZoom": False},
        )
        st.html(
            f'<div class="hs-ar-statstrip">'
            f'<span>Mínima: <strong>{formatar_numero(valores[campo].min())}{escape(unidade)}</strong></span>'
            f'<span>Máxima: <strong>{formatar_numero(valores[campo].max())}{escape(unidade)}</strong></span>'
            f'<span>Média: <strong>{formatar_numero(valores[campo].mean())}{escape(unidade)}</strong></span>'
            f'<span>Leituras: <strong>{len(valores)}</strong></span>'
            '</div>'
        )




def mini_estatistica(rotulo, valor, detalhe, cor, fundo):
    """Cartão compacto apenas com estatísticas reais do período."""
    st.html(
        f'<div class="hs-ar-mini" style="--accent:{cor};--accent-bg:{fundo}">'
        f'<div class="hs-ar-mini-label">{escape(rotulo)}</div>'
        f'<div class="hs-ar-mini-val">{escape(valor)}</div>'
        f'<div class="hs-ar-mini-foot">{escape(detalhe)}</div>'
        '<div class="hs-ar-mini-rule"></div></div>'
    )


def panorama(dados):
    """Indicadores numéricos adicionais derivados das medições consultadas."""
    temp = dados["air_temperature_c"].dropna()
    umid = dados["air_humidity_pct"].dropna()
    itens = [
        ("Temperatura mínima", f"{formatar_numero(temp.min())} °C" if not temp.empty else "—", "Menor medição no período", CORES["temperatura"], CORES["temperatura_claro"]),
        ("Temperatura máxima", f"{formatar_numero(temp.max())} °C" if not temp.empty else "—", "Maior medição no período", CORES["temperatura"], CORES["temperatura_claro"]),
        ("Umidade mínima", f"{formatar_numero(umid.min())} %" if not umid.empty else "—", "Menor medição no período", CORES["umidade"], CORES["umidade_claro"]),
        ("Umidade máxima", f"{formatar_numero(umid.max())} %" if not umid.empty else "—", "Maior medição no período", CORES["umidade"], CORES["umidade_claro"]),
    ]
    colunas = st.columns(4, gap="small")
    for coluna, item in zip(colunas, itens):
        with coluna:
            mini_estatistica(*item)


def relacao_variaveis(dados):
    """Relaciona leituras simultâneas das duas variáveis, sem inferir causalidade."""
    pares = dados.dropna(subset=["air_temperature_c", "air_humidity_pct"]).copy()
    with st.container(key="hs_ar_relacao"):
        st.html(
            '<div class="hs-ar-panel-title">Temperatura × umidade relativa</div>'
            '<p class="hs-ar-panel-desc">Cada ponto representa uma medição em que ambas as variáveis foram registradas.</p>'
        )
        if pares.empty:
            st.info("Não há pares de medições válidos para essa análise.")
            return
        figura = go.Figure()
        figura.add_trace(go.Scatter(
            x=pares["air_temperature_c"],
            y=pares["air_humidity_pct"],
            mode="markers",
            marker=dict(color=CORES["umidade"], size=11,
                        line=dict(color="#FFFDF6", width=2), opacity=.83),
            customdata=pares["horario"].dt.strftime("%d/%m/%Y às %H:%M:%S"),
            hovertemplate="<b>%{customdata}</b><br>Temperatura: %{x:.1f} °C<br>Umidade relativa: %{y:.1f}%<extra></extra>",
            showlegend=False,
        ))
        configurar_plot(figura, "Umidade relativa (%)", CORES["umidade"], eixo_percentual=True)
        figura.update_layout(height=355, margin=dict(l=28,r=26,t=28,b=36))
        figura.update_xaxes(title_text="Temperatura do ar (°C)")
        st.plotly_chart(figura, width="stretch", key="hs_ar_scatter",
                        config={"displayModeBar":False, "scrollZoom":False})
        st.caption(f"{len(pares)} medições pareadas · Relação visual, sem indicação de causalidade.")


def registros_detalhados(dados):
    """Tabela de auditoria e CSV referentes apenas ao filtro consultado."""
    secao("Medições registradas")
    with st.expander(f"Consultar tabela detalhada · {len(dados)} registros", expanded=False):
        tabela = dados[["horario", "air_temperature_c", "air_humidity_pct"]].copy()
        tabela["horario"] = tabela["horario"].dt.strftime("%d/%m/%Y %H:%M:%S")
        tabela = tabela.rename(columns={
            "horario":"Data e horário",
            "air_temperature_c":"Temperatura do ar (°C)",
            "air_humidity_pct":"Umidade relativa do ar (%)",
        }).iloc[::-1].reset_index(drop=True)
        st.dataframe(tabela, width="stretch", hide_index=True, height=330)
        csv = tabela.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
        st.download_button("Baixar dados do ar em CSV", data=csv,
                           file_name="hortasense_monitoramento_ar.csv", mime="text/csv",
                           use_container_width=True)


def main():
    # app.py já injeta o tema global no uso pela navegação. A reaplicação é
    # mantida para permitir testar esta página isoladamente com Streamlit.
    aplicar_tema()
    aplicar_estilo()
    cabecalho()
    secao("Consulta ambiental")

    with st.container(key="hs_ar_consulta"):
        st.html(
            '<div class="hs-ar-panel-title">Explore as medições do ar</div>'
            '<p class="hs-ar-panel-desc">Selecione o intervalo para comparar as duas variáveis.</p>'
        )
        periodo = st.selectbox(
            "Período de visualização", options=list(PERIODOS), index=1,
            key="hs_ar_periodo",
        )
        dia = None
        if PERIODOS[periodo][0] == "data":
            dia = st.date_input(
                "Data do monitoramento (horário de Fortaleza)",
                value=datetime.now(FUSO_LOCAL).date(), format="DD/MM/YYYY",
                key="hs_ar_data",
            )

    try:
        registros, tipo, tamanho = consultar_periodo(periodo, dia)
    except (requests.exceptions.RequestException, ValueError, KeyError) as erro:
        # Não expor detalhes de endpoints, tokens ou cabeçalhos ao usuário.
        st.error("Não foi possível consultar as medições do Supabase. Verifique a conexão e as permissões.")
        return

    if not registros:
        st.info("Nenhuma medição disponível para a seleção atual.")
        return

    dados, campos_ausentes = preparar_medicoes(registros)
    if campos_ausentes:
        st.warning("Os registros retornados não contêm todos os campos esperados para monitoramento do ar.")
        return
    dados = filtrar_periodo(dados, tipo, tamanho)
    if dados.empty:
        st.info("Não foram encontradas medições para esse intervalo.")
        return

    horario_primeiro = dados.iloc[0]["horario"].strftime("%d/%m/%Y às %H:%M:%S")
    horario_ultimo = dados.iloc[-1]["horario"].strftime("%d/%m/%Y às %H:%M:%S")
    st.html(
        '<div class="hs-ar-info-rail"><div>'
        '<div class="hs-ar-info-kicker">Unidade monitorada</div>'
        '<div class="hs-ar-info-title">Horta 01 · Condições atmosféricas</div>'
        f'<div class="hs-ar-info-sub">De {escape(horario_primeiro)} até {escape(horario_ultimo)} · Horário de Fortaleza</div>'
        '</div>'
        f'<span class="hs-ar-info-chip">{len(dados)} medições na seleção</span>'
        '</div>'
    )

    secao("Indicadores atmosféricos")
    col_temp, col_umidade = st.columns(2, gap="medium")
    temp_validos = dados["air_temperature_c"].dropna()
    umid_validos = dados["air_humidity_pct"].dropna()
    horario_ultima = dados.iloc[-1]["horario"].strftime("%d/%m/%Y às %H:%M:%S")

    with col_temp:
        cartao(
            "Temperatura do ar", formatar_numero(temp_validos.iloc[-1]) if not temp_validos.empty else "—",
            "°C", "AMBIENTE", "01", CORES["temperatura"], CORES["temperatura_claro"],
            f"{len(temp_validos)} leituras válidas no período",
        )
    with col_umidade:
        cartao(
            "Umidade relativa do ar", formatar_numero(umid_validos.iloc[-1]) if not umid_validos.empty else "—",
            "%", "ATMOSFERA", "02", CORES["umidade"], CORES["umidade_claro"],
            f"{len(umid_validos)} leituras válidas no período",
        )
    st.caption(f"Último registro do período selecionado: {horario_ultima} · Horário de Fortaleza")

    secao("Resumo estatístico")
    panorama(dados)

    secao("Evolução das condições do ar")
    grafico(
        dados, "air_temperature_c", "Temperatura do ar",
        "Variação térmica entre as medições registradas.",
        CORES["temperatura"], "°C", tipo, "hs_ar_grafico_temperatura",
    )
    grafico(
        dados, "air_humidity_pct", "Umidade relativa do ar",
        "Acompanhe a concentração relativa de vapor de água no ambiente.",
        CORES["umidade"], "%", tipo, "hs_ar_grafico_umidade",
    )
    st.html(
        '<div class="hs-ar-insight">'
        '<div class="hs-ar-insight-title">Como interpretar os gráficos?</div>'
        '<div class="hs-ar-insight-copy">A temperatura do ar é apresentada em graus Celsius '
        'e a umidade relativa em porcentagem. Os dois gráficos compartilham o mesmo período '
        'selecionado, mas utilizam escalas próprias. Lacunas superiores a 20 segundos interrompem '
        'as linhas nos filtros temporais; não são preenchidas com valores estimados.</div>'
        '</div>'
    )
    secao("Relação entre as variáveis")
    relacao_variaveis(dados)
    registros_detalhados(dados)


# Compatível com execução isolada e com o roteamento de st.Page.
main()
