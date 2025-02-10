from machine import Pin
import network
from time import sleep
from hcsr04 import HCSR04
from umqtt.simple import MQTTClient

# Configuración de MQTT
MQTT_BROKER = "192.168.188.212"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "esp32_sensor_client"  # Asegúrate de usar un ID único para el cliente
MQTT_USER = ""  # Si no tienes usuario, déjalo vacío
MQTT_PASSWORD = ""  # Si no tienes contraseña, déjalo vacío
MQTT_TOPIC_PUB = "mgcs/sensor"  # Topic para publicar la distancia

# Configuración del sensor y los LED
sensor = HCSR04(15, 4)
ledr = Pin(18, Pin.OUT)
ledg = Pin(21, Pin.OUT)
ledy = Pin(19, Pin.OUT)

# Función para conectar a WiFi
def conectar_wifi():
    print("Conectando a WiFi...", end="")
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        sta_if.active(True)
        sta_if.connect('RaspBerry 7', 'linux4321')
        while not sta_if.isconnected():
            print(".", end="")
            sleep(0.5)
    print("\nWiFi Conectada! IP:", sta_if.ifconfig()[0])

# Función para subscribirse al broker MQTT
def subscribir():
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT,
                             user=MQTT_USER, password=MQTT_PASSWORD, keepalive=30)
        client.set_callback(llegada_mensaje)
        client.connect()
        client.subscribe(MQTT_TOPIC_PUB)  # Suscripción al topic
        print("Conectado a %s, en el tópico %s" % (MQTT_BROKER, MQTT_TOPIC_PUB))
        return client
    except Exception as e:
        print("Error conectando al broker MQTT:", e)
        return None

# Función que maneja los mensajes recibidos en el topic
def llegada_mensaje(topic, msg):
    print("Mensaje recibido:", msg)
    if msg == b'true':
        ledr.value(1)
    elif msg == b'false':
        ledr.value(0)

# Función para reconectar al broker MQTT
def reconectar_mqtt():
    global client
    print("Intentando reconectar a MQTT...")
    while client is None:  # Mientras no esté conectado
        client = subscribir()  # Intentar la conexión nuevamente
        sleep(5)  # Esperar 5 segundos antes de volver a intentar

# Conectar a WiFi
conectar_wifi()

# Conectar al broker MQTT
client = subscribir()

# Variable para la distancia anterior
distancia_anterior = 0

# Ciclo principal
while True:
    try:
        if client is not None:
            client.check_msg()  # Verificar si hay mensajes nuevos
        else:
            reconectar_mqtt()  # Intentar reconectar si client es None

        # Obtener la distancia del sensor
        distancia = int(sensor.distance_cm())
        print(f"Distancia del objeto: {distancia} cm.")

        if client:
            # Publicar solo si el cliente MQTT está conectado
            if distancia > 200:
                print("Lejos")
                client.publish(MQTT_TOPIC_PUB, str(distancia))  # Publicar la distancia
                ledr.on()
                ledy.off()
                ledg.off()
            elif distancia > 100:
                print("No tan cerca")
                client.publish(MQTT_TOPIC_PUB, str(distancia))  # Publicar la distancia
                ledr.off()
                ledy.on()
                ledg.off()
            elif distancia > 0:
                print("Muy cerca")
                client.publish(MQTT_TOPIC_PUB, str(distancia))  # Publicar la distancia
                ledr.off()
                ledy.off()
                ledg.on()
        else:
            print("Cliente MQTT no disponible, no se puede publicar.")

        sleep(1)  # Esperar 1 segundo antes de la siguiente medición

    except OSError as e:
        print("Error detectado:", e)
        reconectar_mqtt()  # Intentar reconectar si ocurre un error