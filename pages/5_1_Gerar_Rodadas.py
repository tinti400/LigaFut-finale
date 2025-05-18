# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import itertools
import random

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Gerar Rodadas", page_icon="⚙️", layout="centered")
st.title("⚙️ Gerar Rodadas da Divisão")

# 🔹 Selecionar divisão
opcao_divisao = st.selectbox("Selecione a Divisão", ["Divisão 1", "Divisão 2"])
numero_divisao = opcao_divisao.split()[-1]
tabela_rodadas = f"rodadas_divisao_{numero_divisao}"

# 📅 Buscar times pela divisão da tabela usuarios
try:
    usuarios = supabase.table("usuarios").select("time_id").eq("Divisão", opcao_divisao).execute().data
    time_ids = list({u["time_id"] for u in usuarios if u.get("time_id")})
except Exception as e:
    st.error(f"Erro ao buscar times: {e}")
    st.stop()

if st.button(f"⚙️ Gerar Rodadas da {opcao_divisao}"):
    if len(time_ids) < 2:
        st.warning("🚨 É necessário no mínimo 2 times para gerar rodadas.")
        st.stop()

    # 🔄 Apagar rodadas antigas
    try:
        supabase.table(tabela_rodadas).delete().neq("numero", -1).execute()
    except Exception as e:
        st.error(f"Erro ao apagar rodadas antigas: {e}")
        st.stop()

    # ⚽ Gerar confrontos de turno e returno
    confrontos = list(itertools.combinations(time_ids, 2))
    ida = [{"mandante": a, "visitante": b, "gols_mandante": None, "gols_visitante": None} for a, b in confrontos]
    volta = [{"mandante": b, "visitante": a, "gols_mandante": None, "gols_visitante": None} for a, b in confrontos]
    todos_jogos = ida + volta
    random.shuffle(todos_jogos)

    max_por_rodada = len(time_ids) // 2
    rodadas = []

    while todos_jogos:
        rodada = []
        usados = set()
        for j in todos_jogos[:]:
            if j["mandante"] not in usados and j["visitante"] not in usados:
                rodada.append(j)
                usados.update([j["mandante"], j["visitante"]])
                todos_jogos.remove(j)
                if len(rodada) == max_por_rodada:
                    break
        rodadas.append(rodada)

    # 💾 Salvar rodadas
    try:
        for i, jogos in enumerate(rodadas, 1):
            supabase.table(tabela_rodadas).insert({"numero": i, "jogos": jogos}).execute()
        st.success(f"✅ {len(rodadas)} rodadas geradas com sucesso para {opcao_divisao}!")
    except Exception as e:
        st.error(f"Erro ao salvar rodadas: {e}")
