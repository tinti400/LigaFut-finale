# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import registrar_movimentacao

st.set_page_config(page_title="Elenco - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or "id_time" not in st.session_state:
    st.warning("⚠️ Você precisa estar logado para acessar esta página.")
    st.stop()

usuario_id = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state.get("nome_time", "")

st.markdown(f"<h2 style='text-align:center;'>👥 Elenco do {nome_time}</h2><hr>", unsafe_allow_html=True)

# 📦 Buscar elenco do time
res = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
jogadores = res.data if res.data else []

if not jogadores:
    st.info("📃 Nenhum jogador encontrado no elenco.")
    st.stop()

# 🧑‍💼 Exibir jogadores com visual estilo planilha moderna
for jogador in jogadores:
    with st.container():
        col1, col2, col3, col4, col5, col6 = st.columns([1, 2.5, 1.5, 1.5, 2, 2])

        with col1:
            if jogador.get("imagem_url"):
                st.markdown(
                    f"""
                    <div style="width:60px;height:60px;border-radius:50%;overflow:hidden;border:2px solid #ddd;">
                        <img src="{jogador['imagem_url']}" width="60" style="object-fit:cover;">
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown("🧍‍♂️")

        with col2:
            st.markdown(f"**{jogador['nome']}**")
            st.markdown(f"{jogador.get('nacionalidade', '🇧🇷')}")

        with col3:
            st.markdown(f"**Posição:** {jogador.get('posicao', '-')}")
        
        with col4:
            st.markdown(f"**Overall:** {jogador.get('overall', 'N/A')}")

        with col5:
            st.markdown("**Valor:** R$ {:,.0f}".format(jogador["valor"]).replace(",", "."))
            st.markdown(f"**Origem:** {jogador.get('origem', 'Desconhecida')}")

        with col6:
            if st.button(f"Vender {jogador['nome']}", key=f"vender_{jogador['id']}"):
                try:
                    # Remove do elenco
                    supabase.table("elenco").delete().eq("id", jogador["id"]).execute()

                    # Insere no mercado
                    supabase.table("mercado_transferencias").insert({
                        "nome": jogador["nome"],
                        "posicao": jogador["posicao"],
                        "overall": jogador["overall"],
                        "valor": jogador["valor"],
                        "id_time": id_time,
                        "time_origem": nome_time,
                        "imagem_url": jogador.get("imagem_url", ""),
                        "nacionalidade": jogador.get("nacionalidade", "Desconhecida"),
                        "origem": jogador.get("origem", "Desconhecida")
                    }).execute()

                    registrar_movimentacao(
                        id_time=id_time,
                        jogador=jogador["nome"],
                        valor=round(jogador["valor"] * 0.7),
                        tipo="mercado",
                        categoria="venda",
                        destino="Mercado"
                    )

                    st.success(f"{jogador['nome']} foi vendido para o mercado com sucesso.")
                    st.experimental_rerun()

                except Exception as e:
                    st.error(f"Erro ao vender jogador: {e}")

st.markdown("<hr>", unsafe_allow_html=True)
st.button("🔄 Atualizar", on_click=st.experimental_rerun)



