# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import itertools
import random

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Gerar Rodadas", page_icon="⚙️", layout="centered")
st.title("⚙️ Gerar Rodadas da Temporada")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 👑 Verifica se é admin
email_usuario = st.session_state.get("usuario", "")
try:
    admin_ref = supabase.table("admins").select("email").eq("email", email_usuario).execute()
    eh_admin = len(admin_ref.data) > 0
    if not eh_admin:
        st.warning("🔒 Acesso permitido apenas para administradores.")
        st.stop()
except Exception as e:
    st.error(f"Erro ao verificar administrador: {e}")
    st.stop()

# 🔽 Seleção da divisão e temporada
col1, col2 = st.columns(2)
opcao_divisao = col1.selectbox("Selecione a Divisão", ["Divisão 1", "Divisão 2", "Divisão 3"])
opcao_temporada = col2.selectbox("Selecione a Temporada", ["Temporada 1", "Temporada 2", "Temporada 3"])

numero_divisao = opcao_divisao.split()[-1]
numero_temporada = opcao_temporada.split()[-1]
tabela_rodadas = f"rodadas_divisao_{numero_divisao}_temp{numero_temporada}"

# 📅 Buscar times pela divisão
try:
    usuarios = supabase.table("usuarios").select("time_id").eq("Divisão", opcao_divisao).execute().data
    time_ids = list({u["time_id"] for u in usuarios if u.get("time_id")})
except Exception as e:
    st.error(f"Erro ao buscar times: {e}")
    st.stop()

# 🔘 Botão para gerar rodadas
if st.button(f"⚙️ Gerar Rodadas da {opcao_divisao} - {opcao_temporada}"):
    if len(time_ids) < 2:
        st.warning("🚨 É necessário no mínimo 2 times para gerar rodadas.")
        st.stop()

    # 🔄 Apagar rodadas anteriores
    try:
        supabase.table(tabela_rodadas).delete().neq("numero", -1).execute()
    except Exception as e:
        st.error(f"Erro ao apagar rodadas antigas: {e}")
        st.stop()

    # ⚽ Gerar confrontos com turno e returno organizados
    confrontos = list(itertools.combinations(time_ids, 2))

    def montar_rodadas(jogos):
        max_por_rodada = len(time_ids) // 2
        rodadas = []
        todos_jogos = jogos[:]

        while todos_jogos:
            rodada = []
            usados = set()
            for j in todos_jogos[:]:
                if j["mandante"] not in usados and j["visitante"] not in usados:
                    rodada.append(j)
                    usados.update([j["mandante"], j["visitante"]])
                    todos_jogos.remove(j)
                    if len(rodada) == max_por_rodada:
                        break
            rodadas.append(rodada)
        return rodadas

    # Turno (mando normal)
    jogos_ida = [{"mandante": a, "visitante": b, "gols_mandante": None, "gols_visitante": None} for a, b in confrontos]
    rodadas_ida = montar_rodadas(jogos_ida)

    # Returno (mando invertido)
    jogos_volta = [{"mandante": b, "visitante": a, "gols_mandante": None, "gols_visitante": None} for a, b in confrontos]
    rodadas_volta = montar_rodadas(jogos_volta)

    # Junta mantendo a ordem correta: turno → returno
    rodadas = rodadas_ida + rodadas_volta

    # 💾 Salvar rodadas
    try:
        for i, jogos in enumerate(rodadas, 1):
            supabase.table(tabela_rodadas).insert({"numero": i, "jogos": jogos}).execute()
        st.success(f"✅ {len(rodadas)} rodadas geradas com sucesso para {opcao_divisao} - {opcao_temporada}!")
    except Exception as e:
        st.error(f"Erro ao salvar rodadas: {e}")

