import sys
import signal
from random import randrange
from time import sleep

import paho.mqtt.client as mqtt

antecessor = None
sucessor = None
disconnected = False
sucessor_ready = False
antecessor_ready = False
has_started = False


def check_interval(k):  # Checa se a chave está dentro do intervalo de responsabilidade
    k = int(k)
    if antecessor is None:  # Se é o único nó na rede,
        return True  # todas as chaves ficam sob sua responsabilidade
    elif antecessor > nodeID:
        return (antecessor < k <= rangeAddr) or (0 <= k <= nodeID)

    return antecessor < k <= nodeID


def checkIfAnt(newNodeID):  # Checa se o novo nó é um antecessor
    if antecessor is None:  # Se ele for o único nó na hash ...
        ant = True
    elif antecessor > nodeID:
        ant = antecessor < newNodeID <= rangeAddr or 0 <= newNodeID < nodeID
    else:
        ant = nodeID > newNodeID > antecessor

    return ant


def checkIfSuc(newNodeID):  # Checa se o novo nó é um sucessor
    if sucessor is None:  # Se ele for o único nó na hash ...
        suc = True
    elif sucessor < nodeID:
        suc = nodeID < newNodeID <= rangeAddr or 0 <= newNodeID < sucessor
    else:
        suc = sucessor > newNodeID > nodeID

    return suc


def print_intervalo(nome, esq, dir):
    print("Node %s: Intervalo de responsabilidade: (%s, %s]"  # Formatação temporária
          % (nome, f"{int(esq):,}".replace(",", "\'"), f"{int(dir):,}".replace(",", "\'")))


def on_message(client, userdata, msg):
    topic = msg.topic
    m = msg.payload.decode("utf-8")

    # Novo nó entrando na DHT
    if topic == "has_started":
        global has_started
        has_started = True
    elif topic == "join":
        client.publish("has_started", "yes") # mesmo que nao seja ant/suc, avisa que a DHT já começou
        newNodeID = int(m)

        # Verifica se é um novo antecessor, logo avisa pro novo nó que você é sucessor dele
        if checkIfAnt(newNodeID):
            global antecessor

            client.publish("ack-join", "%s/%s/sucessor" % (str(nodeID), str(newNodeID)))

            # Altera intervalo de responsabilidade
            antecessor = newNodeID
            print_intervalo(name, antecessor, nodeID)

        # Verifica se é um novo sucessor, logo avisa pro novo nó que você é antecessor dele 
        if checkIfSuc(newNodeID):
            global sucessor

            client.publish("ack-join", "%s/%s/antecessor" % (str(nodeID), str(newNodeID)))
            sucessor = newNodeID

    # Confirmação da entrada na DHT:
    # Formato:  {Node remetente} / {Node destinatário} / {O que o remetente é para o destinatário}
    elif topic == "ack-join":
        source, dest, tipo = m.split("/")
        source = int(source)

        if int(dest) == nodeID: # Define intervalo de responsabilidade
            if tipo == "sucessor":
                sucessor = source
            elif antecessor != source:
                antecessor = source
                print_intervalo(name, antecessor, nodeID)
                
                # Publica elementos da sua hashTable que não são mais de sua responsabilidade 
                for key in hashTable:
                    if not check_interval(key):
                        client.publish("put", "%s %s" % (str(key), str(hashTable[key])))
                        hashTable.pop(key) # apaga a chave

    elif topic == "put":
        key, value = m.split(" ", 1)  # m é uma mensagem no formato "chave string"
        if check_interval(key):
            key = int(key)
            hashTable[key] = value
            client.publish("ack-put", str(nodeID))
            print("Node %s: Valor %s armazenado com sucesso na chave %s." % (name, value, str(key)))

    elif topic == "get":
        if check_interval(m):  # Recebe uma chave
            key = int(m)
            value = hashTable[key]
            client.publish("res-get", value)
            print("Node %s: Valor %s retornado da chave %s." % (name, value, str(key)))


rangeAddr = 1000
#rangeAddr = 2 ** 32  # Quantidade máxima de endereços na tabela hash
hashTable = {}
nodeID = randrange(0, rangeAddr)

mqttBroker = "127.0.0.1"  # Broker tem IP local e porta padrão

# Verifica se foi passado um nome/número específico para o node
if len(sys.argv) > 1:
    name = sys.argv[1]
else:
    name = nodeID

# Conecta ao broker mqtt
client = mqtt.Client("Node_%s" % name)  # Passar como parâmetro o nome/número do nó
while client.connect(mqttBroker) != 0:
    sleep(0.1)
print("Node %s: Conectado ao broker." % name, "ID: " + str(nodeID))

################ Entrada na DHT ####################

# Se inscreve no tópico ack-join
client.subscribe("ack-join")
client.on_message = on_message
client.loop_start()

# --------> E SE ELE FOR O PRIMEIRO? Verifica se a DHT já foi iniciada, espera um tempo 
#                                   e inicia a DHT sozinho
max_times = 100

count = 0
client.subscribe("has_started")
# Manda seu nodeId para entrar e espera receber nodeId do seu antecessor e sucessor
while (antecessor is None or sucessor is None) and (count < max_times or has_started):
    client.publish("join", nodeID)  # Para garantir que os nós receberão seu nodeId
    sleep(0.01)
    count += 1

if antecessor is None:
    print_intervalo(name, 0, rangeAddr)

# Se inscreve no tópico join, put e get
client.subscribe("join")
client.subscribe("has_started")
client.subscribe("put")
client.subscribe("get")
client.unsubscribe("has_started")
client.unsubscribe("ack-join")

################ Saída da DHT ####################


while True:
    continue