# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import random
from itertools import combinations
from datetime import datetime

st.set_page_config(page_title="♻️ Gerar Rodadas", layout="wide")
st.title("♻️ Gerar Rodadas - LigaFut")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🧠 Função para montar nome da tabela
def nome_tabela_rodadas(temporada, divisao):
    return f"rodadas_temporada_{temporada}_divisao_{divisao}"

# 🧼 Apaga rodadas antigas com tratamento seguro (evita erro DELETE requires WHERE)
def apagar_rodadas_antigas(tabela):
    try:
        supabase.table(tabela).delete().neq("id", "").execute()
        st.success(f"🧹 Rodadas antigas apagadas da tabela `{tabela}`.")
    except Exception as e:
        if "does not exist" in str(e).lower():
            st.info(f"ℹ️ Tabela `{tabela}` ainda não existe (nada a apagar).")
        else:
            st.error(f"❌ Erro ao apagar rodadas da tabela `{tabela}`: {e}")

# ⚽ Gera rodadas com turno e returno
def gerar_rodadas(times):
    random.shuffle(times)
    jogos_turno = list(combinations(times, 2))
    random.shuffle(jogos_turno)

    total_rodadas = len(times) - 1
    rodadas_turno = [[] for _ in range(total_rodadas)]

    for jogo in jogos_turno:
        for rodada in rodadas_turno:
            times_na_rodada = [j['mandante'] for j in rodada] + [j['visitante'] for j in rodada]
            if jogo[0] not in times_na_rodada and jogo[1] not in times_na_rodada:
                rodada.append({"mandante": jogo[0], "visitante": jogo[1]})
                break

    rodadas_returno = [
        [{"mandante": jogo["visitante"], "visitante": jogo["mandante"]} for jogo in rodada]
        for rodada in rodadas_turno
    ]

    return rodadas_turno + rodadas_returno

# 🔁 Loop por temporada e divisão
for temporada in [1, 2, 3]:
    for divisao in [1, 2, 3]:
        st.markdown(f"## 📅 Temporada {temporada} | Divisão {divisao}")

        tabela_rodadas = nome_tabela_rodadas(temporada, divisao)

        # ⚠️ Validação antes de buscar times
        if not temporada or not divisao:
            st.error("❌ Temporada ou divisão inválida.")
            continue

        # 🧹 Apagar rodadas anteriores
        apagar_rodadas_antigas(tabela_rodadas)

        try:
            # 🔄 Buscar times da divisão e temporada
            res = supabase.table("times").select("id").eq("divisao", divisao).eq("temporada", temporada).execute()
            lista_times = [item["id"] for item in res.data if "id" in item]

            if len(lista_times) < 2:
                st.warning(f"⚠️ Poucos times para gerar rodadas na Divisão {divisao}, Temporada {temporada}.")
                continue

            rodadas = gerar_rodadas(lista_times)

            for i, rodada in enumerate(rodadas, start=1):
                dados = {
                    "numero": i,
                    "jogos": rodada,
                    "data_criacao": datetime.now().isoformat()
                }
                supabase.table(tabela_rodadas).insert(dados).execute()

            st.success(f"✅ {len(rodadas)} rodadas geradas para `{tabela_rodadas}`.")
        except Exception as e:
            st.error(f"❌ Erro ao gerar rodadas da `{tabela_rodadas}`: {e}")
