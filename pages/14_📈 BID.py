# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="📋 BID da LigaFut", layout="wide")
st.title("📋 BID da LigaFut")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 🔄 Recupera movimentações
try:
    mov_ref = supabase.table("movimentacoes").select("*").order("data", desc=True).limit(200).execute()
    movimentacoes = mov_ref.data
except Exception as e:
    st.error(f"Erro ao buscar movimentações: {e}")
    movimentacoes = []

# 🔁 Mapeia os IDs dos times para nomes
try:
    times_res = supabase.table("times").select("id", "nome").execute()
    times_map = {t["id"]: t["nome"] for t in times_res.data}
except Exception as e:
    st.error(f"Erro ao buscar nomes dos times: {e}")
    times_map = {}

# 📋 Exibe todas as movimentações com ícone
if not movimentacoes:
    st.info("Nenhuma movimentação registrada ainda.")
else:
    for mov in movimentacoes:
        jogador = mov.get("jogador", "Desconhecido")
        tipo = mov.get("tipo", "N/A").capitalize()
        categoria = mov.get("categoria", "N/A").capitalize()
        valor = mov.get("valor", 0)
        data = mov.get("data", "")
        id_time = mov.get("id_time", "")
        nome_time = times_map.get(id_time, "Desconhecido")
        destino = mov.get("destino", "")
        origem = mov.get("origem", "")

        # Data formatada
        try:
            data_formatada = datetime.fromisoformat(data).strftime('%d/%m/%Y %H:%M')
        except:
            data_formatada = "Data inválida"

        # Valor formatado
        valor_str = f"R$ {abs(valor):,.0f}".replace(",", ".")

        # Determina o ícone
        if categoria.lower() == "leilao":
            icone = "📢"
        elif categoria.lower() == "proposta":
            icone = "📤"
        elif valor >= 0:
            icone = "🟢"
        else:
            icone = "🔴"

        # Exibição formatada
        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([1, 6])
            with col1:
                st.markdown(f"<span style='font-size:28px'>{icone}</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**🕒 {data_formatada}** — **{nome_time}**")
                st.markdown(f"**👤 Jogador:** {jogador}")
                st.markdown(f"**💬 Tipo:** {tipo} — **📂 Categoria:** {categoria}")
                st.markdown(f"**💰 Valor:** {valor_str}")
                if origem:
                    st.markdown(f"**↩️ Origem:** {origem}")
                if destino:
                    st.markdown(f"**➡️ Destino:** {destino}")
