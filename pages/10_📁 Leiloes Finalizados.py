# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="📁 Leilões Finalizados", layout="wide")
st.title("📁 Leilões Finalizados")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 📥 Buscar leilões finalizados
res = supabase.table("leiloes").select("*").eq("finalizado", True).order("fim", desc=True).execute()
leiloes_finalizados = res.data if res.data else []

if not leiloes_finalizados:
    st.info("Nenhum leilão finalizado encontrado.")
    st.stop()

# 📝 Exibir leilões
for leilao in leiloes_finalizados:
    nome_jogador = leilao.get("nome_jogador", "Desconhecido")
    posicao = leilao.get("posicao_jogador", "-")
    overall = leilao.get("overall_jogador", "N/A")
    valor_final = leilao.get("valor_atual", 0)
    nome_time_vencedor = leilao.get("time_vencedor", "-")
    fim = leilao.get("fim")

    st.markdown("---")
    st.markdown(f"**🧑‍🎯 Jogador:** {nome_jogador} ({posicao}) - ⭐ {overall}")
    st.markdown(f"**💰 Valor Final:** R$ {valor_final:,.0f}".replace(",", "."))
    st.markdown(f"**🏆 Time Vencedor:** {nome_time_vencedor}")
    if fim:
        fim_dt = datetime.fromisoformat(fim)
        st.markdown(f"**📅 Finalizado em:** {fim_dt.strftime('%d/%m/%Y %H:%M')}")
