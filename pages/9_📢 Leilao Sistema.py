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

# 🔍 Buscar leilão ativo
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

# 🖼️ Exibir imagem e dados organizados
st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)

if imagem_url:
    st.image(imagem_url, width=250)

st.markdown(f"""
<h3>{nome_jogador}</h3>
<p>
<b>Posição:</b> {posicao_jogador} &nbsp;&nbsp; 
<b>Overall:</b> {overall_jogador} &nbsp;&nbsp; 
<b>Nacionalidade:</b> {nacionalidade}<br><br>
<b>💰 Preço Atual:</b> R$ {valor_atual:,.0f}
</p>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ⏳ Cronômetro visual
st.markdown(f"<h2 style='text-align:center'>⏳ Tempo restante: {minutos:02d}:{segundos:02d}</h2>", unsafe_allow_html=True)
st.markdown("---")

# 🏧 Último lance
if id_time_vencedor:
    nome_time = supabase.table("times").select("nome").eq("id", id_time_vencedor).execute().data[0]["nome"]
    st.info(f"🏷️ Último Lance: {nome_time}")

# ⏹️ Marcar leilão como aguardando validação
if tempo_restante == 0:
    leilao_atualizado = supabase.table("leiloes").select("finalizado", "validado").eq("id", leilao["id"]).execute()
    if leilao_atualizado.data and not leilao_atualizado.data[0]["finalizado"] and not leilao_atualizado.data[0].get("validado", False):

        supabase.table("leiloes").update({
            "ativo": False,
            "aguardando_validacao": True
        }).eq("id", leilao["id"]).execute()

        st.success("✅ Leilão finalizado! Aguardando validação do administrador.")
    else:
        st.info("⏳ Leilão já finalizado ou validado.")

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
                    st.rerun()

st.markdown("---")
if st.button("🔄 Atualizar"):
    st.rerun()
