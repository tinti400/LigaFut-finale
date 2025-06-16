# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
from utils import registrar_movimentacao

st.set_page_config(page_title="Leilões Ativos - LigaFut", layout="wide")

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

# 🔒 Verifica restrição de leilão
res_restricoes = supabase.table("times").select("restricoes").eq("id", id_time_usuario).execute()
restricoes = res_restricoes.data[0].get("restricoes", {}) if res_restricoes.data else {}
if restricoes.get("leilao", False):
    st.error("🚫 Seu time está proibido de participar de leilões.")
    st.stop()

# 🔍 Buscar até 3 leilões ativos
res = supabase.table("leiloes").select("*").eq("ativo", True).eq("finalizado", False).limit(3).execute()
leiloes = res.data

if not leiloes:
    st.warning("⚠️ Nenhum leilão ativo no momento.")
    st.stop()

# 🔄 Loop por leilões ativos
for leilao in leiloes:
    st.markdown("---")
    st.markdown(f"### 🧤 {leilao['nome_jogador']} ({leilao['posicao_jogador']})")

    # 📦 Dados
    fim = leilao.get("fim")
    valor_atual = leilao["valor_atual"]
    incremento = leilao["incremento_minimo"]
    id_time_vencedor = leilao.get("id_time_atual", "")
    imagem_url = leilao.get("imagem_url", "")
    overall_jogador = leilao.get("overall_jogador", "N/A")
    nacionalidade = leilao.get("nacionalidade", "Desconhecida")

    # ⏱️ Cronômetro
    fim_dt = datetime.fromisoformat(fim)
    tempo_restante = max(0, int((fim_dt - datetime.utcnow()).total_seconds()))
    minutos, segundos = divmod(tempo_restante, 60)

    # 📸 Imagem + Info
    col1, col2 = st.columns([1, 3])
    with col1:
        if imagem_url:
            st.image(imagem_url, width=180)
    with col2:
        st.markdown(f"""
        **Overall:** {overall_jogador}  
        **Nacionalidade:** {nacionalidade}  
        **💰 Preço Atual:** R$ {valor_atual:,.0f}  
        **⏳ Tempo restante:** {minutos:02d}:{segundos:02d}
        """)
        if id_time_vencedor:
            nome_time = supabase.table("times").select("nome").eq("id", id_time_vencedor).execute().data[0]["nome"]
            st.info(f"🏷️ Último Lance: {nome_time}")

    # ⏹️ Finalizar leilão se tempo acabou
    if tempo_restante == 0:
        atual = supabase.table("leiloes").select("finalizado", "validado").eq("id", leilao["id"]).execute()
        if atual.data and not atual.data[0].get("finalizado") and not atual.data[0].get("validado"):
            supabase.table("leiloes").update({
                "ativo": False,
                "aguardando_validacao": True
            }).eq("id", leilao["id"]).execute()
            st.success("✅ Leilão finalizado! Aguardando validação.")
        continue

    # 📢 Lances de múltiplos do incremento mínimo
    st.markdown("#### 💥 Dar um Lance")
    colunas = st.columns(5)
    botoes = [incremento * i for i in range(1, 11)]
    for i, aumento in enumerate(botoes):
        novo_lance = valor_atual + aumento
        with colunas[i % 5]:
            if st.button(f"➕ R$ {novo_lance:,.0f}".replace(",", "."), key=f"lance_{leilao['id']}_{i}"):
                saldo_ref = supabase.table("times").select("saldo").eq("id", id_time_usuario).execute()
                saldo = saldo_ref.data[0]["saldo"]
                if novo_lance > saldo:
                    st.error("❌ Saldo insuficiente.")
                else:
                    if (fim_dt - datetime.utcnow()).total_seconds() <= 15:
                        novo_fim = datetime.utcnow() + timedelta(seconds=15)
                    else:
                        novo_fim = fim_dt
                    supabase.table("leiloes").update({
                        "valor_atual": novo_lance,
                        "id_time_atual": id_time_usuario,
                        "time_vencedor": nome_time_usuario,
                        "fim": novo_fim.isoformat()
                    }).eq("id", leilao["id"]).execute()
                    st.success("✅ Lance enviado com sucesso!")
                    st.rerun()

st.markdown("---")
if st.button("🔄 Atualizar"):
    st.rerun()
