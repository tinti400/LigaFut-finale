# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Editar Resultados", page_icon="📋", layout="wide")
st.title("📋 Editar Resultados das Rodadas")

# 🔒 Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 🔽 Selecionar divisão
divisao = st.selectbox("Selecione a divisão", ["Divisão 1", "Divisão 2"])
numero_divisao = divisao.split()[-1]
nome_tabela_rodadas = f"rodadas_divisao_{numero_divisao}"

# 🧠 Buscar nomes dos times
@st.cache(ttl=120)
def obter_nomes_times():
    res = supabase.table("times").select("id", "nome").execute()
    return {t["id"]: t["nome"] for t in res.data}

# 🔍 Buscar rodadas da divisão
@st.cache(ttl=60)
def buscar_rodadas():
    return supabase.table(nome_tabela_rodadas).select("*").order("numero").execute().data

rodadas = buscar_rodadas()
nomes_times = obter_nomes_times()

if not rodadas:
    st.info("⚠️ Nenhuma rodada encontrada para esta divisão.")
else:
    for rodada in rodadas:
        st.markdown(f"## 📆 Rodada {rodada['numero']}")
        novos_jogos = []

        for jogo in rodada.get("jogos", []):
            mandante_id = jogo["mandante"]
            visitante_id = jogo["visitante"]
            gols_mandante = jogo.get("gols_mandante") or 0
            gols_visitante = jogo.get("gols_visitante") or 0

            nome_m = nomes_times.get(mandante_id, "FOLGA" if mandante_id == "FOLGA" else "?")
            nome_v = nomes_times.get(visitante_id, "FOLGA" if visitante_id == "FOLGA" else "?")

            with st.container():
                st.markdown(f"### ⚔️ {nome_m} vs {nome_v}")

                if "FOLGA" in [mandante_id, visitante_id]:
                    st.info("🛌 Este time folgou nesta rodada.")
                    novos_jogos.append(jogo)
                    continue

                col1, col2, col3 = st.columns([4, 1, 4])
                with col1:
                    novo_gm = st.number_input("Gols Mandante", min_value=0, value=gols_mandante, key=f"{rodada['numero']}_{mandante_id}")
                with col2:
                    st.markdown("**x**")
                with col3:
                    novo_gv = st.number_input("Gols Visitante", min_value=0, value=gols_visitante, key=f"{rodada['numero']}_{visitante_id}")

                if st.button("💾 Salvar", key=f"salvar_{rodada['numero']}_{mandante_id}_{visitante_id}"):
                    jogo["gols_mandante"] = novo_gm
                    jogo["gols_visitante"] = novo_gv
                    novos_jogos = rodada["jogos"]  # atualiza apenas um jogo

                    # Atualiza no banco
                    supabase.table(nome_tabela_rodadas).update({
                        "jogos": novos_jogos
                    }).eq("numero", rodada["numero"]).execute()
                    st.success("✅ Resultado salvo!")
                    st.rerun()

        st.divider()

