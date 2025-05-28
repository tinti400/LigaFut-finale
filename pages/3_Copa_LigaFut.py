# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import random
from datetime import datetime

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🏆 Copa LigaFut", layout="centered")
st.title("🏆 Copa LigaFut - Mata-mata")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 📥 Buscar todos os times
res_times = supabase.table("times").select("id, nome").execute()
times = res_times.data or []
times = sorted(times, key=lambda x: x["nome"])

# 🎯 Selecionar manualmente os times para a Copa
st.subheader("📋 Selecione os times participantes da Copa")
opcoes = [f"{t['nome']} — {t['id']}" for t in times]
selecionados = st.multiselect("Escolha exatamente 16 times:", options=opcoes)

if st.button("⚽ Gerar Copa"):
    if len(selecionados) != 16:
        st.error("❌ Você deve selecionar exatamente 16 times para o sorteio.")
        st.stop()

    # 🔄 Embaralhar times e gerar confrontos
    try:
        time_ids = [t.split(" — ")[1] for t in selecionados]
        random.shuffle(time_ids)
        confrontos = []
        for i in range(0, len(time_ids), 2):
            mandante = time_ids[i]
            visitante = time_ids[i + 1]
            confrontos.append({
                "mandante": mandante,
                "visitante": visitante,
                "gols_mandante": None,
                "gols_visitante": None
            })

        # 📤 Inserir confrontos na Supabase
        data = {
            "jogos": confrontos,
            "fase": "oitavas",
            "data_criacao": datetime.now().isoformat()
        }
        supabase.table("copa_ligafut").insert(data).execute()
        st.success("✅ Copa criada com sucesso!")
        st.json(confrontos)

    except Exception as e:
        st.error(f"Erro ao gerar a copa: {e}")

# 📋 Mostrar última copa criada
st.markdown("---")
st.subheader("📅 Últimos Confrontos Gerados")

try:
    res = supabase.table("copa_ligafut").select("*").order("data_criacao", desc=True).limit(1).execute()
    ultima_copa = res.data[0] if res.data else None

    if ultima_copa and "jogos" in ultima_copa:
        jogos = ultima_copa["jogos"]
        # Criar mapa de IDs -> nomes
        mapa = {t["id"]: t["nome"] for t in times}

        for jogo in jogos:
            if isinstance(jogo, dict) and "mandante" in jogo and "visitante" in jogo:
                nome_mandante = mapa.get(jogo["mandante"], "Desconhecido")
                nome_visitante = mapa.get(jogo["visitante"], "Desconhecido")
                st.markdown(f"🔷 **{nome_mandante}** x **{nome_visitante}**")
            else:
                st.warning("⚠️ Jogo inválido ou dados ausentes.")
    else:
        st.info("Nenhuma copa encontrada.")
except Exception as e:
    st.error(f"Erro ao buscar confrontos: {e}")


