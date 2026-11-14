
"""
HortaSense — Receptor de Telemetria MQTT.

Recebe mensagens JSON do ESP32, valida o dispositivo
e armazena as medições em um banco SQLite local.
"""

import json

import paho.mqtt.client as mqtt

from database import inicializar_banco, salvar_medicao


# Configurações correspondentes ao firmware do ESP32.
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "hortasense/grupo01/estufa01/telemetria"

DEVICE_ID = "hortasense_01"
CLIENT_ID = "hortasense_python_monitor"


def on_connect(client, userdata, flags, reason_code, properties):
    """Inscreve o cliente no tópico de telemetria."""

    if reason_code.is_failure:
        print(f"Falha na conexão MQTT: {reason_code}")
        return

    print("Conectado ao broker MQTT!")

    resultado, _ = client.subscribe(MQTT_TOPIC, qos=0)

    if resultado == mqtt.MQTT_ERR_SUCCESS:
        print(f"Inscrição solicitada: {MQTT_TOPIC}")
    else:
        print(f"Erro ao solicitar inscrição: {resultado}")


def on_message(client, userdata, message):
    """Recebe, interpreta e armazena uma medição."""

    try:
        payload = message.payload.decode("utf-8")
        dados = json.loads(payload)

        # Considera somente o dispositivo do protótipo.
        if not isinstance(dados, dict):
            raise ValueError("Mensagem JSON não é um objeto.")

        if dados.get("device") != DEVICE_ID:
            print("Mensagem de outro dispositivo ignorada.")
            return

        # Registra a medição no banco de dados.
        registro_id = salvar_medicao(dados)

        print("\n========== HORTASENSE ==========")
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
        # Impede que uma falha no banco encerre o receptor.
        print(f"Falha ao processar ou armazenar medição: {erro}")


def main():
    """Inicializa o banco e inicia o receptor MQTT."""

    # Prepara a tabela antes de iniciar o recebimento.
    inicializar_banco()
    print("Banco de dados SQLite inicializado.")

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=CLIENT_ID,
    )

    client.on_connect = on_connect
    client.on_message = on_message

    print("Iniciando receptor MQTT do HortaSense...")

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_forever()

    except OSError as erro:
        print(f"Falha de comunicação MQTT: {erro}")

    except KeyboardInterrupt:
        print("\nEncerrando receptor MQTT...")

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
