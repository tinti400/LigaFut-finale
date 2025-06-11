# 25_Painel_Administrativo.py

import streamlit as st
from supabase import create_client
from datetime import datetime
import json

st.set_page_config(page_title="🛠️ Painel Administrativo", layout="centered")
st.title("🛠️ Painel Administrativo - LigaFut")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.subheader("⚖️ Aplicar Punição")

# 📥 Buscar times
try:
    res = supabase.table("times").select("id, nome, saldo, restricoes").execute()
    times = res.data
except Exception as e:
    st.error(f"Erro ao carregar times: {e}")
    st.stop()

if not times:
    st.warning("Nenhum time encontrado.")
    st.stop()

# 📌 Selecionar time
nomes_times = {t["nome"]: t for t in times}
nome_escolhido = st.selectbox("Selecione o time", list(nomes_times.keys()))
time_escolhido = nomes_times[nome_escolhido]
id_time = time_escolhido["id"]
saldo_atual = time_escolhido["saldo"]
restricoes_atuais = time_escolhido.get("restricoes", {})

# 🛑 Tipo de punição
tipo_punicao = st.radio("Tipo de punição", ["Perda de pontos", "Multa financeira"])

# 🔢 Valor da punição
valor = st.number_input(
    "Quantos pontos retirar?" if tipo_punicao == "Perda de pontos" else "Qual valor da multa? (R$)",
    min_value=1, step=1
)

# 📝 Motivo
motivo = st.text_input("Motivo da punição (opcional)").strip()

# ✅ Aplicar punição
if st.button("✅ Aplicar Punição"):
    try:
        if tipo_punicao == "Perda de pontos":
            supabase.table("punicoes").insert({
                "id_time": id_time,
                "nome_time": nome_escolhido,
                "pontos_retirados": valor,
                "motivo": motivo or "-",
                "tipo": "pontos",
                "data": datetime.now().isoformat()
            }).execute()
            st.success(f"✅ {valor} ponto(s) retirado(s) do time {nome_escolhido}.")

        else:
            novo_saldo = max(0, saldo_atual - valor)
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

            supabase.table("movimentacoes").insert({
                "id_time": id_time,
                "jogador": "Punição Financeira",
                "tipo": "punição",
                "categoria": "saída",
                "valor": valor,
                "origem": nome_escolhido,
                "data": datetime.now().isoformat()
            }).execute()

            supabase.table("punicoes").insert({
                "id_time": id_time,
                "nome_time": nome_escolhido,
                "pontos_retirados": 0,
                "motivo": motivo or "-",
                "tipo": "financeira",
                "data": datetime.now().isoformat()
            }).execute()

            st.success(f"💰 Multa de R$ {valor:,.0f} aplicada ao time {nome_escolhido}.".replace(",", "."))

    except Exception as e:
        st.error(f"Erro ao aplicar punição: {e}")

# 🧱 Seção de restrições
st.markdown("---")
st.subheader("🚫 Restrições de Acesso do Time")

# Carregar estado atual (se já houver)
r = restricoes_atuais if isinstance(restricoes_atuais, dict) else {}

# Checkboxes para restrições
bloq_leilao = st.checkbox("Proibir de participar do Leilão", value=r.get("leilao", False))
bloq_mercado = st.checkbox("Proibir de usar o Mercado de Transferências", value=r.get("mercado", False))
bloq_roubo = st.checkbox("Proibir no Evento de Roubo", value=r.get("roubo", False))
bloq_multa = st.checkbox("Proibir no Evento de Multa", value=r.get("multa", False))

# Botão para aplicar restrições
if st.button("🔒 Atualizar Restrições do Time"):
    nova_restricao = {
        "leilao": bloq_leilao,
        "mercado": bloq_mercado,
        "roubo": bloq_roubo,
        "multa": bloq_multa
    }

    try:
        supabase.table("times").update({"restricoes": nova_restricao}).eq("id", id_time).execute()
        st.success("🔒 Restrições atualizadas com sucesso.")
    except Exception as e:
        st.error(f"Erro ao salvar restrições: {e}")


