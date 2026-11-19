import os
from datetime import timezone
import requests
import streamlit as st


def _obter_credenciais():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")

    if not url or not key:
        raise ValueError("Configure SUPABASE_URL e SUPABASE_KEY nos Secrets.")

    headers = {
        "apikey": key,
        "Content-Type": "application/json",
    }
    return f"{url.rstrip('/')}/rest/v1/medicoes", headers


def inicializar_banco():
    return True


def salvar_medicao(dados):
    endpoint, headers = _obter_credenciais()
    headers["Prefer"] = "return=representation"
    resp = requests.post(endpoint, headers=headers, json=dados, timeout=10)
    resp.raise_for_status()
    registro = resp.json()
    return registro[0]["id"] if registro else None


def consultar_ultimas_medicoes(limite=10):
    endpoint, headers = _obter_credenciais()
    params = {
        "select": "*",
        "order": "id.desc",
        "limit": limite,
    }
    resp = requests.get(endpoint, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def consultar_medicoes_intervalo(inicio_local, fim_local):
    if inicio_local.tzinfo is None or fim_local.tzinfo is None:
        raise ValueError("Os horários precisam conter informação de fuso.")
    if inicio_local >= fim_local:
        raise ValueError("O horário final deve ser posterior ao inicial.")

    inicio_utc = inicio_local.astimezone(timezone.utc).isoformat()
    fim_utc = fim_local.astimezone(timezone.utc).isoformat()

    endpoint, headers = _obter_credenciais()
    params = [
        ("select", "*"),
        ("received_at", f"gte.{inicio_utc}"),
        ("received_at", f"lt.{fim_utc}"),
        ("order", "received_at.asc,id.asc"),
    ]
    resp = requests.get(endpoint, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()