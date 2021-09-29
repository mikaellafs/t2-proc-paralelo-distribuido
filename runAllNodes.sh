#!/bin/bash
ctrlCHandler()
{
	pID=$$
    kill -9 -${pID}
	exit 1
}


trap ctrlCHandler SIGINT;

echo "" > log.txt #limpa arquivo de log

totalNodes=50
if [ "$1" != "" ]; then 
	totalNodes=$1
fi

CONTADOR=0
while [  $CONTADOR -lt ${totalNodes} ]; do
	python3 -u Node.py >> log.txt &		
	let CONTADOR=CONTADOR+1;
	sleep 0.5
done

echo "Nodes criados, aguarde até que todos fiquem prontos..."
echo "Aperte Ctrl-C para encerrar a DHT"

while true; do true; done # para aguardar o encerramento
