## -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import requests
import random
from itertools import combinations
from datetime import datetime

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🧠 Função para montar nome da tabela
def nome_tabela_rodadas(temporada, divisao):
    return f"rodadas_temporada_{temporada}_divisao_{divisao}"

# 🧠 Verifica se a tabela existe
def tabela_existe(nome_tabela):
    url_api = f"{url}/rest/v1/{nome_tabela}?limit=1"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}"
    }
    response = requests.get(url_api, headers=headers)
    return response.status_code != 404

# 🧼 Apaga rodadas antigas se a tabela existir
def apagar_rodadas_antigas(tabela):
    if tabela_existe(tabela):
        supabase.table(tabela).delete().execute()
        st.success(f"Rodadas antigas apagadas da tabela `{tabela}`.")
    else:
        st.info(f"Tabela `{tabela}` ainda não existe (nada a apagar).")

# ⚽ Função para gerar rodadas (turno e returno)
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
        st.markdown(f"### Temporada {temporada} | Divisão {divisao}")

        tabela_rodadas = nome_tabela_rodadas(temporada, divisao)
        apagar_rodadas_antigas(tabela_rodadas)

        res = supabase.table("times").select("id").eq("divisao", divisao).eq("temporada", temporada).execute()
        lista_times = [item["id"] for item in res.data]

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

        st.success(f"✅ {len(rodadas)} rodadas geradas para {tabela_rodadas}.")
