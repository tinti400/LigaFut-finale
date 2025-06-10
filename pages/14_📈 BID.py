# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="📈 BID - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

st.markdown("<h1 style='text-align: center;'>📈 BID - Boletim Informativo Diário</h1><hr>", unsafe_allow_html=True)

# 🔄 Carrega todas movimentações
try:
    mov_ref = supabase.table("movimentacoes").select("*").order("data_hora", desc=True).execute()
    todas_movs = mov_ref.data
except Exception as e:
    st.error(f"Erro ao buscar movimentações: {e}")
    todas_movs = []

# 📰 Exibe BID
if not todas_movs:
    st.info("Nenhuma movimentação registrada ainda.")
else:
    for mov in todas_movs:
        tipo = mov.get("tipo", "outros").upper()
        categoria = mov.get("categoria", "").capitalize()
        jogador = mov.get("jogador", "Jogador desconhecido")
        valor = mov.get("valor", 0)
        origem = mov.get("origem", "Desconhecido")
        destino = mov.get("destino", "Desconhecido")
        data = mov.get("data_hora", "")

        # Converte data para formato legível
        try:
            data_formatada = datetime.fromisoformat(data).strftime("%d/%m %H:%M")
        except:
            data_formatada = ""

        st.markdown(f"""
            <div style='padding:10px; border-radius:8px; margin-bottom:10px; background-color:#f0f2f6;'>
                <b>{categoria} - {tipo}</b><br>
                <small>{data_formatada}</small><br>
                <b>{jogador}</b><br>
                {origem} ⟶ {destino}<br>
                💰 R$ {valor:,.0f}
            </div>
        """, unsafe_allow_html=True)



