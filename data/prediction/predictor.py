import pandas as pd

def calcular_probabilidade_estatica(modelo, colunas_treino, modo, mapa, equipa_0, equipa_1):
    """Calcula a probabilidade de uma partida completa."""
    entrada = pd.DataFrame(0, index=[0], columns=colunas_treino)
    
    if f'mode_{modo}' in colunas_treino: entrada.at[0, f'mode_{modo}'] = 1
    if f'map_{mapa}' in colunas_treino: entrada.at[0, f'map_{mapa}'] = 1
    
    for b in equipa_0:
        if f't0_{b}' in colunas_treino: entrada.at[0, f't0_{b}'] = 1
    for b in equipa_1:
        if f't1_{b}' in colunas_treino: entrada.at[0, f't1_{b}'] = 1
        
    probabilidades = modelo.predict_proba(entrada)[0]
    return probabilidades[0] * 100, probabilidades[1] * 100

def recomendar_brawlers_draft(modelo, colunas_treino, modo, mapa, aliados, inimigos, brawlers_validos):
    """Executa simulações vetorizadas para preencher uma vaga na equipa aliada em milissegundos."""
    todos_selecionados = aliados + inimigos
    candidatos = [b for b in brawlers_validos if b not in todos_selecionados]
    
    if not candidatos:
        return []

    # 1. Cria a linha base com os dados estáticos da partida
    base_df = pd.DataFrame(0, index=[0], columns=colunas_treino)
    if f'mode_{modo}' in colunas_treino: base_df.at[0, f'mode_{modo}'] = 1
    if f'map_{mapa}' in colunas_treino: base_df.at[0, f'map_{mapa}'] = 1
    
    for b in aliados:
        if f't0_{b}' in colunas_treino: base_df.at[0, f't0_{b}'] = 1
    for b in inimigos:
        if f't1_{b}' in colunas_treino: base_df.at[0, f't1_{b}'] = 1

    # 2. Vetorização: Multiplica a linha base para o número exato de candidatos
    df_simulacao = pd.concat([base_df] * len(candidatos), ignore_index=True)
    
    # 3. Injeta cada candidato na sua respetiva linha (processamento rápido em memória)
    for i, candidato in enumerate(candidatos):
        if f't0_{candidato}' in colunas_treino:
            df_simulacao.at[i, f't0_{candidato}'] = 1
            
    # 4. Inferência em Bloco: O modelo prevê todas as combinações simultaneamente
    probabilidades = modelo.predict_proba(df_simulacao)
    
    resultados = []
    for i, candidato in enumerate(candidatos):
        prob_vitoria = probabilidades[i][1] * 100
        resultados.append((candidato, prob_vitoria))
        
    resultados.sort(key=lambda x: x[1], reverse=True)
    return resultados[:5]