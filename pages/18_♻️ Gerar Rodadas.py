## -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random
from itertools import combinations

st.set_page_config(page_title="♻️ Gerar Rodadas Todas Temporadas", layout="wide")
st.title("♻️ Gerar Rodadas - Todas Temporadas")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🧠 Nome da tabela de rodadas por temporada e divisão
def nome_tabela(temporada, divisao):
    return f"rodadas_temporada_{temporada}_divisao_{divisao}"

# 🧹 Apagar rodadas antigas
def apagar_rodadas(tabela):
    try:
        supabase.table(tabela).delete().execute()
        st.info(f"🧹 Rodadas antigas apagadas da tabela `{tabela}`.")
    except Exception as e:
        st.error(f"❌ Erro ao apagar rodadas da tabela {tabela}: {e}")

# ⚽ Geração de rodadas com turno e returno
def gerar_rodadas(times):
    random.shuffle(times)
    jogos_turno = list(combinations(times, 2))
    random.shuffle(jogos_turno)

    rodadas_turno = [[] for _ in range(len(times) - 1)]

    for jogo in jogos_turno:
        for rodada in rodadas_turno:
            times_na_rodada = [j["mandante"] for j in rodada] + [j["visitante"] for j in rodada]
            if jogo[0] not in times_na_rodada and jogo[1] not in times_na_rodada:
                rodada.append({"mandante": jogo[0], "visitante": jogo[1]})
                break

    rodadas_returno = [
        [{"mandante": j["visitante"], "visitante": j["mandante"]} for j in rodada]
        for rodada in rodadas_turno
    ]

    return rodadas_turno + rodadas_returno

# 🔍 Buscar times da tabela usuarios
try:
    res_usuarios = supabase.table("usuarios").select("id_time, nome_time, divisao, temporada").execute()
    if not res_usuarios.data:
        st.warning("⚠️ Nenhum time encontrado na tabela 'usuarios'.")
        st.stop()

    # Agrupar times por (temporada, divisão)
    grupos = {}
    for user in res_usuarios.data:
        temporada = user.get("temporada")
        divisao = user.get("divisao")
        id_time = user.get("id_time")
        if temporada and divisao and id_time:
            chave = (temporada, divisao)
            grupos.setdefault(chave, []).append(id_time)

    # 🔄 Gerar rodadas por grupo
    for (temporada, divisao), lista_times in sorted(grupos.items()):
        st.markdown(f"### 📅 Temporada {temporada} | Divisão {divisao}")
        if len(lista_times) < 2:
            st.warning(f"⚠️ Poucos times na divisão {divisao}, temporada {temporada}.")
            continue

        tabela = nome_tabela(temporada, divisao)
        apagar_rodadas(tabela)
        rodadas = gerar_rodadas(lista_times)

        for i, rodada in enumerate(rodadas, start=1):
            dados = {
                "numero": i,
                "jogos": rodada,
                "data_criacao": datetime.now().isoformat()
            }
            supabase.table(tabela).insert(dados).execute()

        st.success(f"✅ {len(rodadas)} rodadas geradas na tabela `{tabela}`.")

except Exception as e:
    st.error(f"❌ Erro ao buscar usuários ou gerar rodadas: {e}")
