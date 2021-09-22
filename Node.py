import paho.mqtt.client as mqtt
from random import randrange
import sys
import numpy as np
from time import sleep

antecessor = None
sucessor = None

def check_interval(k):
    k = int(k)
    if index == 0:  # Se é o primeiro nó do intervalo, seu antecessor possui nodeID menor que o seu
        return (antecessor < k <= rangeAddr) or (0 <= k <= nodeID)

    return antecessor < k <= nodeID  # Checa se esta dentro do intervalo de responsabilidade

def checkIfAnt(newNodeID): # checa se o novo nó é um antecessor
    if # se ele for o unico nó na hash ...
        ant = True
    elif antecessor > nodeID:
        ant = antecessor < newNodeID <= rangeAddr or 0 <= newNodeID < nodeID
    else:
        ant = nodeID > newNodeID > antecessor
    
    return ant

def checkIfSuc(newNodeID): # checa se o novo nó é um sucessor
    if # se ele for o unico nó na hash ...
        suc = True
    if sucessor < nodeID:
        suc =  nodeID < newNodeID <= rangeAddr or 0 <= newNodeID < sucessor
    else:
        suc = sucessor > newNodeID > nodeID
    
    return suc


def on_message(client, userdata, msg):
    topic = msg.topic
    m = msg.payload.decode("utf-8")

    # Novo nó entrando na DHT
    if topic == "join":
        newNodeID = int(m)

        # Verifica se é um novo antecessor
        if  checkIfAnt(newNodeID):
            client.publish("ack-join", "%s/%s/antecessor" % (str()))          
                    

    elif topic == "ack-join":
        

    elif topic == "put":
        key, value = m.split(" ", 1)  # m é uma mensagem no formato "chave string"
        if check_interval(key):
            key = int(key)
            hashTable[key] = value
            client.publish("ack-put", str(nodeID))
            print("Valor %s armazenado com sucesso na chave %s." % (value, str(key)))
        
    else:  # get
        if check_interval(m):  # Recebe uma chave
            key = int(m)
            value = hashTable[key]
            client.publish("res-get", value)
            print("Valor %s retornado da chave %s." % (value, str(key)))


rangeAddr = 2 ** 32  # Quantidade máxima de endereços na tabela hash
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
print("Node_%s conectado ao broker." % name, "ID: " + str(nodeID))

################ Entrada na DHT ####################

# Se inscreve no tópico ack-join
client.subscribe("ack-join")

# --------> E SE ELE FOR O PRIMEIRO?

# Manda seu nodeId para entrar e espera receber nodeId do seu antecessor e sucessor
while( sucessor == None or antecessor == None)
    client.publish("join", nodeID) # para garantir que os nós receberão seu nodeId
    sleep(1)

# Manda mensagem para seu sucesso e antecessor no topico ack-join para antecessor e sucessor
# com seu nodeID confirmando que esta pronto 
# já que são os únicos que precisam alterar a responsabilidade
client.publish("ack-join", "%s/%s" % (str(nodeID), str(antecessor)))   # "nodeid/nodeIdAntecessor"
client.publish("ack-join", "%s/%s" % (str(nodeID), str(sucessor)))     # "nodeid/nodeIdSucessor"

print("Pronto! Intervalo de responsabilidade: (", int(antecessor), ",", int(nodeID), "]")
# Se inscreve no tópico join, put e get
client.subscribe("join")
client.subscribe("put")
client.subscribe("get")

################ Saída na DHT ####################
#   Como vai sair? Tratar sinal de ctrl-c?

while True: 
    continue