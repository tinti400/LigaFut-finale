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
st.markdown("Simule e solicite um empréstimo para investir no seu time!")

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
    st.info("📌 Você pode solicitar um novo empréstimo abaixo:")

    valor_milhoes = st.slider("Valor desejado (em milhões)", 10, 100, 20, step=5)
    valor = valor_milhoes * 1_000_000

    parcelas = st.selectbox("Número de parcelas", [3, 6, 10])
    juros = 0.10 if parcelas == 3 else 0.08 if parcelas == 6 else 0.05

    valor_total = int(valor * (1 + juros))
    valor_parcela = int(valor_total / parcelas)

    st.markdown("---")
    st.markdown(f"**💵 Valor Total a Pagar:** R$ {valor_total:,}")
    st.markdown(f"**📆 Parcelas:** {parcelas}x de R$ {valor_parcela:,}")
    st.markdown(f"**📈 Juros aplicados:** {int(juros * 100)}%")

    if st.button("✅ Solicitar Empréstimo"):
        try:
            # 🔽 Cria novo empréstimo
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

            # 💰 Atualiza saldo do time
            res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
            saldo_atual = res_saldo.data[0]["saldo"] if res_saldo.data else 0
            novo_saldo = saldo_atual + valor
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

            # 📌 Registro da movimentação
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
