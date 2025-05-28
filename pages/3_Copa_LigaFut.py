# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import random
from datetime import datetime
import json

st.set_page_config(page_title="🏆 Copa LigaFut", layout="wide")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# Título
st.markdown("## 🏆 Copa LigaFut - Mata-mata")

# 🔍 Buscar todos os times disponíveis
res = supabase.table("times").select("id, nome").execute()
times = res.data if res.data else []

# 📝 Seleção manual dos times
st.subheader("✅ Selecione os times que participarão da Copa")
times_selecionados = []

cols = st.columns(4)
for idx, time in enumerate(times):
    col = cols[idx % 4]
    if col.checkbox(f"{time['nome']} — ID: {time['id']}", key=f"time_{time['id']}"):
        times_selecionados.append(time)

# Botão para gerar Copa
if len(times_selecionados) % 2 != 0:
    st.warning("⚠️ É necessário selecionar um número **par** de times.")
elif len(times_selecionados) < 2:
    st.info("Selecione pelo menos 2 times.")
else:
    if st.button("⚙️ Gerar Nova Copa LigaFut"):
        try:
            time_ids = [t["id"] for t in times_selecionados]
            nomes_times = {t["id"]: t["nome"] for t in times_selecionados}
            random.shuffle(time_ids)

            confrontos = []
            for i in range(0, len(time_ids), 2):
                mandante_id = time_ids[i]
                visitante_id = time_ids[i+1]
                confrontos.append({
                    "mandante": mandante_id,
                    "visitante": visitante_id,
                    "gols_mandante": None,
                    "gols_visitante": None
                })

            dados = {
                "numero": 1,
                "fase": "oitavas",
                "jogos": json.dumps(confrontos),
                "criado_em": datetime.now().isoformat()
            }

            supabase.table("copa_ligafut").insert(dados).execute()

            st.success("✅ Copa criada com sucesso!")
            st.json(confrontos)

        except Exception as e:
            st.error(f"Erro ao gerar a copa: {e}")




