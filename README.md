# Trabalho T2 - DHT 

**Objetivo**

Experimentar a implementação de sistemas de comunicação indireta por meio de middleware Publish/Subscribe com Filas de Mensagens. Sincronizar a troca de mensagens entre os componentes do sistema. Utilizar brokers de troca de mensagens na implementação de sistemas distribuídos.

**Descrição**

A DHT é formada por um conjunto de nós, onde cada nó é responsável por armazenar um intervalo de chaves, organizadas em uma topologia circular, crescente no sentido horário. Ao todo são 2^32 valores que podem ser distribuídos nos nós. Cada nó conhece apenas o seu antecessor e seu sucessor, sendo seu intervalo de responsabilidade de chaves igual a (id_antecessor, id_noAtual]. O número de nós é indefinido, assim, novos nós podem sair e entrar na DHT. Na entrada de um nó, apenas o antecessor e o sucessor devem ser atualizados. Com isso, esses nós respondem ao pedido de entrada na DHT indicando o que são para quem está entrando e alteram seu intervalo de responsabilidade, além disso, algumas chaves que antes eram de sua responsabilidade, agoram são do novo nó, com isso, a redistribuição  feita enviando os valores pelo método put e recebidas pelo tópico get pelo novo nó. Na sada de um nó.... <FALAR SOBRE SAÍDA>. Clientes publicam valores strings

**Implementação**

Ao ser inicializado, o nó da DHT deve avisar aos outros por meio do publish de seu nodeID no topic "join", o qual determinará seu intervalo de responsabilidade. Além disso, ele também se inscreve nesse tópico para receber o nodeID dos outros. Ao receber o nodeID de todos os nós (nesse caso 8, inclusive o seu próprio), o nó está pronto para receber mensagens, no entanto, isso não garante que os outros nós também estejam prontos, ou seja, não garante que eles receberam todos os nodeIDs também. O nó agora envia seu nodeID no topic "ack-join" e também se inscreve nele. Quando todos os nodesIDs são recebidos pelo tópico "ack-join" o nó se inscreve nos tópicos put e get, que são os tópicos no qual o cliente irá publicar mensagens.

O cliente gera 100 chaves aleatórias e as utiliza para inserir 100 strings aleatórias na DHT, publicando mensagens no tópico "put". Após recebimento das mensagens de confirmação — publicadas no tópico "ack-put" pelo nó responsável por armazenar o valor inserido, — o cliente resgata os mesmos valores utilizando apenas as 100 chaves geradas, publicando mensagens no tópico "get" e recebendo os valores por mensagens de tópico "res-get".

## Pré-requisitos
```
sudo apt-get install mosquitto
pip3 install paho-mqtt
pip3 install numpy
pip3 install Django
```

## Execução

O broker escolhido foi o Mosquitto que usa o protocolo MQTT. Configurações padrão de IP e porta (127.0.0.1:1883).

Criação dos nós da DHT: 8 nós devem ser executados para iniciar o recebimento das mensagens.
```
python3 Node.py <nome_do_nó>
```
Em que <nome_do_nó> deve se substituído por um número ou string. Não é um argumento obrigatório e deve ser único.



O cliente é executado da seguinte maneira:
```
python3 Cliente.py
```

## Automatização

Para iniciar todos os nós em background, execute o script runAllNodes.sh

```
bash runAllNodes.sh <num_nodes>
```
Substituindo <num_nodes> pela quantidade de nós que deseja iniciar. Não é um argumento obrigatório, caso não seja informado, 8 nós serão criados. Você pode conferir os logs dos nós no arquivo log.txt gerado.
