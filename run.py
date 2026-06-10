import sys
import os

# 1. BLINDAGEM DO CAMINHO ABSOLUTO
# Anula o erro da pasta 'data' ao forçar o interpretador a usar a raiz do projeto
CAMINHO_RAIZ = os.path.dirname(os.path.abspath(__file__))
if CAMINHO_RAIZ not in sys.path:
    sys.path.insert(0, CAMINHO_RAIZ)

# 2. IMPORTAÇÕES DOS MÓDULOS DE ENGENHARIA DE DADOS
from data.database.db import initdb
from data.collector.collector import executar_coleta

# 3. IMPORTAÇÕES DOS MÓDULOS DE CIÊNCIA DE DADOS (Condicionais)
# Permite que o menu rode mesmo que estes ficheiros ainda não tenham sido criados
try:
    from data.preprocessing.dataset_builder import construir_dataset
except ImportError:
    construir_dataset = None

try:
    from data.training.train import treinar_modelo
except ImportError:
    treinar_modelo = None

# 4. ORQUESTRAÇÃO INTERATIVA
def menu():
    while True:
        print("\n" + "="*45)
        print(" PIPELINE: BRAWL STARS MACHINE LEARNING ")
        print("="*45)
        print("1. Inicializar/Resetar Banco de Dados")
        print("2. Iniciar Coleta de Dados (Motor Crawler)")
        print("3. Construir Dataset (Pré-processamento Pandas)")
        print("4. Treinar Modelo Preditivo (Scikit-Learn)")
        print("0. Sair")
        print("="*45)
        
        escolha = input("Escolha a etapa a executar: ")
        
        if escolha == '1':
            print("\n[Executando] Recriação da estrutura SQL...")
            initdb()
            print("Concluído.")
            
        elif escolha == '2':
            print("\n[Executando] Inicialização do Crawler...")
            executar_coleta()
            
        elif escolha == '3':
            if construir_dataset:
                print("\n[Executando] Achatamento Relacional e Geração de CSV...")
                construir_dataset()
            else:
                print("\n[Erro Estrutural] O módulo 'dataset_builder.py' não foi encontrado.")
                print("Crie o ficheiro na pasta 'data/preprocessing/' antes de usar esta opção.")
                
        elif escolha == '4':
            if treinar_modelo:
                print("\n[Executando] Treino do Algoritmo Random Forest...")
                treinar_modelo()
            else:
                print("\n[Erro Estrutural] O módulo 'train.py' não foi encontrado.")
                print("Crie o ficheiro na pasta 'data/prediction/' antes de usar esta opção.")
                
        elif escolha == '0':
            print("\nSistema encerrado de forma segura.")
            break
            
        else:
            print("\n[Aviso] Opção inválida. Digite um número de 0 a 4.")

if __name__ == "__main__":
    menu()