import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="💰 Validar Saldos - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica se é admin
email_usuario = st.session_state.get("usuario", "")
admin_ref = supabase.table("admins").select("email").eq("email", email_usuario).execute()
eh_admin = admin_ref.data

if not eh_admin:
    st.warning("🔒 Acesso restrito a administradores.")
    st.stop()

st.title("💰 Validação de Saldos por Rodada")

id_liga = "VUnsRMAPOc9Sj9n5BenE"
colecao_rodadas = f"ligas/{id_liga}/rodadas_divisao_1"

def atualizar_saldo(id_time, valor):
    time_ref = supabase.table("times").select("saldo").eq("id", id_time).execute()
    saldo_atual = time_ref.data[0]["saldo"] if time_ref.data else 0
    supabase.table("times").update({"saldo": saldo_atual + valor}).eq("id", id_time).execute()

if st.button("💰 Validar saldos das rodadas"):
    rodadas = supabase.table(colecao_rodadas).select("*").execute().data
    jogos_processados = 0

    for rodada in rodadas:
        dados = rodada.get("jogos", [])
        for jogo in dados:
            mandante = jogo.get("mandante")
            visitante = jogo.get("visitante")
            gols_mandante = jogo.get("gols_mandante")
            gols_visitante = jogo.get("gols_visitante")

            # Pula jogos sem placar
            if gols_mandante is None or gols_visitante is None:
                continue

            saldo_mandante = 0
            saldo_visitante = 0

            # Vitória
            if gols_mandante > gols_visitante:
                saldo_mandante += 2_000_000
            elif gols_visitante > gols_mandante:
                saldo_visitante += 2_000_000

            # Gols feitos / sofridos
            saldo_mandante += (gols_mandante * 50_000) - (gols_visitante * 5_000)
            saldo_visitante += (gols_visitante * 50_000) - (gols_mandante * 5_000)

            # Atualiza Supabase
            atualizar_saldo(mandante, saldo_mandante)
            atualizar_saldo(visitante, saldo_visitante)

            jogos_processados += 1

    st.success(f"✅ Saldos atualizados com sucesso para {jogos_processados} jogos!")
