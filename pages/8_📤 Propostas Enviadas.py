# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import verificar_sessao
from datetime import datetime

st.set_page_config(page_title="📤 Propostas Enviadas", layout="wide")
verificar_sessao()

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🔄 Buscar propostas enviadas
res = supabase.table("propostas").select("*").eq("id_time_origem", id_time).order("data", desc=True).execute()
propostas = res.data if res.data else []

# 🔰 Título
st.markdown(f"""
<h3>📤 Propostas Enviadas - {nome_time}</h3>
""", unsafe_allow_html=True)

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
                st.markdown(f"### {proposta['jogador_nome']} ({proposta['jogador_posicao']})")
                st.write(f"🌍 **Nacionalidade:** {proposta.get('nacionalidade', 'Desconhecida')}")
                st.write(f"📌 **Posição:** {proposta['jogador_posicao']}")
                st.write(f"⭐ **Overall:** {proposta['jogador_overall']}")
                st.write(f"💰 **Valor:** R$ {proposta['jogador_valor']:,.0f}".replace(",", "."))
                st.write(f"🏟️ **Clube Alvo:** {proposta['nome_time_destino']}")
                st.write(f"📦 **Valor Oferecido:** R$ {proposta['valor_oferecido']:,.0f}".replace(",", "."))

                status = proposta.get("status", "pendente")
                status_display = {
                    "pendente": "🟡 Pendente",
                    "aceita": "✅ Aceita",
                    "recusada": "❌ Recusada",
                    "contraproposta": "🔁 Contraproposta"
                }
                st.write(f"📄 **Status:** {status_display.get(status, status.capitalize())}")

                # ⏰ Data
                data_envio = proposta.get("data")
                if data_envio:
                    dt = datetime.fromisoformat(data_envio)
                    st.write(f"🕒 Enviada em: {dt.strftime('%d/%m/%Y %H:%M')}")

            jogadores_oferecidos = proposta.get("jogadores_oferecidos", [])
            if jogadores_oferecidos:
                st.markdown("**🔁 Jogadores Oferecidos em Troca:**")
                for j in jogadores_oferecidos:
                    st.write(f"- {j['nome']} (OVR {j['overall']}) - {j['posicao']}")

