from machine import Pin
import dht
import time
import network
from umqtt.simple import MQTTClient
import machine

# Configuración del sensor DHT11
DHT_PIN = 4  # GPIO donde conectaste el DHT11
sensor = dht.DHT11(Pin(DHT_PIN))

# Configuración WiFi
WIFI_SSID = "Ubee9779-2.4G"
WIFI_PASSWORD = "A266879779"

# Configuración MQTT
MQTT_CLIENT_ID = "esp32_dht11"
MQTT_BROKER = "192.168.0.28"
MQTT_PORT = 1883
MQTT_TOPIC_PUB = "mc/ejercicio2"
MQTT_TOPIC_SUB = "mc/ledRGB"

# Conectar a WiFi
def conectar_wifi():
    print("Conectando a WiFi...", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.3)
    print("\nWiFi Conectada!")

# Callback para recibir mensajes MQTT
def llegada_mensaje(topic, msg):
    print(f"Mensaje recibido en {topic}: {msg.decode()}")

    try:
        payload = msg.decode().split(",")  # Dividir el mensaje
        temperatura = float(payload[0])
        humedad = float(payload[1])

        print(f"Temperatura: {temperatura}°C, Humedad: {humedad}%")

        # Control del LED basado en la temperatura recibida de Node-RED
        if temperatura < 25:
            set_color(0, 1, 0)  # Azul
        elif 25 <= temperatura <= 27:
            set_color(0, 0, 1)  # Verde 
        else:
            set_color(1, 0, 0)  # Rojo (Caliente)

    except Exception as e:
        print(f"Error procesando el mensaje: {e}")

# Conectar al broker MQTT
def subscribir():
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
        client.set_callback(llegada_mensaje)
        client.connect()
        client.subscribe(MQTT_TOPIC_SUB)
        print(f"Conectado a {MQTT_BROKER}, suscrito a {MQTT_TOPIC_SUB}")
        return client
    except Exception as e:
        print(f"Error conectando a MQTT: {e}")
        return None

# Pines del LED RGB
led_rojo = machine.Pin(25, machine.Pin.OUT, value=0)
led_verde = machine.Pin(26, machine.Pin.OUT, value=0)
led_azul = machine.Pin(27, machine.Pin.OUT, value=0)

# Función para controlar el color del LED RGB
def set_color(r, g, b):
    """Controla el color del LED RGB"""
    led_rojo.value(r)
    led_verde.value(g)
    led_azul.value(b)

# Conectar a WiFi
conectar_wifi()

# Conectar a MQTT
client = subscribir()
if client is None:
    print("No se pudo conectar a MQTT. Reinicia el ESP32.")
else:
    while True:
        client.check_msg()  # Procesar mensajes entrantes
        try:
            sensor.measure()
            temperatura = sensor.temperature()
            humedad = sensor.humidity()

            # Publicar datos a Node-RED
            datos = f"{temperatura},{humedad}"
            print(f"Publicando: Temperatura {temperatura}°C, Humedad {humedad}%")
            client.publish(MQTT_TOPIC_PUB, datos)

            # Control de color del LED según temperatura
            if temperatura < 25:
                set_color(0, 1, 0)  # Verde (Frío)
            elif 25 <= temperatura <= 27:
                set_color(0, 0, 1)  # Azul (Templado)
            else:
                set_color(1, 0, 0)  # Rojo (Caliente)

        except OSError as e:
            print("Error al leer el sensor:", e)

        time.sleep(2)
