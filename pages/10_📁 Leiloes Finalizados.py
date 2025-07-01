# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="📁 Leilões - Histórico", layout="wide")
st.title("📁 Histórico de Leilões")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 📥 Buscar todos leilões ordenados pelo fim
res = supabase.table("leiloes").select("*").order("fim", desc=True).execute()
leiloes = res.data if res.data else []

if not leiloes:
    st.info("Nenhum leilão encontrado.")
    st.stop()

# 📦 Exibir todos os leilões em cards
for leilao in leiloes:
    nome_jogador = leilao.get("nome_jogador", "Desconhecido")
    posicao = leilao.get("posicao_jogador", "-")
    overall = leilao.get("overall_jogador", "N/A")
    valor_final = leilao.get("valor_atual", 0)
    nome_time_vencedor = leilao.get("time_vencedor", "-")
    finalizado = leilao.get("finalizado", False)
    fim = leilao.get("fim")

    # ⏰ Formatando data
    data_fim = "-"
    if fim:
        try:
            fim_dt = datetime.fromisoformat(fim)
            data_fim = fim_dt.strftime("%d/%m/%Y %H:%M")
        except:
            pass

    with st.container():
        st.markdown("---")
        st.markdown(f"**🧑‍🎯 Jogador:** `{nome_jogador}` | **Posição:** {posicao} | **⭐ Overall:** {overall}")
        st.markdown(f"**💰 Valor Final:** R$ {valor_final:,.0f}".replace(",", "."))
        st.markdown(f"**🏆 Time Vencedor:** {nome_time_vencedor}")
        st.markdown(f"**📅 Finalizado em:** {data_fim}")
        status = "✅ Finalizado" if finalizado else "⏳ Em andamento"
        st.markdown(f"**📌 Status:** {status}")
