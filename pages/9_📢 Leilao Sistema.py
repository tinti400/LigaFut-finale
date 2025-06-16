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

# 🔒 Verifica restrições
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

# 🔁 Loop nos leilões
for leilao in leiloes:
    st.markdown("---")
    st.subheader(f"🧤 {leilao['nome_jogador']} ({leilao['posicao_jogador']})")

    fim = leilao.get("fim")
    fim_dt = datetime.fromisoformat(fim)
    tempo_restante = max(0, int((fim_dt - datetime.utcnow()).total_seconds()))
    minutos, segundos = divmod(tempo_restante, 60)

    valor_atual = leilao["valor_atual"]
    incremento = leilao["incremento_minimo"]
    overall = leilao.get("overall_jogador", "N/A")
    nacionalidade = leilao.get("nacionalidade", "-")
    imagem_url = leilao.get("imagem_url", "")
    id_time_vencedor = leilao.get("id_time_atual", "")

    # 🖼️ Exibir informações
    col1, col2 = st.columns([1, 3])
    with col1:
        if imagem_url:
            st.image(imagem_url, width=180)
    with col2:
        st.markdown(f"""
        **Overall:** {overall}  
        **Nacionalidade:** {nacionalidade}  
        **💰 Preço Atual:** R$ {valor_atual:,.0f}  
        **⏳ Tempo Restante:** {minutos:02d}:{segundos:02d}
        """)
        if id_time_vencedor:
            time_res = supabase.table("times").select("nome").eq("id", id_time_vencedor).execute()
            if time_res.data:
                st.info(f"🏷️ Último Lance: {time_res.data[0]['nome']}")

    # ⏹️ Finalizar leilão se tempo acabar
    if tempo_restante == 0:
        leilao_ref = supabase.table("leiloes").select("finalizado", "validado").eq("id", leilao["id"]).execute()
        dados = leilao_ref.data[0] if leilao_ref.data else {}
        if not dados.get("finalizado") and not dados.get("validado"):
            supabase.table("leiloes").update({
                "ativo": False,
                "aguardando_validacao": True
            }).eq("id", leilao["id"]).execute()
            st.success("✅ Leilão finalizado! Aguardando validação.")
        continue

    # 💸 Lances
    st.markdown("#### 💥 Dar um Lance")
    botoes = [incremento * i for i in range(1, 11)]
    colunas = st.columns(5)

    for i, aumento in enumerate(botoes):
        novo_lance = valor_atual + aumento
        with colunas[i % 5]:
            if st.button(f"➕ R$ {novo_lance:,.0f}".replace(",", "."), key=f"lance_{leilao['id']}_{i}"):
                saldo_res = supabase.table("times").select("saldo").eq("id", id_time_usuario).execute()
                saldo = saldo_res.data[0]["saldo"]
                if novo_lance > saldo:
                    st.error("❌ Saldo insuficiente.")
                else:
                    # ⏳ Estender tempo se necessário
                    agora = datetime.utcnow()
                    if (fim_dt - agora).total_seconds() <= 15:
                        fim_dt = agora + timedelta(seconds=15)

                    # Atualizar leilão
                    supabase.table("leiloes").update({
                        "valor_atual": novo_lance,
                        "id_time_atual": id_time_usuario,
                        "time_vencedor": nome_time_usuario,
                        "fim": fim_dt.isoformat()
                    }).eq("id", leilao["id"]).execute()

                    st.success("✅ Lance enviado com sucesso!")
                    st.experimental_rerun()

# 🔁 Atualizar manualmente
st.markdown("---")
if st.button("🔄 Atualizar Página"):
    st.experimental_rerun()
