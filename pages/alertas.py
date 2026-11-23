"""HortaSense | Alertas e Ocorrências.

Analisa as medições registradas para identificar períodos de solo seco,
excesso de umidade e interrupções no envio de dados do ESP32.
"""

from html import escape
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from database import consultar_ultimas_medicoes


FUSO_LOCAL = ZoneInfo("America/Fortaleza")
GAP_OFFLINE_SEG = 120  # 2 minutos sem envio = ocorrência de dispositivo


def aplicar_estilo():
    """Mantém a identidade visual das páginas Visão Geral e Histórico."""
    st.html("""
    <style>
      .stApp:has(#hs-alertas-root) [data-testid="stMain"] .block-container {
        max-width: 1280px;
        padding-top: 2rem;
        padding-bottom: 4rem;
      }
      .hs-al-hero {
        position: relative;
        isolation: isolate;
        overflow: hidden;
        background: linear-gradient(112deg, #2F5A3A 0%, #35663F 57%, #668B4A 100%);
        border-radius: 32px 32px 32px 9px;
        padding: 42px 46px 38px;
        margin-bottom: 26px;
        box-shadow: 0 14px 34px rgba(47,90,58,.09);
        color: #FFFDF6;
        font-family: 'Manrope', sans-serif;
      }
      .hs-al-hero:before {
        content: '';
        position: absolute;
        width: 290px; height: 290px;
        border-radius: 50%;
        right: -115px; top: -175px;
        background: rgba(220,232,210,.14);
        z-index: -1;
      }
      .hs-al-hero:after {
        content: '';
        position: absolute;
        width: 155px; height: 155px;
        border: 2px solid rgba(220,232,210,.24);
        border-radius: 50%;
        right: 40px; bottom: -110px;
        z-index: -1;
      }
      .hs-al-eyebrow {
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
      .hs-al-eyebrow:before {
        content: '';
        width: 9px; height: 9px;
        border-radius: 50%;
        background: #C5DF9D;
      }
      .hs-al-title {
        color: #FFFDF6 !important;
        font-family: 'Bricolage Grotesque', sans-serif;
        font-weight: 800;
        font-size: clamp(32px,4.1vw,50px);
        line-height: 1.08;
        letter-spacing: -.05em;
        margin: 26px 0 14px;
      }
      .hs-al-subtitle {
        color: #F8F1DC !important;
        max-width: 650px;
        font-size: 15px;
        line-height: 1.7;
        margin: 0 0 24px;
      }
      .hs-al-signature {
        display: flex; align-items: center; gap: 12px;
        color: #F8F1DC;
        font-size: 11px; font-weight: 700;
      }
      .hs-al-signature:before {
        content: '';
        width: 34px; height: 3px;
        border-radius: 99px;
        background: #C5DF9D;
      }
      .hs-al-section {
        display: flex; align-items: center; gap: 12px;
        margin: 28px 0 16px;
        color: #2F5A3A;
        font: 800 12px/1.4 'Manrope', sans-serif;
        letter-spacing: .10em;
        text-transform: uppercase;
      }
      .hs-al-section:before {
        content: '';
        width: 7px; height: 22px;
        border-radius: 99px;
        background: #8AA730;
      }
      .hs-al-summary {
        position: relative;
        overflow: hidden;
        padding: 22px 22px 20px;
        border: 1px solid #D8DFC9;
        border-radius: 26px 26px 26px 9px;
        background: #FFFDF6;
        box-shadow: 0 8px 22px rgba(47,90,58,.05);
        font-family: 'Manrope', sans-serif;
      }
      .hs-al-summary:before {
        content: '';
        position: absolute;
        width: 105px; height: 105px;
        top: -42px; right: -28px;
        background: var(--al-tint);
        border-radius: 50%;
      }
      .hs-al-summary-tag {
        position: relative;
        color: var(--al-accent);
        font-size: 10px; font-weight: 800;
        letter-spacing: .11em;
        text-transform: uppercase;
      }
      .hs-al-summary-val {
        position: relative;
        color: #2F5A3A;
        font: 800 clamp(28px,2.8vw,38px)/1.15 'Bricolage Grotesque', sans-serif;
        letter-spacing: -.035em;
        margin: 10px 0 4px;
      }
      .hs-al-summary-desc {
        position: relative;
        color: #57664F;
        font-size: 12px; font-weight: 600;
      }
      .hs-al-summary-bar {
        width: 56px; height: 5px;
        background: var(--al-accent);
        border-radius: 10px;
        margin-top: 16px;
      }
      .stApp:has(#hs-alertas-root) [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background-color: #FFFDF6 !important;
        border-color: #B9D0A6 !important;
        border-radius: 14px !important;
      }
      @media(max-width:800px) {
        .hs-al-hero { padding: 28px 22px; border-radius: 24px 24px 24px 8px; }
      }
    </style>
    <span id="hs-alertas-root" style="display:none"></span>
    """)


