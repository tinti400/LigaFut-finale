# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🔧 Configuração da página
st.set_page_config(page_title="Editar Resultados", page_icon="📋", layout="centered")
st.title("📋 Editar Resultados das Rodadas")

# 🔒 Verifica se o usuário está logado
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado.")
    st.stop()

# 🔽 Seleção da divisão
divisao_selecionada = st.selectbox("Selecione a Divisão", ["Divisão 1", "Divisão 2"])
numero_divisao = divisao_selecionada.split()[-1]
nome_tabela_rodadas = f"rodadas_divisao_{numero_divisao}"

# 🔁 Função para obter os nomes dos times
@st.cache(ttl=120)
def obter_nomes_times():
    res = supabase.table("times").select("id", "nome").execute()
    return {t["id"]: t["nome"] for t in res.data}

# 📅 Função para buscar rodadas
@st.cache(ttl=60)
def buscar_rodadas():
    return supabase.table(nome_tabela_rodadas).select("*").order("numero").execute().data

# 🔄 Carrega rodadas e nomes
rodadas_existentes = buscar_rodadas()
mapa_nomes = obter_nomes_times()

# 🎯 Edição rodada a rodada
if rodadas_existentes:
    st.subheader("📝 Escolha a Rodada para Editar")
    rodada_numeros = [r["numero"] for r in rodadas_existentes]
    rodada_escolhida = st.selectbox("Rodada", rodada_numeros)
    rodada = next(r for r in rodadas_existentes if r["numero"] == rodada_escolhida)

    for jogo in rodada["jogos"]:
        mandante_id = jogo.get("mandante")
        visitante_id = jogo.get("visitante")
        gols_mandante = jogo.get("gols_mandante") or 0
        gols_visitante = jogo.get("gols_visitante") or 0

        nome_mandante = mapa_nomes.get(mandante_id, "FOLGA" if mandante_id == "FOLGA" else "?")
        nome_visitante = mapa_nomes.get(visitante_id, "FOLGA" if visitante_id == "FOLGA" else "?")

        with st.container():
            st.markdown(f"### ⚔️ {nome_mandante} vs {nome_visitante}")

            if "FOLGA" in [mandante_id, visitante_id]:
                st.info("🚫 Este time folgou nesta rodada.")
                continue

            col1, col2, col3 = st.columns([4, 1, 4])
            with col1:
                novo_gm = st.number_input("Gols Mandante", min_value=0, value=gols_mandante, key=f"gm_{mandante_id}_{visitante_id}")
            with col2:
                st.markdown("**x**")
            with col3:
                novo_gv = st.number_input("Gols Visitante", min_value=0, value=gols_visitante, key=f"gv_{mandante_id}_{visitante_id}")

            if st.button("💾 Salvar resultado", key=f"salvar_{mandante_id}_{visitante_id}"):
                novos_jogos = []
                for j in rodada["jogos"]:
                    if j["mandante"] == mandante_id and j["visitante"] == visitante_id:
                        j["gols_mandante"] = novo_gm
                        j["gols_visitante"] = novo_gv
                    novos_jogos.append(j)

                supabase.table(nome_tabela_rodadas).update({"jogos": novos_jogos}).eq("numero", rodada_escolhida).execute()
                st.success(f"✅ Resultado salvo: {nome_mandante} {novo_gm} x {novo_gv} {nome_visitante}")
                st.rerun()
else:
    st.info("⚠️ Nenhuma rodada encontrada para esta divisão.")
