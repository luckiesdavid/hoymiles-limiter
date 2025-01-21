import paho.mqtt.client as mqtt
import json
import configparser

### Configparser
config = configparser.ConfigParser()
config.read('pv_limiter_config.ini')

# MQTT-Broker-Konfiguration
BROKER_ADDRESS = config.get('MQTT', 'broker')  # IP-Adresse des Home Assistant MQTT-Brokers
BROKER_PORT = config.get('MQTT', 'port')                # Standard-MQTT-Port
USERNAME = config.get('MQTT', 'user')        # Dein MQTT-Benutzername (falls erforderlich)
PASSWORD = config.get('MQTT', 'pw')        # Dein MQTT-Passwort (falls erforderlich)

# Zu sendende Variable
def send_mqtt(topic, payload_dict):

    payload = json.dumps(payload_dict)  # Konvertiere Dictionary in JSON-String
    #print(payload)

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            #print("Verbunden mit dem MQTT-Broker")
            client.publish(topic, payload)
            print(f"send to topic {topic}")
        else:
            print(f"Verbindung fehlgeschlagen mit Code {rc}")

    # MQTT-Client erstellen
    client = mqtt.Client()
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.connect(BROKER_ADDRESS, BROKER_PORT)

    # Verbindung schließen
    client.loop_start()
    client.loop_stop()
    client.disconnect()
