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

# 📋 Grupos fixos conforme as imagens (ordem exata)
grupos_fixos = {
    "Grupo A": ["Bayern", "Borussia", "PSG", "Atletico de Madrid"],
    "Grupo B": ["Belgrano", "Ajax", "Liverpool", "Manchester United"],
    "Grupo C": ["venezia", "Milan", "Charleroi", "Boca Jrs"],
    "Grupo D": ["tottenham", "Estudiantes", "Casa Pia", "Lyon"],
    "Grupo E": ["Olympique Marselhe", "Newells", "Real Betis", "Stuttgart"],
    "Grupo F": ["River", "Arsenal", "Inter Miami", "Chelsea"],
    "Grupo G": ["Rio Ave", "Napoli", "Leicester", "Wolverhampton"],
    "Grupo H": ["Barcelona", "Wrexham", "Atlanta", "Real Madrid"]
}

# 🎯 Interface para selecionar os times participantes (todos marcados)
st.subheader("📌 Selecione os times participantes da Copa")
nomes_disponiveis = list(todos_times.keys())
selecionados = st.multiselect(
    "Desmarque os times que NÃO irão participar:",
    nomes_disponiveis,
    default=nomes_disponiveis
)

# ▶️ Botão para gerar grupos fixos com os selecionados
if st.button("✅ Gerar Grupos Fixos da Copa"):
    if len(selecionados) != 32:
        st.warning("🚨 Você precisa deixar exatamente 32 times selecionados.")
        st.stop()

    # 🔁 Valida se todos os times dos grupos fixos estão entre os selecionados
    nomes_necessarios = [nome for grupo in grupos_fixos.values() for nome in grupo]
    faltando = [nome for nome in nomes_necessarios if nome not in selecionados]
    if faltando:
        st.error(f"❌ Os seguintes times dos grupos fixos não estão entre os selecionados: {', '.join(faltando)}")
        st.stop()

    try:
        # 🧹 Limpa dados antigos
        supabase.table("grupos_copa").delete().neq("grupo", "").execute()
        supabase.table("copa_ligafut").delete().neq("fase", "").execute()
    except Exception as e:
        st.error(f"Erro ao limpar dados antigos: {e}")
        st.stop()

    data_copa = datetime.now().strftime("%Y-%m-%d")

    try:
        # 💾 Salva os grupos fixos e gera os jogos
        for grupo_nome, nomes_times in grupos_fixos.items():
            ids = []
            for nome in nomes_times:
                id_time = todos_times.get(nome)
                if not id_time:
                    st.warning(f"⚠️ Time '{nome}' não encontrado.")
                    continue
                ids.append(id_time)
                supabase.table("grupos_copa").insert({
                    "grupo": grupo_nome,
                    "id_time": id_time,
                    "data_criacao": data_copa
                }).execute()

            # ⚽ Jogos (ida e volta)
            jogos = []
            for mandante, visitante in itertools.combinations(ids, 2):
                jogos.append({"mandante": mandante, "visitante": visitante, "gols_mandante": None, "gols_visitante": None})
                jogos.append({"mandante": visitante, "visitante": mandante, "gols_mandante": None, "gols_visitante": None})

            supabase.table("copa_ligafut").insert({
                "grupo": grupo_nome,
                "fase": "grupos",
                "data_criacao": data_copa,
                "jogos": jogos
            }).execute()

        st.success("✅ Grupos e confrontos gerados com sucesso!")
        st.subheader("📊 Grupos Gerados")
        for grupo, nomes in grupos_fixos.items():
            st.markdown(f"**{grupo}**: {', '.join(nomes)}")

    except Exception as e:
        st.error(f"Erro ao salvar grupos: {e}")
