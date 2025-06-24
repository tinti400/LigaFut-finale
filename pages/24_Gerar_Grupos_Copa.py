# 24_Gerar_Grupos_Copa.py
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random
import itertools

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🎯 Gerar Grupos da Copa", layout="centered")
st.title("🎯 Gerar Grupos da Copa LigaFut")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 👑 Verifica admin
email_usuario = st.session_state.get("usuario", "")
admin_check = supabase.table("admins").select("email").eq("email", email_usuario).execute()
if not admin_check.data:
    st.warning("🔒 Acesso permitido apenas para administradores.")
    st.stop()

# 🔄 Buscar times
times_data = supabase.table("times").select("id, nome").execute().data
opcoes = {t["nome"]: t["id"] for t in times_data}
selecionados = st.multiselect("📌 Escolha os times participantes da Copa:", list(opcoes.keys()))

if st.button("⚙️ Gerar Grupos da Copa"):
    if len(selecionados) != 32:
        st.warning("🚨 É necessário selecionar exatamente 32 times para o formato Copa do Mundo.")
        st.stop()

    # 🔄 Embaralhar e organizar os grupos
    ids_times = [opcoes[nome] for nome in selecionados]
    random.shuffle(ids_times)

    grupos = {f"Grupo {chr(65+i)}": ids_times[i*4:(i+1)*4] for i in range(8)}
    data_copa = datetime.now().strftime("%Y-%m-%d")

    try:
        supabase.table("grupos_copa").delete().neq("grupo", "").execute()

        for grupo_nome, times in grupos.items():
            for id_time in times:
                supabase.table("grupos_copa").insert({
                    "grupo": grupo_nome,
                    "id_time": id_time,
                    "data_criacao": data_copa
                }).execute()
    except Exception as e:
        st.error(f"Erro ao salvar grupos: {e}")
        st.stop()

    # 🏆 Gerar confrontos (turno e returno)
    try:
        supabase.table("copa_ligafut").delete().eq("fase", "grupos").eq("data_criacao", data_copa).execute()

        for grupo_nome, times in grupos.items():
            jogos = []
            for mandante, visitante in itertools.combinations(times, 2):
                # Turno
                jogos.append({
                    "mandante": mandante,
                    "visitante": visitante,
                    "gols_mandante": None,
                    "gols_visitante": None
                })
                # Returno
                jogos.append({
                    "mandante": visitante,
                    "visitante": mandante,
                    "gols_mandante": None,
                    "gols_visitante": None
                })

            supabase.table("copa_ligafut").insert({
                "grupo": grupo_nome,
                "fase": "grupos",
                "data_criacao": data_copa,
                "jogos": jogos
            }).execute()
        st.success("✅ Grupos e confrontos (turno e returno) gerados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar confrontos: {e}")
        st.stop()

    # 👁️ Visualização
    st.subheader("📊 Grupos Gerados")
    for grupo, lista in grupos.items():
        nomes = [nome for nome, id_ in opcoes.items() if id_ in lista]
        st.markdown(f"**{grupo}**: {', '.join(nomes)}")
