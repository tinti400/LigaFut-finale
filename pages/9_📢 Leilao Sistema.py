# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao

st.set_page_config(page_title="Leilão - LigaFut", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time_usuario = st.session_state["id_time"]
nome_time_usuario = st.session_state.get("nome_time", "")

# 🔍 Buscar leilão ativo
res = supabase.table("leiloes").select("*").eq("ativo", True).eq("finalizado", False).limit(1).execute()
if not res.data:
    st.warning("⚠️ Nenhum leilão ativo no momento.")
    st.stop()

leilao = res.data[0]
id_leilao = leilao["id"]
nome_jogador = leilao["nome_jogador"]
posicao_jogador = leilao["posicao_jogador"]
overall_jogador = leilao["overall_jogador"]
valor_atual = leilao["valor_atual"]
incremento_minimo = leilao["incremento_minimo"]
id_time_vencedor = leilao.get("id_time_vencedor")
imagem_url = leilao.get("imagem_url", "")
origem = leilao.get("origem", "")
nacionalidade = leilao.get("nacionalidade", "")

# ⏱️ Cronômetro
fim = datetime.fromisoformat(leilao["fim"])
restante = (fim - datetime.utcnow()).total_seconds()

if restante <= 0:
    if not leilao["finalizado"] and id_time_vencedor:
        # ✅ Inserir no elenco com dados completos
        jogador = {
            "nome": nome_jogador,
            "posicao": posicao_jogador,
            "overall": overall_jogador,
            "valor": valor_atual,
            "id_time": id_time_vencedor,
            "origem": origem,
            "nacionalidade": nacionalidade,
            "imagem_url": imagem_url
        }
        supabase.table("elenco").insert(jogador).execute()

        # 💰 Atualiza saldo
        saldo_atual = supabase.table("times").select("saldo").eq("id", id_time_vencedor).execute().data[0]["saldo"]
        novo_saldo = saldo_atual - valor_atual
        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time_vencedor).execute()

        # 💾 Registrar movimentação
        registrar_movimentacao(
            id_time=id_time_vencedor,
            jogador=nome_jogador,
            tipo="leilao",
            categoria="compra",
            valor=valor_atual,
            origem=origem
        )

    # 🔚 Finaliza o leilão
    supabase.table("leiloes").update({"ativo": False, "finalizado": True}).eq("id", id_leilao).execute()
    st.info("⏱️ Leilão finalizado automaticamente.")
    st.stop()

# 📄 Exibir informações
st.title("📢 Leilão em Andamento")
st.markdown(f"**Jogador:** {nome_jogador}")
st.markdown(f"**Posição:** {posicao_jogador}")
st.markdown(f"**Overall:** {overall_jogador}")
st.markdown(f"**Origem:** {origem}")
st.markdown(f"**Nacionalidade:** {nacionalidade}")
st.markdown(f"**Valor Atual:** R$ {valor_atual:,.0f}".replace(",", "."))

if imagem_url:
    st.image(imagem_url, width=180)

# 💸 Lance
novo_lance = st.number_input("💰 Seu lance (mínimo R$ +100 mil)", min_value=valor_atual + 100_000, step=100_000)

if st.button("💥 Dar Lance"):
    # Atualiza leilão
    supabase.table("leiloes").update({
        "valor_atual": novo_lance,
        "id_time_vencedor": id_time_usuario,
        "fim": (datetime.utcnow().timestamp() + 15)
    }).eq("id", id_leilao).execute()
    st.success("✅ Lance registrado com sucesso!")
    st.rerun()

# ⏳ Tempo restante
st.info(f"⏳ Tempo restante: {int(restante)} segundos")

