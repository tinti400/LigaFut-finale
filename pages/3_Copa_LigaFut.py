
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
        supabase.table("copa_ligafut").delete().neq("fase", "").execute()

        random.shuffle(time_ids)

        # Fase Preliminar se não for número ideal
        rodadas = []
        fase_atual = 1

        if len(time_ids) > 16:
            # 6 times sorteados para a preliminar
            preliminar = time_ids[:6]
            restantes = time_ids[6:]
            jogos_preliminar = []
            for i in range(0, 6, 2):
                jogos_preliminar.append({
                    "mandante": preliminar[i],
                    "visitante": preliminar[i+1],
                    "gols_mandante": None,
                    "gols_visitante": None
                })
            supabase.table("copa_ligafut").insert({
                "fase": "Preliminar",
                "numero": fase_atual,
                "jogos": jogos_preliminar
            }).execute()
            fase_atual += 1
        else:
            restantes = time_ids[:]

        # Oitavas, Quartas, Semi e Final (será preenchido manualmente após resultados)
        st.success("✅ Copa LigaFut criada com sucesso com fase preliminar!")
        st.info("Acompanhe os resultados e avance manualmente para as próximas fases.")

    except Exception as e:
        st.error(f"Erro ao gerar a copa: {e}")
