import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

def treinar_modelo():
    print("A carregar o dataset...")
    
    # Ajuste este caminho dependendo de onde guardar o train.py
    # Este código pressupõe que o train.py está dentro de data/prediction/
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_csv = os.path.abspath(os.path.join(diretorio_atual, "..", "..", "dataset_brawl.csv"))
    
    try:
        df = pd.read_csv(caminho_csv)
    except FileNotFoundError:
        print(f"Erro Crítico: Ficheiro não encontrado no caminho {caminho_csv}")
        return

    print(f"Dataset carregado com {len(df)} partidas. A iniciar transformação matricial...")

    # 1. Transformar Variáveis Categóricas Básicas (Modo e Mapa)
    # Converte 'mode' e 'map' em colunas de 0 e 1
    df_encoded = pd.get_dummies(df, columns=['mode', 'map'])

# 2. Transformação do Grafo de Equipas (Multi-Hot Encoding)
    print("A nivelar a ordem dos Brawlers (Invariância Permutacional)...")
    todos_brawlers = set(df['t0_brawler_1']).union(
        df['t0_brawler_2'], df['t0_brawler_3'],
        df['t1_brawler_1'], df['t1_brawler_2'], df['t1_brawler_3']
    )

    # CORREÇÃO DE PERFORMANCE: Criação de todas as colunas de uma vez só em um dicionário
    novas_colunas = {}
    for brawler in todos_brawlers:
        novas_colunas[f't0_{brawler}'] = 0
        novas_colunas[f't1_{brawler}'] = 0

    # Converte o dicionário em DataFrame temporário e une ao principal sem fragmentar a memória
    df_novas = pd.DataFrame(novas_colunas, index=df_encoded.index)
    df_encoded = pd.concat([df_encoded, df_novas], axis=1)

    # Povoamento binário: assinala '1' se o brawler estiver na equipe, ignorando o slot
    for i in range(1, 4):
        for brawler in todos_brawlers:
            df_encoded.loc[df[f't0_brawler_{i}'] == brawler, f't0_{brawler}'] = 1
            df_encoded.loc[df[f't1_brawler_{i}'] == brawler, f't1_{brawler}'] = 1

    # Remoção do "ruído" (strings originais e hashes irrelevantes para cálculo)
    colunas_texto = ['match_hash', 't0_brawler_1', 't0_brawler_2', 't0_brawler_3',
                     't1_brawler_1', 't1_brawler_2', 't1_brawler_3']
    df_encoded = df_encoded.drop(columns=colunas_texto)

    # 3. Definição do Alvo (O que queremos prever) e Funcionalidades (O que usamos para prever)
    X = df_encoded.drop(columns=['target'])
    y = df_encoded['target']

    # Separação: 80% para ensinar a máquina, 20% para a testar às cegas
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("A iniciar o treino do Algoritmo Gradient Boosting...")
    
    # O Gradient Boosting aprende sequencialmente. 
    # n_estimators: Número de iterações de correção de erro.
    # learning_rate: Impede que o modelo tome decisões demasiado drásticas de uma só vez.
    # max_depth: Limita a profundidade para evitar memorização excessiva (Overfitting).
    modelo = GradientBoostingClassifier(
        n_estimators=200, 
        learning_rate=0.05, 
        max_depth=4, 
        random_state=42
    )
    modelo.fit(X_train, y_train)

    # 4. Avaliação Matemática
    print("\nA extrair previsões sobre os dados de teste...")
    previsoes = modelo.predict(X_test)
    precisao = accuracy_score(y_test, previsoes)

    print("\n================ RESULTADOS ================")
    print(f"Precisão Base (Accuracy): {precisao * 100:.2f}%")
    print("--------------------------------------------")
    print(classification_report(y_test, previsoes, target_names=['Derrota Eq.0', 'Vitória Eq.0']))
    print("============================================")
    
    # NOVO BLOCO: Auditoria Matemática de Variáveis
    importancias = modelo.feature_importances_
    df_importancias = pd.DataFrame({'Variavel': X.columns, 'Peso_Matematico': importancias})
    # Ordena as variáveis da que tem mais impacto para a que tem menos
    df_importancias = df_importancias.sort_values(by='Peso_Matematico', ascending=False)
    
    print("\n--- TOP 10 VARIÁVEIS DE MAIOR IMPACTO NA PREVISÃO ---")
    print(df_importancias.head(10).to_string(index=False))
    print("-----------------------------------------------------")

    # 5. Guardar o estado cerebral da IA
    caminho_modelo = os.path.join(diretorio_atual, 'modelo_brawl.pkl')
    caminho_colunas = os.path.join(diretorio_atual, 'colunas_brawl.pkl')
    
    joblib.dump(modelo, caminho_modelo)
    joblib.dump(X.columns.tolist(), caminho_colunas)
    
    print(f"\nModelo matemático exportado: {caminho_modelo}")
    print("O ficheiro .pkl pode agora ser invocado para fazer previsões em tempo real.")

if __name__ == "__main__":
    treinar_modelo()