# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
from utils import registrar_movimentacao

st.set_page_config(page_title="Leilões Ativos - LigaFut", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

usuario_id = st.session_state["usuario_id"]
id_time_usuario = st.session_state["id_time"]
nome_time_usuario = st.session_state.get("nome_time", "")

# 🔒 Verifica restrição de leilão
res_restricoes = supabase.table("times").select("restricoes").eq("id", id_time_usuario).execute()
restricoes = res_restricoes.data[0].get("restricoes", {}) if res_restricoes.data else {}
if restricoes.get("leilao", False):
    st.error("🚫 Seu time está proibido de participar de leilões.")
    st.stop()

# 🔄 Buscar todos os leilões ativos
res = supabase.table("leiloes").select("*").eq("ativo", True).eq("finalizado", False).order("fim").execute()
leiloes_ativos = res.data

if not leiloes_ativos:
    st.info("⚠️ Nenhum leilão ativo no momento.")
    st.stop()

st.title("🎯 Leilões Ativos")

for leilao in leiloes_ativos:
    st.markdown("---")
    col1, col2 = st.columns([1, 2])

    with col1:
        imagem_url = leilao.get("imagem_url", "")
        if imagem_url and imagem_url.startswith("http"):
            st.image(imagem_url, width=150)
        else:
            st.image("https://cdn-icons-png.flaticon.com/512/147/147144.png", width=150)

    with col2:
        fim_dt = datetime.fromisoformat(leilao["fim"])
        tempo_restante = max(0, int((fim_dt - datetime.utcnow()).total_seconds()))
        minutos, segundos = divmod(tempo_restante, 60)

        st.markdown(f"### {leilao['nome_jogador']}")
        st.markdown(f"**Posição:** {leilao['posicao_jogador']} &nbsp;&nbsp; **Overall:** {leilao['overall_jogador']}")
        st.markdown(f"**Origem:** {leilao.get('origem', 'Desconhecida')} &nbsp;&nbsp; **Nacionalidade:** {leilao.get('nacionalidade', 'Desconhecida')}")
        st.markdown(f"**⏳ Tempo restante:** {minutos:02d}:{segundos:02d}")
        st.markdown(f"**💰 Preço atual:** R$ {leilao['valor_atual']:,}".replace(",", "."))

        if leilao.get("id_time_atual"):
            nome_time = supabase.table("times").select("nome").eq("id", leilao["id_time_atual"]).execute().data[0]["nome"]
            st.markdown(f"**🏷️ Último Lance:** {nome_time}")

        if tempo_restante == 0:
            if not leilao.get("finalizado") and not leilao.get("validado"):
                supabase.table("leiloes").update({
                    "ativo": False,
                    "aguardando_validacao": True
                }).eq("id", leilao["id"]).execute()
                st.success("✅ Leilão finalizado! Aguardando validação do administrador.")
            else:
                st.info("⏳ Leilão já finalizado.")
            continue

        st.markdown("#### 💥 Enviar Lance")
        botoes = [(leilao["valor_atual"] + leilao["incremento_minimo"] * i) for i in range(1, 6)]

        if len(botoes) >= 1:
            colunas = st.columns(len(botoes))
            for i, valor_lance in enumerate(botoes):
                with colunas[i]:
                    if st.button(f"➕ R$ {valor_lance:,.0f}".replace(",", "."), key=f"lance_{leilao['id']}_{i}"):
                        saldo_ref = supabase.table("times").select("saldo").eq("id", id_time_usuario).execute()
                        saldo = saldo_ref.data[0]["saldo"]

                        if valor_lance > saldo:
                            st.error("❌ Saldo insuficiente.")
                        else:
                            agora = datetime.utcnow()
                            novo_fim = fim_dt
                            if (fim_dt - agora).total_seconds() <= 15:
                                novo_fim = agora + timedelta(seconds=15)

                            supabase.table("leiloes").update({
                                "valor_atual": valor_lance,
                                "id_time_atual": id_time_usuario,
                                "time_vencedor": nome_time_usuario,
                                "fim": novo_fim.isoformat()
                            }).eq("id", leilao["id"]).execute()

                            st.success("✅ Lance enviado!")
                            st.experimental_rerun()

st.markdown("---")
if st.button("🔄 Atualizar Leilões"):
    st.experimental_rerun()
