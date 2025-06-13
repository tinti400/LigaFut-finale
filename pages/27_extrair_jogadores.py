import pandas as pd

# Caminho do arquivo CSV original (ajuste o nome se for diferente)
caminho_arquivo = "male_players.csv"

# Colunas que queremos manter
colunas = ['short_name', 'player_positions', 'overall', 'value_eur']

# Lê o CSV com as colunas desejadas
df = pd.read_csv(caminho_arquivo, usecols=colunas)

# Renomeia as colunas para o padrão LigaFut
df.rename(columns={
    'short_name': 'nome',
    'player_positions': 'posição',
    'overall': 'overall',
    'value_eur': 'valor'
}, inplace=True)

# Remove jogadores duplicados pelo nome
df = df.drop_duplicates(subset='nome')

# Remove linhas sem nome ou valor
df = df.dropna(subset=['nome', 'valor'])

# Converte valores para inteiro (R$)
df['valor'] = df['valor'].astype(int)

# Ordena pelo overall (opcional)
df = df.sort_values(by='overall', ascending=False)

# Salva no formato Excel
df.to_excel("jogadores_ligafut.xlsx", index=False)

print("✅ Arquivo jogadores_ligafut.xlsx gerado com sucesso!")
