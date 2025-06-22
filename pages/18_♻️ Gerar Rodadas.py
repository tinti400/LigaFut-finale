# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random
from itertools import combinations

st.set_page_config(page_title="♻️ Gerar Rodadas T2", layout="wide")
st.title("♻️ Gerar Rodadas - Temporada 2")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🧠 Nome da tabela
def nome_tabela_rodadas(divisao):
    return f"rodadas_temporada_2_divisao_{divisao}"

# 🧼 Apagar rodadas antigas
def apagar_rodadas_antigas(tabela):
    try:
        supabase.table(tabela).delete().neq("id", "").execute()
        st.success(f"🧹 Rodadas antigas apagadas da tabela `{tabela}`.")
    except Exception as e:
        if "does not exist" in str(e).lower():
            st.info(f"ℹ️ Tabela `{tabela}` ainda não existe (nada a apagar).")
        else:
            st.error(f"❌ Erro ao apagar rodadas da tabela `{tabela}`: {e}")

# ⚽ Gerar rodadas com turno e returno
def gerar_rodadas(times):
    random.shuffle(times)
    jogos_turno = list(combinations(times, 2))
    random.shuffle(jogos_turno)

    total_rodadas = len(times) - 1
    rodadas_turno = [[] for _ in range(total_rodadas)]

    for mandante, visitante in jogos_turno:
        for rodada in rodadas_turno:
            usados = [j['mandante'] for j in rodada] + [j['visitante'] for j in rodada]
            if mandante["id"] not in usados and visitante["id"] not in usados:
                rodada.append({
                    "mandante": mandante["id"],
                    "visitante": visitante["id"]
                })
                break

    rodadas_returno = [
        [{"mandante": jogo["visitante"], "visitante": jogo["mandante"]} for jogo in rodada]
        for rodada in rodadas_turno
    ]

    return rodadas_turno + rodadas_returno

# 🔁 Loop por divisão
for divisao in [1, 2, 3]:
    st.markdown(f"## 📅 Temporada 2 | Divisão {divisao}")
    try:
        # 🎯 Buscar usuários com times na divisão
        res = supabase.table("usuarios").select("id_time, nome_time, divisao").eq("divisao", divisao).execute()
        usuarios = res.data

        if not usuarios:
            st.warning(f"⚠️ Nenhum time encontrado para a Divisão {divisao}.")
            continue

        times = [{"id": u["id_time"], "nome": u["nome_time"]} for u in usuarios if u.get("id_time") and u.get("nome_time")]

        if len(times) < 2:
            st.warning(f"⚠️ Poucos times na Divisão {divisao} para gerar rodadas.")
            continue

        tabela = nome_tabela_rodadas(divisao)
        apagar_rodadas_antigas(tabela)

        rodadas = gerar_rodadas(times)

        for i, rodada in enumerate(rodadas, start=1):
            dados = {
                "numero": i,
                "jogos": rodada,
                "data_criacao": datetime.now().isoformat()
            }
            supabase.table(tabela).insert(dados).execute()

        st.success(f"✅ {len(rodadas)} rodadas geradas para a Divisão {divisao}.")

    except Exception as e:
        st.error(f"❌ Erro ao buscar usuários ou gerar rodadas: {e}")
