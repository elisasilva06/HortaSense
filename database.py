
"""
HortaSense — Persistência das medições.

Gerencia a criação do banco SQLite e o armazenamento
das mensagens de telemetria recebidas do ESP32.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


# O banco é armazenado em um diretório próprio do projeto.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "hortasense.db"


def conectar():
    """Abre uma conexão SQLite para executar operações."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DATABASE_PATH, timeout=10)


def inicializar_banco():
    """Cria a tabela de medições caso ainda não exista."""
    with conectar() as conexao:
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS medicoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device TEXT NOT NULL,
                air_temperature_c REAL NOT NULL,
                air_humidity_pct REAL NOT NULL,
                soil_temperature_c REAL NOT NULL,
                soil_moisture_pct INTEGER NOT NULL,
                soil_adc INTEGER NOT NULL,
                irrigation_status TEXT NOT NULL,
                uptime_ms INTEGER NOT NULL,
                received_at TEXT NOT NULL
            )
            """
        )

        conexao.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_medicoes_data
            ON medicoes(received_at)
            """
        )


def salvar_medicao(dados):
    """Valida campos básicos e salva uma medição recebida."""
    campos = (
        "device",
        "air_temperature_c",
        "air_humidity_pct",
        "soil_temperature_c",
        "soil_moisture_pct",
        "soil_adc",
        "irrigation_status",
        "uptime_ms",
    )

    # Impede o armazenamento de mensagens incompletas.
    if not isinstance(dados, dict):
        raise ValueError("A telemetria deve ser um objeto JSON.")

    if any(campo not in dados for campo in campos):
        raise ValueError("Mensagem sem todos os campos obrigatórios.")

    # O horário é registrado pelo computador receptor, em UTC.
    recebido_em = datetime.now(timezone.utc).isoformat()

    valores = tuple(dados[campo] for campo in campos)

    with conectar() as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO medicoes (
                device,
                air_temperature_c,
                air_humidity_pct,
                soil_temperature_c,
                soil_moisture_pct,
                soil_adc,
                irrigation_status,
                uptime_ms,
                received_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (*valores, recebido_em),
        )

        return cursor.lastrowid


def consultar_ultimas_medicoes(limite=10):
    """Consulta as medições mais recentes do banco."""
    with conectar() as conexao:
        conexao.row_factory = sqlite3.Row

        registros = conexao.execute(
            """
            SELECT *
            FROM medicoes
            ORDER BY id DESC
            LIMIT ?
            """,
            (limite,),
        ).fetchall()

        return [dict(registro) for registro in registros]

# ============================================================
# CONSULTA HISTÓRICA POR INTERVALO DE DATA E HORÁRIO
# ============================================================

def consultar_medicoes_intervalo(inicio_local, fim_local):
    """
    Consulta as medições entre dois horários locais.

    Parâmetros:
        inicio_local (datetime):
            Início do intervalo no fuso America/Fortaleza.

        fim_local (datetime):
            Final exclusivo do intervalo no mesmo fuso.

    Retorno:
        list[dict]: medições em ordem cronológica.

    Observações:
        - Não altera os dados armazenados.
        - Os horários são convertidos para UTC.
        - A consulta utiliza parâmetros SQL.
        - Não existe limite de 100 registros.
    """

    import sqlite3
    from datetime import timezone
    from pathlib import Path

    if inicio_local.tzinfo is None or fim_local.tzinfo is None:
        raise ValueError(
            "Os horários precisam conter informação de fuso."
        )

    if inicio_local >= fim_local:
        raise ValueError(
            "O horário final deve ser posterior ao inicial."
        )

    # Converte os horários locais para UTC.
    inicio_utc = inicio_local.astimezone(timezone.utc)
    fim_utc = fim_local.astimezone(timezone.utc)

    # Utiliza o mesmo arquivo SQLite do HortaSense.
    caminho_banco = (
        Path(__file__).resolve().parent
        / "data"
        / "hortasense.db"
    )

    # Não cria um banco vazio caso o arquivo esteja ausente.
    if not caminho_banco.is_file():
        return []

    conexao = sqlite3.connect(str(caminho_banco))

    conexao.row_factory = sqlite3.Row

    try:
        cursor = conexao.execute(
            """
            SELECT
                id,
                device,
                air_temperature_c,
                air_humidity_pct,
                soil_temperature_c,
                soil_moisture_pct,
                soil_adc,
                irrigation_status,
                uptime_ms,
                received_at
            FROM medicoes
            WHERE julianday(received_at) >= julianday(?)
              AND julianday(received_at) < julianday(?)
            ORDER BY julianday(received_at) ASC, id ASC
            """,
            (
                inicio_utc.isoformat(),
                fim_utc.isoformat(),
            ),
        )

        return [
            dict(registro)
            for registro in cursor.fetchall()
        ]

    finally:
        conexao.close()
