# 24_Gerar_Grupos_Copa.py
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import itertools

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🎯 Gerar Grupos da Copa", layout="centered")
st.title("🎯 Gerar Grupos Fixos da Copa LigaFut")

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

# 🔄 Buscar todos os times disponíveis
try:
    res = supabase.table("times").select("id, nome").execute()
    todos_times = {t["nome"]: t["id"] for t in res.data}
except Exception as e:
    st.error(f"Erro ao buscar times: {e}")
    st.stop()

grupos_fixos = {
    "Grupo A": ["Bayern", "Borussia Dortmund", "PSG", "Atletico de Madrid"],
    "Grupo B": ["Belgrano", "Ajax", "Liverpool FC", "Manchester United"],
    "Grupo C": ["venezia", "Milan", "Charleroi", "Boca Jrs"],
    "Grupo D": ["Tottenham", "Estudiantes", "Casa Pia", "Lyon"],
    "Grupo E": ["Olympique Marselhe", "Newells", "Real Betis", "VfB Stuttgart"],
    "Grupo F": ["River", "Arsenal", "Inter Miami", "Chelsea FC"],
    "Grupo G": ["Rio Ave", "Napoli", "Leicester", "Wolverhampton"],
    "Grupo H": ["Barcelona", "Wrexham", "Atlanta", "Real Madrid"]
}

# ▶️ Botão para gerar os grupos e confrontos
if st.button("✅ Gerar Grupos Fixos da Copa"):
    # 🧼 Limpa tabelas antigas
    try:
        supabase.table("grupos_copa").delete().neq("grupo", "").execute()
        supabase.table("copa_ligafut").delete().neq("fase", "").execute()
    except Exception as e:
        st.error(f"Erro ao limpar dados antigos: {e}")
        st.stop()

    data_copa = datetime.now().strftime("%Y-%m-%d")

    try:
        for grupo, nomes_times in grupos_fixos.items():
            ids_times = []
            for nome in nomes_times:
                id_time = todos_times.get(nome)
                if id_time:
                    ids_times.append(id_time)
                    # Salva no grupos_copa
                    supabase.table("grupos_copa").insert({
                        "grupo": grupo,
                        "id_time": id_time,
                        "data_criacao": data_copa
                    }).execute()
                else:
                    st.warning(f"⚠️ Time '{nome}' não encontrado no banco.")
            
            # Gera jogos turno e returno
            jogos = []
            for mandante, visitante in itertools.combinations(ids_times, 2):
                jogos.append({
                    "mandante": mandante,
                    "visitante": visitante,
                    "gols_mandante": None,
                    "gols_visitante": None
                })
                jogos.append({
                    "mandante": visitante,
                    "visitante": mandante,
                    "gols_mandante": None,
                    "gols_visitante": None
                })

            # Salva jogos no copa_ligafut
            supabase.table("copa_ligafut").insert({
                "grupo": grupo,
                "fase": "grupos",
                "data_criacao": data_copa,
                "jogos": jogos
            }).execute()

        st.success("✅ Grupos fixos e confrontos criados com sucesso!")

        # 👁️ Visualizar
        st.subheader("📊 Grupos Gerados")
        for grupo, nomes in grupos_fixos.items():
            st.markdown(f"**{grupo}**: {', '.join(nomes)}")

    except Exception as e:
        st.error(f"Erro ao gerar grupos: {e}")
