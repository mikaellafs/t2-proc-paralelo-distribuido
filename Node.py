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
    if antecessor is None:  # Se ele for o único nó na hash ...
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
    global antecessor
    global sucessor

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

        if int(dest) == nodeID:  # Deve alterar seu intervalo de responsabilidade se necessário
            if tipo == "sucessor":
                sucessor = source
            else:
                antecessor = source
                print_intervalo(name, antecessor, nodeID)

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

    elif topic == "leave":
        leave_node, leave_sucessor, leave_antecessor = m.split("/")
        leave_node = int(leave_node)
        if leave_sucessor != "None" and leave_antecessor != "None":
            leave_sucessor = int(leave_sucessor)
            leave_antecessor = int(leave_antecessor)

        # Node não deve tratar a própria msg de leave
        if leave_node != nodeID:

            # No caso de uma DHT com apenas dois nodes e um deles sai,
            # antecessor e sucessor no node restante devem ser None
            if leave_sucessor == leave_antecessor:
                global rangeAddr
                antecessor = None
                sucessor = None
                # Mensagem de reconhecimento no formato: {ID do nó saindo} / {ID do nó que reconhece a saída}
                client.publish("ack-leave", "%s/%s" % (leave_node, str(nodeID)))
                print_intervalo(name, 0, rangeAddr)

            else:
                # Se o node saindo é antecessor deste node, devemos atualizar o antecessor deste node
                # para apontar para o antecessor do node que está saindo
                if leave_node == antecessor:
                    antecessor = leave_antecessor
                    client.publish("ack-leave", "%s/%s" % (leave_node, str(nodeID)))
                    print_intervalo(name, antecessor, nodeID)

                # Se o node saindo é sucessor deste node, devemos atualizar o sucessor deste node
                # para apontar para o sucessor do node que está saindo
                if leave_node == sucessor:
                    sucessor = leave_sucessor
                    client.publish("ack-leave", "%s/%s" % (leave_node, str(nodeID)))
                    print_intervalo(name, antecessor, nodeID)
        else:
            client.publish("ack-leave", "%s/%s" % (leave_node, str(nodeID)))

    elif topic == "ack-leave":
        global disconnected
        global sucessor_ready
        global antecessor_ready
        leave_node, ack_node = m.split("/")
        leave_node = int(leave_node)
        ack_node = int(ack_node)

        # Node deve tratar apenas a própria msg de ack-leave
        if leave_node == nodeID:

            # Caso o reconhecimento seja de seu nó sucessor
            if ack_node == sucessor or ack_node == nodeID:
                client.unsubscribe("put")  # Nesse momento, o intervalo desse nó já está coberto por outro nó
                sucessor_ready = True

            # Caso o reconhecimento seja de seu nó antecessor (que pode ser também seu nó sucessor)
            if ack_node == antecessor or ack_node == nodeID:
                antecessor_ready = True

            if sucessor_ready and antecessor_ready:
                # Publica todos os elementos de sua hashTable de volta na DHT
                for key in hashTable:
                    client.publish("put", "%s %s" % (str(key), str(hashTable[key])))
                disconnected = True  # Permite quebra do loop no signal_handler


def signal_handler(sig, frame):
    # Formato da mensagem de saída: {ID do nó que deseja sair} / {ID de seu sucessor} / {ID de ser antecessor}
    client.publish("leave", "%s/%s/%s" % (str(nodeID), str(sucessor), str(antecessor)))
    while disconnected is False:
        sleep(0.5)
    client.disconnect()
    exit(0)


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
print("Node %s: Conectado ao broker." % name, "ID: " + str(nodeID))

################ Entrada na DHT ####################

# Se inscreve no tópico ack-join
client.subscribe("ack-join")
client.on_message = on_message
client.loop_start()

# --------> E SE ELE FOR O PRIMEIRO? Espera um tempo e então começa a DHT sozinho
max_times = 10

count = 0
# Manda seu nodeId para entrar e espera receber nodeId do seu antecessor e sucessor

while (antecessor is None or sucessor is None) and count < max_times:
    client.publish("join", nodeID)  # Para garantir que os nós receberão seu nodeId
    sleep(0.5)
    count += 1

# Manda mensagem para seu sucessor e antecessor no tópico ack-join
# com seu nodeID confirmando que está pronto
# já que são os únicos que precisam alterar a responsabilidade

if antecessor is not None:  # se não for o único nó na DHT
    # Aviso ao seu antecessor de que você é o sucessor dele e está pronto
    client.publish("ack-join", "%d/%d/sucessor" % (nodeID, antecessor))  # "nodeid/nodeIdAntecessor"
    # Aviso ao seu sucessor de que você é o antecessor dele e está pronto
    client.publish("ack-join", "%d/%d/antecessor" % (nodeID, sucessor))  # "nodeid/nodeIdSucessor"
else:
    print_intervalo(name, 0, rangeAddr)

# Se inscreve no tópico join, put e get
client.subscribe("join")
client.subscribe("put")
client.subscribe("get")

################ Saída da DHT ####################

client.subscribe("leave")
client.subscribe("ack-leave")
signal.signal(signal.SIGINT, signal_handler)

while True:
    continue
