# Trabalho T2 - DHT

### **Objetivo**

Experimentar a implementação de sistemas de comunicação indireta por meio de middleware Publish/Subscribe com Filas de Mensagens. Sincronizar a troca de mensagens entre os componentes do sistema. Utilizar brokers de troca de mensagens na implementação de sistemas distribuídos.

### **Descrição**

A DHT é formada por um conjunto de nós, e cada nó é responsável por armazenar um intervalo de chaves, organizadas em uma topologia circular, crescente no sentido horário. Ao todo são 2<sup>32</sup> valores que podem ser distribuídos nos nós. Cada nó conhece apenas o seu antecessor e seu sucessor, sendo seu intervalo de responsabilidade de chaves igual a (id_antecessor, id_proprio].

O número de nós é indefinido, assim, novos nós podem sair e entrar na DHT. Na entrada de um nó, o antecessor e o sucessor devem ser atualizados. Com isso, esses nós respondem ao pedido de entrada na DHT indicando o que são para quem está entrando e alteram seu intervalo de responsabilidade. Além disso, algumas chaves que antes eram de sua responsabilidade, agora são do novo nó, assim a redistribuição é feita enviando os valores pelo método `put` e recebidas pelo tópico `get` pelo novo nó.

Na saída de um nó A, seu sucessor deve alterar o próprio intervalo de responsabilidade de modo a cobrir o intervalo que o A deixará de cobrir. O antecessor de A não altera o próprio intervalo de responsabilidade, mas altera o próprio sucessor. As chaves que eram da responsabilidade de A devem ser reintroduzidas à DHT pelo método ``put``.

Clientes publicam valores (strings) com uma determinada chave no tópico `put`. Todos os nós recebem a mensagem, mas apenas o nó responsável pelo intervalo de chaves no qual a chave da mensagem está inclusa armazena o valor. Da mesma forma para a recuperação de chaves pelos clientes, todos os nós recebem a mensagem que o cliente publica no tópico `get`, mas ao verificar o intervalo de responsabilidade, somente um nó responde ao cliente. Vários clientes podem publicar e recuperar valores ao mesmo tempo, por isso, os clientes foram implementados com um identificador.

### **Implementação**

O primeiro nó deve iniciar a DHT e ser responsável por armazenar todas as chaves no espaço de endereçamento. Para este nó saber que é o primeiro, ele envia continuamente seu nodeID no tópico `join` esperando algum retorno de algum nó da DHT. Se não houver resposta dentro de 100 tentativas, ele começa a DHT sozinho. Os próximos nós que entrarem seguem a mesma ideia, no entanto, recebem um retorno do(s) nó(s) da DHT pelo tópico `has_started`. Ao receber o retorno, o nó entrando espera pelo recebimento do seu antecessor e sucessor pelo tópico `ack-join` no formato padronizado. Após isso, ele envia uma confirmação e só assim ele pode se inscrever nos tópicos de `put` e `get`.

Para que um nó saia, ele deve enviar seu nodeID para o tópico ``leave``e aguardar que seu antecessor e sucessor estejam prontos, ou seja, tenham realizado as devidas alterações. O nó sucessor ao que está saindo deve alterar seu intervalo de responsabilidade substituindo seu antecessor pelo antecessor que recebe na mensagem ``leave``. O nó antecessor não altera seu intervalo de responsabilidade mas deve atualizar seu sucessor para o sucessor recebido na mensagem ``leave``. Em seguida, o nó saindo envia seus pares chave/valor para a DHT utilizando mensagens ``put`` e se desconecta.

O cliente gera 100 chaves aleatórias e as utiliza para inserir 100 strings aleatórias na DHT, publicando mensagens no tópico `put`. Após recebimento das mensagens de confirmação — publicadas no tópico ``ack-put`` pelo nó responsável por armazenar o valor inserido, — o cliente resgata os mesmos valores utilizando apenas as 100 chaves geradas, publicando mensagens no tópico ``get`` e recebendo os valores por mensagens de tópico ``res-get``.

## Pré-requisitos
```
sudo apt-get install mosquitto
pip3 install paho-mqtt
pip3 install numpy
pip3 install Django
```

## Execução

O broker escolhido foi o Mosquitto que usa o protocolo MQTT. Configurações padrão de IP e porta (127.0.0.1:1883).

Criação dos nós da DHT: pelo menos um nó deve ser executado para iniciar o recebimento das mensagens.
```
python3 Node.py <nome_do_nó>
```
Em que ``<nome_do_nó>`` deve ser substituído por um número ou string. Não é um argumento obrigatório, mas deve ser único se usado.

O cliente é executado da seguinte maneira:
```
python3 Cliente.py <wait>
```
Substituindo ``<wait>`` por 1, caso queira esperar por uma confirmação antes de recuperar as chaves pelo tópico get. Caso nenhum valor seja informado, não haverá confirmação, portanto é um argumento opcional.

## Automatização

Para iniciar todos os nós em background, execute o script ``runAllNodes.sh``

```
bash runAllNodes.sh <num_nodes>
```
Substituindo ``<num_nodes>`` pela quantidade de nós que deseja iniciar. Não é um argumento obrigatório, caso não seja informado, 8 nós serão criados. Você pode conferir os logs dos nós no arquivo log.txt gerado.

Para rodar vários clientes, execute o script ``runClientes.sh``.

```
bash runClients.sh <num_clients>
```
Substituindo ``<num_clients>`` pela quantidade de clientes que deseja criar. Não é um argumento obrigatório, caso não seja informado, 5 clientes serão criados. Você pode conferir os logs dos clientes no arquivo logClients.txt gerado.
