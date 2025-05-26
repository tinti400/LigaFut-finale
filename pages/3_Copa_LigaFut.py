
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import random

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🏆 Copa LigaFut", page_icon="🏆", layout="centered")
st.title("🏆 Gerar Copa LigaFut (Mata-mata)")

# 🔐 Verifica login e permissão
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

if not eh_admin:
    st.warning("🔒 Apenas administradores podem gerar a Copa.")
    st.stop()

# 📊 Buscar todos os times da Liga (1ª e 2ª divisão)
res = supabase.table("usuarios").select("time_id").execute()
time_ids = list({u["time_id"] for u in res.data if u.get("time_id")})

if len(time_ids) < 2:
    st.warning("⚠️ Mínimo de 2 times para gerar a Copa.")
    st.stop()

# 📊 Gerar confrontos
if st.button("⚙️ Gerar Copa LigaFut"):
    try:
        supabase.table("copa_ligafut").delete().neq("numero", -1).execute()
        random.shuffle(time_ids)

        fase_atual = 1
        numero_fase = 1
        jogos_fase1 = []

        # Fase preliminar se não for múltiplo de 16
        while len(time_ids) % 2 != 0:
            bye_time = time_ids.pop()
            jogos_fase1.append({
                "mandante": bye_time,
                "visitante": "BYE",
                "gols_mandante": None,
                "gols_visitante": None
            })

        # Confrontos diretos
        for i in range(0, len(time_ids), 2):
            jogos_fase1.append({
                "mandante": time_ids[i],
                "visitante": time_ids[i+1],
                "gols_mandante": None,
                "gols_visitante": None
            })

        # Inserir fase 1
        supabase.table("copa_ligafut").insert({
            "numero": numero_fase,
            "fase": "Fase 1",
            "jogos": jogos_fase1
        }).execute()

        st.success("✅ Copa LigaFut gerada com sucesso!")
    except Exception as e:
        st.error(f"Erro ao gerar a copa: {e}")
