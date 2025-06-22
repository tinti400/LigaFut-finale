# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import random
from itertools import combinations
from datetime import datetime

st.set_page_config(page_title="♻️ Gerar Rodadas", layout="wide")
st.title("♻️ Gerar Rodadas - LigaFut")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🧠 Função para nome da tabela
def nome_tabela_rodadas(divisao):
    return f"rodadas_divisao_{divisao}"

# 🧼 Função para apagar rodadas anteriores
def apagar_rodadas_antigas(tabela):
    try:
        res = supabase.table(tabela).select("id").execute()
        if res.data:
            for item in res.data:
                supabase.table(tabela).delete().eq("id", item["id"]).execute()
            st.success(f"🧹 Rodadas antigas apagadas da tabela `{tabela}`.")
        else:
            st.info(f"ℹ️ Tabela `{tabela}` ainda não possui rodadas (nada a apagar).")
    except Exception as e:
        if "does not exist" in str(e).lower():
            st.info(f"ℹ️ Tabela `{tabela}` ainda não existe.")
        else:
            st.error(f"❌ Erro ao apagar rodadas da tabela `{tabela}`: {e}")

# ⚽ Geração das rodadas com turno e returno
def gerar_rodadas(times_ids):
    random.shuffle(times_ids)
    jogos = list(combinations(times_ids, 2))  # todos contra todos
    random.shuffle(jogos)

    qtd_rodadas = len(times_ids) - 1
    rodadas_turno = [[] for _ in range(qtd_rodadas)]

    for jogo in jogos:
        for rodada in rodadas_turno:
            ja_na_rodada = [j["mandante"] for j in rodada] + [j["visitante"] for j in rodada]
            if jogo[0] not in ja_na_rodada and jogo[1] not in ja_na_rodada:
                rodada.append({"mandante": jogo[0], "visitante": jogo[1]})
                break

    rodadas_returno = [
        [{"mandante": j["visitante"], "visitante": j["mandante"]} for j in rodada]
        for rodada in rodadas_turno
    ]

    return rodadas_turno + rodadas_returno

# 🔁 Loop pelas divisões (1 a 3)
for divisao in [1, 2, 3]:
    st.markdown(f"## 📅 Divisão {divisao}")

    tabela_rodadas = nome_tabela_rodadas(divisao)

    # 🔄 Buscar times da divisão
    try:
        res_times = supabase.table("times").select("id").eq("divisao", divisao).execute()
        lista_times = [t["id"] for t in res_times.data if "id" in t]

        if len(lista_times) < 2:
            st.warning(f"⚠️ Divisão {divisao} precisa de pelo menos 2 times.")
            continue

        # 🧹 Limpar rodadas antigas
        apagar_rodadas_antigas(tabela_rodadas)

        # ⚽ Gerar novas rodadas
        rodadas = gerar_rodadas(lista_times)

        for i, rodada in enumerate(rodadas, start=1):
            supabase.table(tabela_rodadas).insert({
                "numero": i,
                "jogos": rodada,
                "data_criacao": datetime.now().isoformat()
            }).execute()

        st.success(f"✅ {len(rodadas)} rodadas geradas para a divisão {divisao}.")
    except Exception as e:
        st.error(f"❌ Erro ao gerar rodadas da divisão {divisao}: {e}")
