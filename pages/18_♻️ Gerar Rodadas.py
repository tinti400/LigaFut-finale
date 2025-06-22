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

# 🧠 Montar nome da tabela de rodadas
def nome_tabela_rodadas(divisao):
    return f"rodadas_divisao_{divisao}"

# 🧼 Apagar rodadas antigas
def apagar_rodadas_antigas(tabela):
    try:
        res = supabase.table(tabela).select("id").execute()
        if res.data:
            for item in res.data:
                supabase.table(tabela).delete().eq("id", item["id"]).execute()
            st.success(f"🧹 {len(res.data)} rodadas apagadas da tabela `{tabela}`.")
        else:
            st.info(f"ℹ️ Nenhuma rodada antiga encontrada em `{tabela}`.")
    except Exception as e:
        if "does not exist" in str(e).lower():
            st.info(f"ℹ️ Tabela `{tabela}` ainda não existe.")
        else:
            st.error(f"❌ Erro ao apagar rodadas da tabela `{tabela}`: {e}")

# ⚽ Geração das rodadas com turno e returno
def gerar_rodadas(times_ids):
    random.shuffle(times_ids)
    jogos = list(combinations(times_ids, 2))
    random.shuffle(jogos)

    qtd_rodadas = len(times_ids) - 1
    rodadas_turno = [[] for _ in range(qtd_rodadas)]

    for jogo in jogos:
        for rodada in rodadas_turno:
            escalados = [j['mandante'] for j in rodada] + [j['visitante'] for j in rodada]
            if jogo[0] not in escalados and jogo[1] not in escalados:
                rodada.append({"mandante": jogo[0], "visitante": jogo[1]})
                break

    rodadas_returno = [
        [{"mandante": j["visitante"], "visitante": j["mandante"]} for j in rodada]
        for rodada in rodadas_turno
    ]

    return rodadas_turno + rodadas_returno

# 🔄 Buscar todos usuários com id_time e divisão
try:
    usuarios_res = supabase.table("usuarios").select("id_time", "divisao").execute()
    usuarios = usuarios_res.data or []

    # Agrupar por divisão
    divisao_times = {}
    for u in usuarios:
        id_time = u.get("id_time")
        divisao = u.get("divisao")
        if id_time and divisao:
            divisao_times.setdefault(divisao, []).append(id_time)

    # Loop por divisão
    for divisao, lista_times in divisao_times.items():
        st.markdown(f"## 📅 Divisão {divisao}")

        if len(lista_times) < 2:
            st.warning(f"⚠️ Divisão {divisao} precisa de pelo menos 2 times.")
            continue

        tabela_rodadas = nome_tabela_rodadas(divisao)
        apagar_rodadas_antigas(tabela_rodadas)

        rodadas = gerar_rodadas(lista_times)

        for i, rodada in enumerate(rodadas, start=1):
            supabase.table(tabela_rodadas).insert({
                "numero": i,
                "jogos": rodada,
                "data_criacao": datetime.now().isoformat()
            }).execute()

        st.success(f"✅ {len(rodadas)} rodadas geradas para a divisão {divisao}.")

except Exception as e:
    st.error(f"❌ Erro ao buscar usuários ou gerar rodadas: {e}")
