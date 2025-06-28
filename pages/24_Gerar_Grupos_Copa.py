# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import itertools

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🎯 Gerar Grupos da Copa", layout="wide")
st.title("🎯 Definir Grupos da Copa LigaFut Manualmente")

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

# 🔄 Buscar times disponíveis
try:
    res = supabase.table("times").select("id, nome").execute()
    times_disponiveis = sorted(res.data, key=lambda x: x["nome"])
except Exception as e:
    st.error(f"Erro ao buscar times: {e}")
    st.stop()

# 🔄 Criar dicionário nome -> id
nome_para_id = {t["nome"]: t["id"] for t in times_disponiveis}
nomes_times = list(nome_para_id.keys())

# 🧩 Grupos fixos conforme imagens
estrutura_grupos = {
    "Grupo A": ["Bayern", "Borussia", "PSG", "Atletico de Madrid"],
    "Grupo B": ["Belgrano", "Ajax", "Liverpool", "Manchester United"],
    "Grupo C": ["venezia", "Milan", "Charleroi", "Boca Jrs"],
    "Grupo D": ["tottenham", "Estudiantes", "Casa Pia", "Lyon"],
    "Grupo E": ["Olympique Marselhe", "Newells", "Real Betis", "Stuttgart"],
    "Grupo F": ["River", "Arsenal", "Inter Miami", "Chelsea"],
    "Grupo G": ["Rio Ave", "Napoli", "Leicester", "Wolverhampton"],
    "Grupo H": ["Barcelona", "Wrexham", "Atlanta", "Real Madrid"]
}

# 🧠 Interface para selecionar os times corretamente
st.subheader("📝 Selecione os times corretos para cada grupo:")

grupos_selecionados = {}
colunas = st.columns(4)
for i, (grupo, sugestoes) in enumerate(estrutura_grupos.items()):
    with colunas[i % 4]:
        st.markdown(f"**{grupo}**")
        selecionados = []
        for j, sugestao in enumerate(sugestoes):
            escolha = st.selectbox(f"{grupo} - Posição {j+1} ({sugestao})", nomes_times, key=f"{grupo}_{j}")
            selecionados.append(nome_para_id[escolha])
        grupos_selecionados[grupo] = selecionados

# ▶️ Botão para salvar os grupos e gerar confrontos
if st.button("✅ Salvar Grupos e Gerar Confrontos"):
    try:
        # Limpa dados antigos
        supabase.table("grupos_copa").delete().neq("grupo", "").execute()
        supabase.table("copa_ligafut").delete().neq("fase", "").execute()

        data_copa = datetime.now().strftime("%Y-%m-%d")

        # Salvar grupos e jogos
        for grupo, id_times in grupos_selecionados.items():
            for id_time in id_times:
                supabase.table("grupos_copa").insert({
                    "grupo": grupo,
                    "id_time": id_time,
                    "data_criacao": data_copa
                }).execute()

            # Gera jogos do grupo (turno e returno)
            jogos = []
            for mandante, visitante in itertools.combinations(id_times, 2):
                jogos.append({"mandante": mandante, "visitante": visitante, "gols_mandante": None, "gols_visitante": None})
                jogos.append({"mandante": visitante, "visitante": mandante, "gols_mandante": None, "gols_visitante": None})

            supabase.table("copa_ligafut").insert({
                "grupo": grupo,
                "fase": "grupos",
                "data_criacao": data_copa,
                "jogos": jogos
            }).execute()

        st.success("✅ Grupos e confrontos gerados com sucesso!")
        st.subheader("📊 Grupos Gerados")
        for grupo, id_times in grupos_selecionados.items():
            nomes = [nome for nome, id_ in nome_para_id.items() if id_ in id_times]
            st.markdown(f"**{grupo}**: {', '.join(nomes)}")

    except Exception as e:
        st.error(f"❌ Erro ao gerar grupos: {e}")
