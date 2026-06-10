# Importa a função de inicialização do seu arquivo de banco de dados
from data.database.db import initdb
from data.collector.collector import executar_coleta


def main():
    print("Verificando/Inicializando o banco de dados...")
    initdb()
    
    print("Iniciando o motor de coleta da API...")
    executar_coleta()
    
    print("Operação concluída com sucesso.")

