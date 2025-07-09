# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import verificar_sessao, registrar_movimentacao
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
st.markdown("Invista no seu clube e escolha um jogador como garantia do empréstimo.")

# 🔍 Verifica divisão do time
res_div = supabase.table("times").select("divisao", "saldo").eq("id", id_time).execute()
time_data = res_div.data[0]
divisao_raw = time_data.get("divisao")
divisao = str(divisao_raw).strip().lower() if divisao_raw else "outros"
saldo_atual = time_data.get("saldo", 0)

# 💳 Limite por divisão
limites_divisao = {
    "1": 500_000_000,
    "2": 300_000_000,
    "3": 150_000_000
}
limite_maximo = limites_divisao.get(divisao, 100_000_000)

# 🔍 Verifica empréstimo ativo
res = supabase.table("emprestimos").select("*").eq("id_time", id_time).eq("status", "ativo").execute()
emprestimo_ativo = res.data[0] if res.data else None

if emprestimo_ativo:
    st.warning("📛 Empréstimo ativo detectado. Quite-o antes de solicitar um novo.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**💵 Valor Total:** R$ {emprestimo_ativo['valor_total']:,}")
        st.markdown(f"**📆 Parcelas Totais:** {emprestimo_ativo['parcelas_totais']}")
        st.markdown(f"**📅 Tipo de Parcelamento:** Por Turno")
    with col2:
        st.markdown(f"**🔁 Parcelas Restantes:** {emprestimo_ativo['parcelas_restantes']}")
        st.markdown(f"**💸 Valor por Turno:** R$ {emprestimo_ativo['valor_parcela']:,}")
        st.markdown(f"**📈 Juros:** {int(emprestimo_ativo['juros'] * 100)}%")

    if "jogador_garantia" in emprestimo_ativo:
        g = emprestimo_ativo["jogador_garantia"]
        st.info(f"🎯 **Garantia:** {g['nome']} ({g['posicao']}) - R$ {g['valor']:,}")

else:
    with st.expander("ℹ️ Como funciona o parcelamento por turno?"):
        st.markdown("""
        Em vez de pagar por rodada, o valor do empréstimo é dividido por turnos da liga:

        - **1 turno** ➜ 5% de juros  
        - **2 turnos** ➜ 10%  
        - **3 turnos** ➜ 15%  
        - **4 turnos** ➜ 20%

        Ao final de cada turno, será cobrada 1 parcela automaticamente.  
        **É obrigatório escolher um jogador como garantia**, entre os 7 mais valiosos do elenco.
        """)

    st.info(f"💳 Limite de crédito disponível para sua divisão (**{divisao.upper()}**): R$ {limite_maximo:,}")

    valor_milhoes = st.slider("💰 Valor do Empréstimo (milhões)", 10, int(limite_maximo / 1_000_000), 20, step=5)
    valor = valor_milhoes * 1_000_000

    parcelas = st.selectbox("📆 Quantidade de Turnos para pagamento", [1, 2, 3, 4])
    juros_por_turno = {1: 0.05, 2: 0.10, 3: 0.15, 4: 0.20}
    juros = juros_por_turno.get(parcelas, 0.20)

    valor_total = int(valor * (1 + juros))
    valor_parcela = int(valor_total / parcelas)

    # 🔍 Buscar os 7 jogadores mais valiosos
    elenco_data = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data
    jogadores_valiosos = sorted(elenco_data, key=lambda x: x.get("valor", 0), reverse=True)[:7]

    if not jogadores_valiosos:
        st.error("❌ Seu time não possui jogadores cadastrados para oferecer como garantia.")
        st.stop()

    jogador_nomes = [f"{j['nome']} - {j['posicao']} (R$ {j['valor']:,})" for j in jogadores_valiosos]
    jogador_escolhido = st.selectbox("🎯 Selecione um jogador como garantia:", jogador_nomes)
    jogador_garantia = jogadores_valiosos[jogador_nomes.index(jogador_escolhido)]

    st.markdown("---")
    st.markdown(f"**💵 Valor Total com Juros:** R$ {valor_total:,}")
    st.markdown(f"**📆 Parcelas:** {parcelas}x (por turno)")
    st.markdown(f"**💸 Valor por Turno:** R$ {valor_parcela:,}")
    st.markdown(f"**📈 Juros Aplicados:** {int(juros * 100)}%")
    st.markdown(f"**🛡️ Garantia:** {jogador_garantia['nome']} ({jogador_garantia['posicao']}) - R$ {jogador_garantia['valor']:,}")

    if valor > limite_maximo:
        st.error("🚫 Valor excede o limite permitido para sua divisão.")
    elif st.button("✅ Solicitar Empréstimo"):
        try:
            # 💾 Registra o empréstimo
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
                "data_inicio": datetime.now().isoformat(),
                "jogador_garantia": {
                    "nome": jogador_garantia["nome"],
                    "posicao": jogador_garantia["posicao"],
                    "valor": jogador_garantia["valor"]
                }
            }).execute()

            # 💰 Atualiza saldo
            novo_saldo = saldo_atual + valor
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

            # 🧾 Registrar movimentação
            registrar_movimentacao(
                id_time=id_time,
                tipo="entrada",
                valor=valor,
                descricao=f"Empréstimo (por turno) com garantia: {jogador_garantia['nome']}",
                categoria="empréstimo"
            )

            st.success("✅ Empréstimo aprovado e valor adicionado ao saldo.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao registrar empréstimo: {e}")
