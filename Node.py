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
    print("Node %s: Intervalo de responsabilidade: ( %s ... %s ]"
          % (nome, f"{int(esq):,}".replace(",", "\'"), f"{int(dir):,}".replace(",", "\'")))


def on_message(client, userdata, msg):
    topic = msg.topic
    m = msg.payload.decode("utf-8")
    global antecessor
    global sucessor

    # Novo nó entrando na DHT
    if topic == "has_started":
        global has_started
        has_started = True
    elif topic == "join":
        client.publish("has_started", "yes")  # Mesmo que não seja ant/suc, avisa que a DHT já começou
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

        if int(dest) == nodeID:  # Define intervalo de responsabilidade
            if tipo == "sucessor":
                sucessor = source
            elif tipo == "antecessor":
                antecessor = source

                # Publica elementos da sua hashTable que não são mais de sua responsabilidade
                for key in hashTable:  # Se for novo nó não faz nada
                    if not check_interval(key):
                        client.publish("put", "%s %s" % (str(key), str(hashTable[key])))
                        hashTable.pop(key)  # Apaga a chave

                if antecessor != source:
                    print_intervalo(name, antecessor, nodeID)

    elif topic == "put":
        codCliente, m = m.split("/")
        key, value = m.split(" ", 1)  # m é uma mensagem no formato "chave string"

        # print(codCliente, m, " ", key, value)
        if check_interval(key):
            key = int(key)
            hashTable[key] = value
            msg = codCliente + "/" + str(nodeID)

            client.publish("ack-put", msg)
            print("Node %s: Valor %s armazenado com sucesso na chave %s." % (name, value, str(key)))

    elif topic == "get":
        if check_interval(m):  # Recebe uma chave
            key = int(m)
            value = hashTable[key]
            msg = str(key) + "/" + value

            client.publish("res-get", msg)
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

        # Node deve tratar apenas a mensagem de ack-leave destinada para ele
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


# rangeAddr = 1000
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

max_times = 100
count = 0

client.subscribe("has_started")
# Manda seu nodeId para entrar e espera receber nodeId do seu antecessor e sucessor
while (antecessor is None or sucessor is None) and (count < max_times or has_started):
    client.publish("join", nodeID)  # Para garantir que os nós receberão seu nodeId
    sleep(0.01)
    count += 1

# Se inscreve no tópico join, put e get
client.subscribe("join")
client.subscribe("put")
client.subscribe("get")
client.unsubscribe("has_started")

if antecessor is None:  # se for o único nó na DHT:    
    print_intervalo(name, 0, rangeAddr)
else:
    client.publish("ack-join", "%d/%d/antecessor" % (nodeID, sucessor))  # Apenas o sucessor deve redistribuir as chaves


################ Saída da DHT ####################

client.subscribe("leave")
client.subscribe("ack-leave")
signal.signal(signal.SIGINT, signal_handler)

while True:
    continue