def formatar_duracao(inicio, fim):
    segundos = int(max(0, (fim - inicio).total_seconds()))
    if segundos < 15:
        return "Evento pontual"
    if segundos < 60:
        return f"Duração: {segundos}s"
    minutos = segundos // 60
    if minutos < 60:
        return f"Duração: {minutos} min"
    horas = minutos // 60
    resto_min = minutos % 60
    return f"Duração: {horas}h {resto_min:02d}min"


def extrair_ocorrencias(registros):
    """Agrupa leituras consecutivas em ocorrências únicas para evitar repetição."""
    if not registros:
        return []

    df = pd.DataFrame(registros).copy()
    df["horario"] = pd.to_datetime(df["received_at"], utc=True, errors="coerce").dt.tz_convert(FUSO_LOCAL)
    df["soil_moisture_pct"] = pd.to_numeric(df["soil_moisture_pct"], errors="coerce")
    df = df.dropna(subset=["horario"]).sort_values("horario").reset_index(drop=True)

    ocorrencias = []
    evento_atual = None

    for i, row in df.iterrows():
        status = row.get("irrigation_status")
        horario = row["horario"]
        umidade = row["soil_moisture_pct"]

        if i > 0:
            gap = (horario - df.loc[i - 1, "horario"]).total_seconds()
            if gap > GAP_OFFLINE_SEG:
                if evento_atual:
                    ocorrencias.append(evento_atual)
                    evento_atual = None
                ocorrencias.append({
                    "categoria": "Dispositivo",
                    "nivel": "info",
                    "titulo": "Interrupção no envio de dados",
                    "inicio": df.loc[i - 1, "horario"],
                    "fim": horario,
                    "detalhe": f"O ESP32 ficou sem enviar leituras por {int(gap // 60)} minuto(s).",
                    "em_andamento": False,
                })

        if status in ("NECESSIDADE_IRRIGACAO", "ATENCAO_HIDRICA"):
            if evento_atual is None or evento_atual["status"] != status:
                if evento_atual:
                    ocorrencias.append(evento_atual)
                eh_critico = status == "NECESSIDADE_IRRIGACAO"
                umidade_txt = f"{umidade:.0f}%" if pd.notna(umidade) else "—"
                evento_atual = {
                    "status": status,
                    "categoria": "Crítico" if eh_critico else "Atenção",
                    "nivel": "error" if eh_critico else "warning",
                    "titulo": "Necessidade de irrigação" if eh_critico else "Excesso de umidade",
                    "inicio": horario,
                    "fim": horario,
                    "umidade_ref": umidade if pd.notna(umidade) else None,
                    "detalhe": (
                        f"Solo seco detectado (umidade em {umidade_txt})."
                        if eh_critico
                        else f"Solo muito úmido detectado (umidade em {umidade_txt})."
                    ),
                    "em_andamento": False,
                }
            else:
                evento_atual["fim"] = horario
                if pd.notna(umidade):
                    if evento_atual["umidade_ref"] is None:
                        evento_atual["umidade_ref"] = umidade
                    elif status == "NECESSIDADE_IRRIGACAO":
                        evento_atual["umidade_ref"] = min(evento_atual["umidade_ref"], umidade)
                    else:
                        evento_atual["umidade_ref"] = max(evento_atual["umidade_ref"], umidade)

                    ref_txt = f"{evento_atual['umidade_ref']:.0f}%"
                    evento_atual["detalhe"] = (
                        f"Umidade atingiu mínima de {ref_txt} durante a ocorrência."
                        if status == "NECESSIDADE_IRRIGACAO"
                        else f"Umidade atingiu máxima de {ref_txt} durante a ocorrência."
                    )
        else:
            if evento_atual:
                ocorrencias.append(evento_atual)
                evento_atual = None

    if evento_atual:
        evento_atual["em_andamento"] = True
        ocorrencias.append(evento_atual)

    return list(reversed(ocorrencias))


