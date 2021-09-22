from random import randrange
from time import sleep
from django.utils.crypto import get_random_string

import paho.mqtt.client as mqtt
import numpy as np

keys = np.array([])    # Chaves aleatórias geradas e enviadas
values = np.array([])  # Valores recebidos em mensagens publicadas em 'res-get'
ack_received = 0       # Quantidade de mensagens publicadas em 'ack-put' recebidas


def on_message(client, userdata, msg):

    # Resgata o conteúdo da mensagem
    m = msg.payload.decode("utf-8")

    if msg.topic == "ack-put":
        global ack_received
        ack_received += 1
        print("Added value to nodeID " + m)
        return

    if msg.topic == "res-get":
        global values
        values = np.append(values, m)
        print("Received value: " + m)
        return


rangeAddr = 2 ** 32  # Quantidade máxima de endereços na tabela hash
mqttBroker = "127.0.0.1"  # Broker tem IP local e porta padrão

client = mqtt.Client("Cliente")
client.connect(mqttBroker)

client.subscribe("ack-put")  # acknowledgement-put()
client.subscribe("res-get")  # response-get()

client.on_message = on_message

keysQtde = 100  # Quantidade de chaves a serem geradas e enviadas
client.loop_start()

# Inserindo conteúdo na DHT
for i in range(1, keysQtde + 1, 1):

    key = str(randrange(0, rangeAddr))
    value = get_random_string(10)

    # Formato padrão de mensagem 'put'
    msg = key + " " + value

    client.publish("put", msg)
    keys = np.append(keys, key)

    print("(" + "{:.3f}".format((i / keysQtde) * 100), "%) ", end='')
    print("Just published \'" + msg + "\' to topic \'put\'")

# Espera a chegada de todos os 'ack-put's
while ack_received < keysQtde:
    sleep(1)

# Resgatando conteúdo da DHT
for key in keys:
    client.publish("get", key)

# Espera a chegada de todos os 'res-get's
while values.size < keysQtde:
    sleep(1)

client.loop_stop()
