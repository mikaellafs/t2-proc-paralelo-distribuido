import sys
from random import randrange
from time import sleep

import paho.mqtt.client as mqtt

antecessor = None
sucessor = None


def check_interval(k):  # Checa se a chave está dentro do intervalo de responsabilidade
    k = int(k)
    if antecessor is None:  # Se é o único nó na rede,
        return True         # todas as chaves ficam sob sua responsabilidade
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
    if antecessor is None:  # Se ele for o único nó na hash ...
        suc = True
    elif sucessor < nodeID:
        suc = nodeID < newNodeID <= rangeAddr or 0 <= newNodeID < sucessor
    else:
        suc = sucessor > newNodeID > nodeID

    return suc


def on_message(client, userdata, msg):
    topic = msg.topic
    m = msg.payload.decode("utf-8")

    # Novo nó entrando na DHT
    if topic == "join":
        newNodeID = int(m)

        # Verifica se é um novo antecessor, logo avisa pro novo nó que você é sucessor dele
        if checkIfAnt(newNodeID):
            client.publish("ack-join", "%s/%s/sucessor" % (str(nodeID), str(newNodeID)))
        # Verifica se é um novo sucessor, logo avisa pro novo nó que você é antecessor dele        
        if checkIfSuc(newNodeID):
            client.publish("ack-join", "%s/%s/antecessor" % (str(nodeID), str(newNodeID)))

    # Confirmação da entrada na DHT:
    # Formato:  {Node remetente} / {Node destinatário} / {O que o remetente é para o destinatário}
    elif topic == "ack-join":
        source, dest, tipo = m.split("/")
        source = int(source)
        global antecessor
        global sucessor

        if int(dest) == nodeID:  # Deve alterar seu intervalo de responsabilidade se necessário
            if tipo == "sucessor":
                sucessor = source
            else:
                antecessor = source
                print("Node %s: Intervalo de responsabilidade: (%s, %s]"  # Formatação temporária
                      % (name, f"{antecessor:,}".replace(",", "\'"), f"{nodeID:,}".replace(",", "\'")))

    elif topic == "put":
        key, value = m.split(" ", 1)  # m é uma mensagem no formato "chave string"
        if check_interval(key):
            key = int(key)
            hashTable[key] = value
            client.publish("ack-put", str(nodeID))
            print("Node %s: Valor %s armazenado com sucesso na chave %s." % (name, value, str(key)))

    else:  # get
        if check_interval(m):  # Recebe uma chave
            key = int(m)
            value = hashTable[key]
            client.publish("res-get", value)
            print("Node %s: Valor %s retornado da chave %s." % (name, value, str(key)))


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
print("Node_%s: conectado ao broker." % name, "ID: " + str(nodeID))

################ Entrada na DHT ####################

# Se inscreve no tópico ack-join
client.subscribe("ack-join")
client.on_message = on_message
client.loop_start()

# --------> E SE ELE FOR O PRIMEIRO? Espera um tempo e então começa a DHT sozinho
max_times = 100

count = 0
# Manda seu nodeId para entrar e espera receber nodeId do seu antecessor e sucessor

while (antecessor is None or sucessor is None) and count < max_times:
    client.publish("join", nodeID)  # Para garantir que os nós receberão seu nodeId
    sleep(0.1)
    count += 1

# Manda mensagem para seu sucessor e antecessor no tópico ack-join
# com seu nodeID confirmando que está pronto
# já que são os únicos que precisam alterar a responsabilidade

if antecessor is not None:  # se não for o único nó na DHT
    # Aviso ao seu antecessor de que você é o sucessor dele e está pronto
    client.publish("ack-join", "%d/%d/sucessor" % (nodeID, antecessor))  # "nodeid/nodeIdAntecessor"
    # Aviso ao seu sucessor de que você é o antecessor dele e está pronto
    client.publish("ack-join", "%d/%d/antecessor" % (nodeID, sucessor))  # "nodeid/nodeIdSucessor"
else:                                                        # Formatação temporária
    print("Node %s: Intervalo de responsabilidade: (%s, %s]" % (name, 0, f"{rangeAddr:,}".replace(",", "\'")))

# Se inscreve no tópico join, put e get
client.subscribe("join")
client.subscribe("put")
client.subscribe("get")

################ Saída da DHT ####################
#   Como vai sair? Tratar sinal de ctrl-c?

while True:
    continue
