import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Classificação", page_icon="📊", layout="centered")
st.title("📊 Tabela de Classificação")

# 🔒 Verifica login
if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

# 🎯 Dados da sessão
divisao = st.session_state.get("divisao", "Divisão 1")
numero_divisao = divisao.split()[-1]
nome_tabela_rodadas = f"rodadas_divisao_{numero_divisao}"

# 📥 Obter os resultados das rodadas
def buscar_resultados():
    return supabase.table(nome_tabela_rodadas).select("*").execute().data

# 📥 Obter os nomes dos times
def obter_nomes_times():
    res_nomes = supabase.table("times").select("id", "nome").execute()
    return {t["id"]: t["nome"] for t in res_nomes.data}

# 🧠 Função para calcular a classificação com validação dos resultados
def calcular_classificacao(rodadas, times_map):
    tabela = {}

    for time_id in times_map:
        tabela[time_id] = {
            "nome": times_map.get(time_id, "Desconhecido"),
            "pontos": 0,
            "v": 0,
            "e": 0,
            "d": 0,
            "gp": 0,
            "gc": 0,
            "sg": 0
        }

    for rodada in rodadas:
        for jogo in rodada["jogos"]:
            mandante = jogo["mandante"]
            visitante = jogo["visitante"]
            # Se o valor dos gols estiver vazio, desconsidera essa rodada
            gm = jogo.get("gols_mandante")
            gv = jogo.get("gols_visitante")

            # Se algum dos gols estiver vazio, desconsidera o jogo
            if gm is None or gv is None:
                continue  # Ignora esse jogo e passa para o próximo

            # Agora podemos somar os valores dos gols, pois ambos são válidos
            gm = int(gm)
            gv = int(gv)

            # Atualizando gols, saldo de gols
            tabela[mandante]["gp"] += gm
            tabela[mandante]["gc"] += gv
            tabela[mandante]["sg"] += gm - gv

            tabela[visitante]["gp"] += gv
            tabela[visitante]["gc"] += gm
            tabela[visitante]["sg"] += gv - gm

            # Atualizando pontos e vitórias/derrotas/empates
            if gm > gv:
                tabela[mandante]["pontos"] += 3
                tabela[mandante]["v"] += 1
                tabela[visitante]["d"] += 1
            elif gm < gv:
                tabela[visitante]["pontos"] += 3
                tabela[visitante]["v"] += 1
                tabela[mandante]["d"] += 1
            else:
                tabela[mandante]["pontos"] += 1
                tabela[visitante]["pontos"] += 1
                tabela[mandante]["e"] += 1
                tabela[visitante]["e"] += 1

    # Ordenar por pontos, saldo de gols e gols marcados
    classificacao = sorted(
        tabela.items(),
        key=lambda x: (x[1]["pontos"], x[1]["sg"], x[1]["gp"]),
        reverse=True
    )

    return classificacao

# 🚨 Exibir tabela de classificação
rodadas_existentes = buscar_resultados()
times_map = obter_nomes_times()

# Calcular a classificação com base nas rodadas
classificacao = calcular_classificacao(rodadas_existentes, times_map)

# Organizar em DataFrame
dados_classificacao = []
for i, (time_id, dados) in enumerate(classificacao, 1):
    dados_classificacao.append({
        "Posição": i,
        "Time": dados["nome"],
        "Pontos": dados["pontos"],
        "Jogos": dados["v"] + dados["e"] + dados["d"],
        "Vitórias": dados["v"],
        "Empates": dados["e"],
        "Derrotas": dados["d"],
        "Gols Marcados": dados["gp"],
        "Gols Sofridos": dados["gc"],
        "Saldo de Gols": dados["sg"]
    })

# Criar DataFrame
df_classificacao = pd.DataFrame(dados_classificacao)

# Exibir a tabela no Streamlit com um visual mais bonito
st.markdown("### Classificação Atual:")
st.dataframe(df_classificacao.style.format({
    'Pontos': '{:,.0f}', 
    'Jogos': '{:,.0f}', 
    'Vitórias': '{:,.0f}', 
    'Empates': '{:,.0f}', 
    'Derrotas': '{:,.0f}', 
    'Gols Marcados': '{:,.0f}', 
    'Gols Sofridos': '{:,.0f}', 
    'Saldo de Gols': '{:,.0f}'
}).background_gradient(axis=None, gmap={1:'green', -1:'red'}, subset=['Pontos']))
