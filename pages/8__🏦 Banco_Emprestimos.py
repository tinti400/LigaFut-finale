# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import verificar_sessao
from datetime import datetime
import uuid

st.set_page_config(page_title="🏦 Banco LigaFut", layout="centered")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
verificar_sessao()
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("🏦 Banco LigaFut")
st.markdown("Invista no seu time com um empréstimo escalonado por divisão.")

# 🔍 Verifica divisão do time
res_div = supabase.table("times").select("divisao", "saldo").eq("id", id_time).execute()
time_data = res_div.data[0]
divisao = time_data.get("divisao", "Outros").lower()
saldo_atual = time_data.get("saldo", 0)

# 💳 Limite por divisão
limites_divisao = {
    "1": 500_000_000,
    "2": 300_000_000,
    "3": 150_000_000
}
limite_maximo = limites_divisao.get(divisao, 100_000_000)

# 🔍 Verifica se já tem empréstimo ativo
res = supabase.table("emprestimos").select("*").eq("id_time", id_time).eq("status", "ativo").execute()
emprestimo_ativo = res.data[0] if res.data else None

if emprestimo_ativo:
    st.warning("❗ Você já possui um empréstimo ativo. Quite-o antes de solicitar outro.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**💵 Valor Total:** R$ {emprestimo_ativo['valor_total']:,}")
        st.markdown(f"**📆 Parcelas Totais:** {emprestimo_ativo['parcelas_totais']}")
        st.markdown(f"**🔁 Parcelas Restantes:** {emprestimo_ativo['parcelas_restantes']}")
    with col2:
        st.markdown(f"**📊 Valor da Parcela:** R$ {emprestimo_ativo['valor_parcela']:,}")
        st.markdown(f"**📈 Juros:** {int(emprestimo_ativo['juros'] * 100)}%")
        st.markdown(f"**📅 Início:** {datetime.fromisoformat(emprestimo_ativo['data_inicio']).strftime('%d/%m/%Y %H:%M')}")
    
    st.success("Status: 🟢 Empréstimo Ativo")
else:
    st.info(f"📌 Seu limite de crédito disponível é de **R$ {limite_maximo:,}** com base na divisão atual.")

    valor_milhoes = st.slider("Valor desejado (em milhões)", 10, int(limite_maximo / 1_000_000), 20, step=5)
    valor = valor_milhoes * 1_000_000

    parcelas = st.selectbox("Número de parcelas (rodadas)", [3, 6, 10])
    juros = 0.10 if parcelas == 3 else 0.08 if parcelas == 6 else 0.05

    valor_total = int(valor * (1 + juros))
    valor_parcela = int(valor_total / parcelas)

    st.markdown("---")
    st.markdown(f"**💵 Valor Total com Juros:** R$ {valor_total:,}")
    st.markdown(f"**📆 Parcelas:** {parcelas} rodadas")
    st.markdown(f"**🔁 Valor por Rodada:** R$ {valor_parcela:,}")
    st.markdown(f"**📈 Juros Aplicados:** {int(juros * 100)}%")

    if valor > limite_maximo:
        st.error(f"🚫 Valor excede o limite permitido para sua divisão.")
    elif st.button("✅ Solicitar Empréstimo"):
        try:
            supabase.table("emprestimos").insert({
                "id": str(uuid.uuid4()),
                "id_time": id_time,
                "nome_time": nome_time,
                "valor_total": valor_total,
                "parcelas_totais": parcelas,
                "parcelas_restantes": parcelas,
                "valor_parcela": valor_parcela,
                "juros": juros,
                "status": "ativo",
                "data_inicio": datetime.now().isoformat()
            }).execute()

            novo_saldo = saldo_atual + valor
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

            from utils import registrar_movimentacao
            registrar_movimentacao(
                id_time=id_time,
                tipo="entrada",
                valor=valor,
                descricao=f"Empréstimo bancário: R$ {valor_milhoes} mi",
                categoria="empréstimo"
            )

            st.success("✅ Empréstimo solicitado com sucesso! Valor adicionado ao seu saldo.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao solicitar empréstimo: {e}")
