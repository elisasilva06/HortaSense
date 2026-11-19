"""
HortaSense — Receptor de Telemetria Bluetooth (BLE).

Recebe mensagens JSON do ESP32-C3 via BLE, valida o dispositivo
e armazena as medições no banco SQLite local.
"""

import asyncio
import json

from bleak import BleakClient, BleakScanner

from database import inicializar_banco, salvar_medicao

DEVICE_NAME = "HortaSense-C3"
CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_ID = "hortasense_01"


def on_ble_data(sender, data: bytearray):
    """Recebe, interpreta e armazena uma medição vinda do BLE."""
    try:
        payload = data.decode("utf-8")
        dados = json.loads(payload)

        if not isinstance(dados, dict):
            raise ValueError("Mensagem JSON não é um objeto.")

        if dados.get("device") != DEVICE_ID:
            print("Mensagem de outro dispositivo ignorada.")
            return

        registro_id = salvar_medicao(dados)

        print("\n========== HORTASENSE (BLE) ==========")
        print(f"Dispositivo: {dados['device']}")
        print(f"Temperatura do ar: {dados['air_temperature_c']} °C")
        print(f"Umidade do ar: {dados['air_humidity_pct']} %")
        print(f"Temperatura do solo: {dados['soil_temperature_c']} °C")
        print(f"Umidade do solo: {dados['soil_moisture_pct']} %")
        print(f"ADC do solo: {dados['soil_adc']}")
        print(f"Estado hídrico: {dados['irrigation_status']}")
        print(f"Tempo de operação: {dados['uptime_ms']} ms")
        print(f"Registro salvo no banco: ID {registro_id}")

    except (UnicodeDecodeError, json.JSONDecodeError) as erro:
        print(f"Mensagem JSON inválida: {erro}")
    except (KeyError, TypeError, ValueError) as erro:
        print(f"Erro ao validar a telemetria: {erro}")
    except Exception as erro:
        print(f"Falha ao processar ou armazenar medição: {erro}")


async def escutar_ble():
    """Mantém a conexão BLE ativa com reconexão automática."""
    while True:
        print(f"Procurando {DEVICE_NAME} via Bluetooth...")
        device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10.0)

        if not device:
            print("ESP32-C3 não encontrado. Tentando novamente em 3s...")
            await asyncio.sleep(3)
            continue

        try:
            async with BleakClient(device) as client:
                print(f"Conectado a {device.name} ({device.address})!")
                await client.start_notify(CHAR_UUID, on_ble_data)

                while client.is_connected:
                    await asyncio.sleep(1)

                print("Conexão BLE encerrada. Reconectando...")
        except Exception as erro:
            print(f"Falha na conexão BLE: {erro}. Tentando novamente em 3s...")
            await asyncio.sleep(3)


def main():
    inicializar_banco()
    print("Banco de dados SQLite inicializado.")
    print("Iniciando receptor BLE do HortaSense...")

    try:
        asyncio.run(escutar_ble())
    except KeyboardInterrupt:
        print("\nEncerrando receptor BLE...")


if __name__ == "__main__":
    main()