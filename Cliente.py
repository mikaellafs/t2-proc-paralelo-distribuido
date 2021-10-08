from random import randrange
from time import time

import numpy as np
import paho.mqtt.client as mqtt
from django.utils.crypto import get_random_string

keys = np.array([])             # Chaves aleatórias geradas e enviadas
values_sent = np.array([])      # Valores enviados em mensagens publicadas em 'put'
values_received = np.array([])  # Valores recebidos em mensagens publicadas em 'res-get'
ack_received = False            # Quantidade de mensagens publicadas em 'ack-put' recebidas


def on_message(client, userdata, msg):

    # Resgata o conteúdo da mensagem
    m = msg.payload.decode("utf-8")
    global ack_received

    if msg.topic == "ack-put":
        codC, node = m.split("/")
        if codC != codCliente: return
        print(codCliente + ": " + "Successfully added value to nodeID " + node)
        ack_received = True
        return

    if msg.topic == "res-get":
        global values_received
        key, m = m.split("/")
        # print(key)
        if key not in keys: return
        values_received = np.append(values_received, m)
        print(codCliente + ": " + "Received value: " + m)
        ack_received = True
        return


codCliente = get_random_string(10)  # Identificador do cliente

# rangeAddr = 1000
rangeAddr = 2 ** 32  # Quantidade máxima de endereços na tabela hash
mqttBroker = "127.0.0.1"  # Broker tem IP local e porta padrão

client = mqtt.Client(codCliente)
client.connect(mqttBroker)

client.subscribe("ack-put")  # acknowledgement-put()
client.subscribe("res-get")  # response-get()

client.on_message = on_message

#keysQtde = 10
keysQtde = 100  # Quantidade de chaves a serem geradas e enviadas
client.loop_start()

# Inserindo conteúdo na DHT
for i in range(1, keysQtde + 1, 1):

    ack_received = False
    key = str(randrange(0, rangeAddr))
    value = get_random_string(10)
    values_sent = np.append(values_sent, value)

    # Formato padrão de mensagem 'put'
    msg = codCliente + "/" + key + " " + value

    client.publish("put", msg)
    keys = np.append(keys, key)

    # Mensagem amigável de porcentagem concluída
    print(codCliente + ": " + "(" + "{:.1f}".format((i / keysQtde) * 100), "%) ", end='')
    print(codCliente + ": " + "Just published \'" + msg + "\' to topic \'put\'")

    # Esperando ack-put com timeout
    start = time()
    while ack_received is False:
        end = time()
        if (end - start) > 50:
            print(codCliente + ": " + "TIMEOUT: Failed to add pair " + msg + " to DHT")
            exit(1)


# Voce pode setar para esperar confirmação antes de recuperar as chaves -> para realização de testes
import sys
if len(sys.argv) > 1 and sys.argv[1] == '1':
    wait = True
else:
    wait = False

if wait:
    print("Aperte qualquer tecla para recuperar as chaves")
    recuperar = input()

# Resgatando conteúdo da DHT
for i in range(1, keysQtde + 1, 1):

    idx = i - 1
    ack_received = False
    key = keys[idx]

    client.publish("get", key)

    # Mensagem amigável de porcentagem concluída
    print(codCliente + ": " + "(" + "{:.1f}".format((i / keysQtde) * 100), "%) ", end='')
    print(codCliente + ": " + "Just published \'" + key + "\' to topic \'get\'")

    # Esperando ack-get com timeout
    start = time()
    while ack_received is False:
        end = time()
        if (end - start) > 50:
            print(codCliente + ": " + "TIMEOUT: Failed to retrieve pair " + key + '/{value} from DHT')
            exit(1)

    # Verificando se os valores recebidos correspondem aos valores esperados
    if values_received[idx] != values_sent[idx]:
        print(codCliente + ": " + "ERROR: Retrieved value " + values_received[idx] + " does not match expected value " + values_sent[idx])
        exit(1)
    else:
        print(codCliente + ": " + "Retrieved value " + values_received[idx] + " matches expected value " + values_sent[idx])

client.loop_stop()
client.disconnect()
