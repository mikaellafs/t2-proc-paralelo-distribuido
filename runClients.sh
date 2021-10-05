echo "" > logClients.txt #limpa arquivo de log

totalClientes=5
if [ "$1" != "" ]; then 
	totalClientes=$1
fi

echo "Criando ${totalClientes} clientes..."

CONTADOR=0
while [ $CONTADOR -lt $totalClientes ]; do
	python3 -u Cliente.py >> logClients.txt &		
	let CONTADOR=CONTADOR+1;
	sleep 0.5
done

echo "Pronto!"