def renderizar_card_ocorrencia(item):
    estilos = {
        "error": {
            "cor": "#AC3028",
            "fundo": "#FFD8D0",
            "borda": "#D45E4D",
            "marcador": "CRÍTICO · SOLO SECO",
            "simbolo": "!",
        },
        "warning": {
            "cor": "#1D5FA7",
            "fundo": "#DCEBFC",
            "borda": "#74A9E2",
            "marcador": "ATENÇÃO · EXCESSO DE UMIDADE",
            "simbolo": "!",
        },
        "info": {
            "cor": "#57664F",
            "fundo": "#EDF3E5",
            "borda": "#B9D0A6",
            "marcador": "DISPOSITIVO · CONEXÃO",
            "simbolo": "i",
        },
    }
    v = estilos[item["nivel"]]
    inicio_txt = item["inicio"].strftime("%d/%m/%Y às %H:%M:%S")
    badge_txt = "Em andamento" if item.get("em_andamento") else formatar_duracao(item["inicio"], item["fim"])

    st.html(
        f"""
        <div style="
            position:relative; overflow:hidden; box-sizing:border-box;
            background:#FFFDF6; border:1px solid {v['borda']};
            border-radius:20px 20px 20px 8px; padding:18px 22px;
            margin-bottom:12px; font-family:'Manrope','Segoe UI',sans-serif;
            box-shadow:0 6px 18px rgba(47,90,58,.04);
        ">
          <div style="position:absolute;top:0;left:0;height:100%;width:6px;background:{v['cor']};"></div>
          <div style="display:flex;align-items:center;gap:15px;flex-wrap:wrap;">
            <div style="
                width:44px;height:44px;flex:none;display:flex;align-items:center;
                justify-content:center;background:{v['fundo']};border:2px solid {v['borda']};
                color:{v['cor']};font-size:22px;font-weight:900;border-radius:50%;
            ">{v['simbolo']}</div>
            <div style="flex:1;min-width:220px;">
              <div style="color:{v['cor']};font-size:10px;font-weight:800;letter-spacing:.11em;">
                {v['marcador']} · {escape(inicio_txt)}
              </div>
              <div style="color:{v['cor']};font-family:'Bricolage Grotesque',sans-serif;
                  font-size:19px;font-weight:800;margin:2px 0;">
                {escape(item['titulo'])}
              </div>
              <div style="color:#27382B;font-size:13px;line-height:1.5;">
                {escape(item['detalhe'])}
              </div>
            </div>
            <span style="
                font-size:11px;font-weight:800;color:{v['cor']};
                background:{v['fundo']};border:1px solid {v['borda']};
                border-radius:999px;padding:7px 13px;white-space:nowrap;
            ">{escape(badge_txt)}</span>
          </div>
        </div>
        """
    )


def main():
    aplicar_estilo()
    st.html("""
    <div class="hs-al-hero">
      <span class="hs-al-eyebrow">MONITORAMENTO DE EVENTOS</span>
      <div class="hs-al-title">Alertas e Ocorrências</div>
      <p class="hs-al-subtitle">
        Acompanhe situações de solo seco, excesso de umidade e interrupções
        de comunicação registradas pelo dispositivo HortaSense.
      </p>
      <div class="hs-al-signature">HortaSense · Cultivo inteligente</div>
    </div>
    """)

    registros = consultar_ultimas_medicoes(500)
    if not registros:
        st.info("Nenhuma medição encontrada para gerar alertas.")
        return

    ocorrencias = extrair_ocorrencias(registros)

    qtd_critico = sum(1 for o in ocorrencias if o["categoria"] == "Crítico")
    qtd_atencao = sum(1 for o in ocorrencias if o["categoria"] == "Atenção")
    qtd_disp = sum(1 for o in ocorrencias if o["categoria"] == "Dispositivo")

    st.html('<div class="hs-al-section">Resumo recente (últimas 500 leituras)</div>')
    c1, c2, c3 = st.columns(3, gap="medium")
    resumos = [
        (c1, "Solo seco", str(qtd_critico), "Necessidade de irrigação", "#AC3028", "#FCE6E0"),
        (c2, "Excesso de umidade", str(qtd_atencao), "Atenção hídrica (> 70%)", "#1D5FA7", "#DCEBFC"),
        (c3, "Dispositivo", str(qtd_disp), "Quedas de envio (> 2 min)", "#57664F", "#EDF3E5"),
    ]
    for col, tag, val, desc, accent, tint in resumos:
        with col:
            st.html(
                f'<div class="hs-al-summary" style="--al-accent:{accent};--al-tint:{tint}">'
                f'<div class="hs-al-summary-tag">{tag}</div>'
                f'<div class="hs-al-summary-val">{val}</div>'
                f'<div class="hs-al-summary-desc">{desc}</div>'
                '<div class="hs-al-summary-bar"></div>'
                '</div>'
            )

    st.html('<div class="hs-al-section">Histórico de ocorrências</div>')
    filtro = st.selectbox(
        "Filtrar por tipo de ocorrência",
        ["Todas", "Crítico", "Atenção", "Dispositivo"],
        index=0,
    )

    filtradas = ocorrencias if filtro == "Todas" else [o for o in ocorrencias if o["categoria"] == filtro]

    if not filtradas:
        st.success("Nenhuma ocorrência registrada para o filtro selecionado.")
        return

    for item in filtradas:
        renderizar_card_ocorrencia(item)


if __name__ == "__main__":
    main()