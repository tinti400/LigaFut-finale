# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
from utils import registrar_movimentacao

st.set_page_config(page_title="Leilão - LigaFut", layout="wide")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time_usuario = st.session_state["id_time"]
nome_time_usuario = st.session_state.get("nome_time", "")

# 🔒 Verifica restrição de leilão para o time
try:
    res_restricoes = supabase.table("times").select("restricoes").eq("id", id_time_usuario).execute()
    restricoes = res_restricoes.data[0].get("restricoes", {}) if res_restricoes.data else {}

    if restricoes.get("leilao", False):
        st.error("🚫 Seu time está proibido de participar de leilões.")
        st.stop()
except Exception as e:
    st.warning(f"⚠️ Erro ao verificar restrições: {e}")

# 🔍 Buscar leilao ativo
res = supabase.table("leiloes").select("*").eq("ativo", True).eq("finalizado", False).limit(1).execute()
if not res.data:
    st.warning("⚠️ Nenhum leilão ativo no momento.")
    st.stop()

leilao = res.data[0]
fim = leilao.get("fim")
valor_atual = leilao["valor_atual"]
incremento = leilao["incremento_minimo"]
id_time_vencedor = leilao.get("id_time_atual", "")
nome_jogador = leilao.get("nome_jogador", "Desconhecido")
posicao_jogador = leilao.get("posicao_jogador", "-")
overall_jogador = leilao.get("overall_jogador", "N/A")
imagem_url = leilao.get("imagem_url", "")
origem = leilao.get("origem", "Desconhecida")
nacionalidade = leilao.get("nacionalidade", "Desconhecida")

# ⏱️ Cronômetro
fim_dt = datetime.fromisoformat(fim)
tempo_restante = max(0, int((fim_dt - datetime.utcnow()).total_seconds()))
minutos, segundos = divmod(tempo_restante, 60)

# 🖼️ Exibir imagem e info do jogador
if imagem_url:
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    st.image(imagem_url, width=220, caption=nome_jogador)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(f"<h2 style='text-align:center'>⏳ Tempo restante: {minutos:02d}:{segundos:02d}</h2>", unsafe_allow_html=True)
st.markdown("---")

col1, col2, col3, col4 = st.columns([2, 4, 2, 2])
with col1: st.subheader(posicao_jogador)
with col2: st.subheader(nome_jogador)
with col3: st.metric("⭐ Overall", overall_jogador)
with col4: st.metric("💰 Lance Atual", f"R$ {valor_atual:,.0f}".replace(",", "."))

st.markdown(f"🏳️ **Origem:** {origem} &nbsp;&nbsp;&nbsp;&nbsp; 🌍 **Nacionalidade:** {nacionalidade}")
st.markdown("---")

# 🏧 Último lance
if id_time_vencedor:
    nome_time = supabase.table("times").select("nome").eq("id", id_time_vencedor).execute().data[0]["nome"]
    st.info(f"🏷️ Último Lance: {nome_time}")

# ⏹️ Finalização automática
if tempo_restante == 0:
    if id_time_vencedor:
        jogador = {
            "nome": nome_jogador,
            "posicao": posicao_jogador,
            "overall": overall_jogador,
            "valor": valor_atual,
            "id_time": id_time_vencedor
        }

        supabase.table("elenco").insert(jogador).execute()

        saldo_ref = supabase.table("times").select("saldo").eq("id", id_time_vencedor).execute()
        saldo = saldo_ref.data[0]["saldo"]
        novo_saldo = saldo - valor_atual
        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time_vencedor).execute()

        registrar_movimentacao(
            id_time=id_time_vencedor,
            jogador=nome_jogador,
            tipo="leilao",
            categoria="compra",
            valor=valor_atual,
            origem="leilao"
        )

        st.success(f"✅ {nome_jogador} foi arrematado por {nome_time} por R$ {valor_atual:,.0f}!".replace(",", "."))

    supabase.table("leiloes").update({"ativo": False, "finalizado": True}).eq("id", leilao["id"]).execute()
    st.stop()

# 📢 Dar lances
if tempo_restante > 0:
    st.markdown("### 💥 Dar um Lance")
    colunas = st.columns(5)
    botoes = [(incremento * i) for i in range(1, 11)]  # 10 valores

    for i, aumento in enumerate(botoes):
        novo_lance = valor_atual + aumento
        with colunas[i % 5]:
            if st.button(f"➕ R$ {novo_lance:,.0f}".replace(",", "."), key=f"lance_{i}"):
                saldo_ref = supabase.table("times").select("saldo").eq("id", id_time_usuario).execute()
                saldo = saldo_ref.data[0]["saldo"]

                if novo_lance > saldo:
                    st.error("❌ Saldo insuficiente.")
                else:
                    fim_estendido = datetime.utcnow()
                    if (fim_dt - fim_estendido).total_seconds() <= 15:
                        fim_dt = fim_estendido + timedelta(seconds=15)

                    supabase.table("leiloes").update({
                        "valor_atual": novo_lance,
                        "id_time_atual": id_time_usuario,
                        "time_vencedor": nome_time_usuario,
                        "fim": fim_dt.isoformat()
                    }).eq("id", leilao["id"]).execute()

                    st.success("✅ Lance enviado com sucesso!")
                    st.experimental_rerun()

st.markdown("---")
if st.button("🔄 Atualizar"):
    st.experimental_rerun()
