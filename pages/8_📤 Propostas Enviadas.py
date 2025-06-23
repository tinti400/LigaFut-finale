# 8_📤 Propostas Enviadas.py
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import verificar_sessao
from datetime import datetime

st.set_page_config(page_title="📤 Propostas Enviadas", layout="wide")
verificar_sessao()

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.markdown(f"<h3>📤 Propostas Enviadas - {nome_time}</h3><hr>", unsafe_allow_html=True)

# 🔄 Buscar propostas enviadas
try:
    res = supabase.table("propostas").select("*").eq("id_time_origem", id_time).order("data", desc=True).execute()
    propostas = res.data if res.data else []
except Exception as e:
    st.error(f"Erro ao buscar propostas enviadas: {e}")
    st.stop()

if not propostas:
    st.info("📭 Nenhuma proposta enviada até o momento.")
else:
    for proposta in propostas:
        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([1, 3])

            with col1:
                imagem = proposta.get("imagem_url") or "https://cdn-icons-png.flaticon.com/512/147/147144.png"
                st.image(imagem, width=80)

            with col2:
                st.markdown(f"### {proposta.get('jogador_nome', 'Desconhecido')} ({proposta.get('jogador_posicao', '')})")
                st.write(f"🌍 **Nacionalidade:** {proposta.get('nacionalidade', 'Desconhecida')}")
                st.write(f"📌 **Posição:** {proposta.get('jogador_posicao', '---')}")
                st.write(f"⭐ **Overall:** {proposta.get('jogador_overall', '-')}")
                st.write(f"💰 **Valor do Jogador:** R$ {proposta.get('jogador_valor', 0):,.0f}".replace(",", ".")}")
                st.write(f"🏟️ **Clube Alvo:** {proposta.get('nome_time_destino', 'Desconhecido')}")
                st.write(f"📦 **Valor Oferecido:** R$ {proposta.get('valor_oferecido', 0):,.0f}".replace(",", "."))                
                st.write(f"📅 **Data da Proposta:** {proposta.get('data', '')[:10]}")
                st.write(f"📌 **Status:** `{proposta.get('status', 'pendente').capitalize()}`")

            jogadores_oferecidos = proposta.get("jogadores_oferecidos", [])
            if jogadores_oferecidos:
                st.markdown("**🔁 Jogadores Oferecidos em Troca:**")
                for j in jogadores_oferecidos:
                    st.write(f"- {j['nome']} (OVR {j['overall']}) - {j['posicao']}")


