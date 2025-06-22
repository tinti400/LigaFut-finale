# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from itertools import combinations
import random
from datetime import datetime

st.set_page_config(page_title="♻️ Gerar Rodadas - Temporada 2", layout="wide")
st.markdown("<h1 style='text-align:center;'>♻️ Gerar Rodadas - Temporada 2</h1><hr>", unsafe_allow_html=True)

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# Função para apagar rodadas anteriores
def apagar_rodadas(tabela):
    try:
        supabase.table(tabela).delete().neq("id", 0).execute()
        return True, None
    except Exception as e:
        return False, str(e)

# Função para gerar confrontos (turno e returno)
def gerar_confrontos(times):
    random.shuffle(times)
    confrontos = list(combinations(times, 2))
    jogos = []
    for i, (mandante, visitante) in enumerate(confrontos):
        jogos.append({
            "mandante_id": mandante["id"],
            "visitante_id": visitante["id"],
            "mandante": mandante["nome"],
            "visitante": visitante["nome"]
        })
    for i, (mandante, visitante) in enumerate(confrontos):
        jogos.append({
            "mandante_id": visitante["id"],
            "visitante_id": mandante["id"],
            "mandante": visitante["nome"],
            "visitante": mandante["nome"]
        })
    return jogos

# Função para distribuir jogos em rodadas
def distribuir_em_rodadas(jogos, times_por_divisao):
    rodadas = []
    rodada_atual = []
    times_rodada = set()

    for jogo in jogos:
        if jogo["mandante_id"] not in times_rodada and jogo["visitante_id"] not in times_rodada:
            rodada_atual.append(jogo)
            times_rodada.add(jogo["mandante_id"])
            times_rodada.add(jogo["visitante_id"])

        if len(rodada_atual) == len(times_por_divisao) // 2:
            rodadas.append(rodada_atual)
            rodada_atual = []
            times_rodada = set()

    if rodada_atual:
        rodadas.append(rodada_atual)

    return rodadas

# Função principal para gerar rodadas
def gerar_rodadas(temporada, divisao):
    nome_tabela = f"rodadas_temporada_{temporada}_divisao_{divisao}"
    try:
        # Buscar todos os usuários com time_id e divisão
        usuarios = supabase.table("usuarios").select("time_id, Divisão").execute().data
        if not usuarios:
            st.error("Nenhum usuário encontrado.")
            return

        # Filtrar times da divisão específica
        usuarios_divisao = [u for u in usuarios if u.get("Divisão") == f"Divisão {divisao}" and u.get("time_id")]
        if not usuarios_divisao:
            st.warning(f"Nenhum time encontrado para a Divisão {divisao}.")
            return

        # Buscar nomes dos times a partir dos IDs
        time_ids = [u["time_id"] for u in usuarios_divisao]
        times_data = supabase.table("times").select("id, nome").in_("id", time_ids).execute().data

        if not times_data:
            st.warning(f"Times não encontrados na tabela 'times'.")
            return

        # Mapear IDs e nomes
        times = [{"id": t["id"], "nome": t["nome"]} for t in times_data]

        # Gerar confrontos e rodadas
        jogos = gerar_confrontos(times)
        rodadas = distribuir_em_rodadas(jogos, times)

        # Apagar rodadas antigas
        apagado, erro = apagar_rodadas(nome_tabela)
        if not apagado:
            st.error(f"Erro ao apagar rodadas da tabela {nome_tabela}: {erro}")
            return

        # Inserir novas rodadas
        for i, rodada in enumerate(rodadas, 1):
            nova_rodada = {
                "numero": i,
                "jogos": rodada,
                "data_criacao": datetime.now().isoformat()
            }
            supabase.table(nome_tabela).insert(nova_rodada).execute()

        st.success(f"✅ Rodadas da Divisão {divisao} - Temporada {temporada} geradas com sucesso!")

    except Exception as e:
        st.error(f"❌ Erro ao buscar usuários ou gerar rodadas: {e}")

# Interface Streamlit
for divisao in [1, 2, 3]:
    with st.expander(f"📅 Temporada 2 | Divisão {divisao}"):
        if st.button(f"🛠️ Gerar Rodadas Divisão {divisao}", key=f"btn_div_{divisao}"):
            gerar_rodadas(temporada=2, divisao=divisao)
