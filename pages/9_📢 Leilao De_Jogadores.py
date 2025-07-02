# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
from utils import registrar_movimentacao

st.set_page_config(page_title="Leilões Ativos - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time_usuario = st.session_state["id_time"]
nome_time_usuario = st.session_state.get("nome_time", "")

# 🔒 Verifica restrições do time
restricoes = {}
try:
    res_restricoes = supabase.table("times").select("restricoes").eq("id", id_time_usuario).execute()
    if res_restricoes.data and isinstance(res_restricoes.data[0].get("restricoes"), dict):
        restricoes = res_restricoes.data[0]["restricoes"]
except Exception:
    restricoes = {}

if restricoes.get("leilao", False):
    st.error("🚫 Seu time está proibido de participar de leilões.")
    st.stop()
# 🧨 Leilões Ativos
st.title("📢 Leilões Ativos")

leiloes_ativos = supabase.table("leiloes").select("*").eq("ativo", True).eq("finalizado", False).execute()

if not leiloes_ativos.data:
    st.info("⏳ Nenhum leilão ativo no momento.")
else:
    for leilao in leiloes_ativos.data:
        with st.container():
            col1, col2 = st.columns([1, 3])
            with col1:
                if leilao.get("imagem_url"):
                    st.image(leilao["imagem_url"], width=120)

            with col2:
                st.markdown(f"### {leilao['nome_jogador']}")
                st.markdown(f"**Posição:** {leilao['posicao_jogador']} | **Overall:** {leilao['overall_jogador']}")
                st.markdown(f"**Valor Atual:** R$ {leilao['valor_atual']:,}".replace(",", "."))
                st.markdown(f"**Origem:** {leilao.get('origem', 'Desconhecida')}")
                st.markdown(f"**Nacionalidade:** {leilao.get('nacionalidade', 'Desconhecida')}")
                if leilao.get("link_sofifa"):
                    st.markdown(f"[📄 Ficha Técnica (SoFIFA)]({leilao['link_sofifa']})", unsafe_allow_html=True)

                fim_dt = datetime.fromisoformat(leilao["fim"])
                tempo_restante = fim_dt - datetime.utcnow()

                if tempo_restante.total_seconds() <= 0:
                    st.warning("⏱️ Leilão encerrado. Aguardando validação.")
                    continue
                else:
                    minutos, segundos = divmod(int(tempo_restante.total_seconds()), 60)
                    st.info(f"⏳ Tempo restante: {minutos:02d}:{segundos:02d}")

                valor_minimo = leilao["valor_atual"] + 100_000
                novo_lance = st.number_input(
                    f"💸 Seu lance (mínimo R$ {valor_minimo:,})".replace(",", "."),
                    min_value=valor_minimo,
                    step=100_000,
                    key=f"lance_{leilao['id']}"
                )

                if st.button("🎯 Dar Lance", key=f"lance_btn_{leilao['id']}"):
                    agora = datetime.utcnow()
                    if (fim_dt - agora).total_seconds() <= 15:
                        fim_dt = agora + timedelta(seconds=15)

                    try:
                        update_payload = {
                            "valor_atual": novo_lance,
                            "id_time_atual": id_time_usuario,
                            "fim": fim_dt.isoformat(),
                            "time_vencedor": nome_time_usuario
                        }

                        supabase.table("leiloes").update(update_payload).eq("id", leilao["id"]).execute()

                        st.success("✅ Lance enviado com sucesso!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao atualizar o leilão: {e}")

# 🔁 Atualizar página manualmente
st.markdown("---")
if st.button("🔄 Atualizar Página"):
    st.experimental_rerun()

