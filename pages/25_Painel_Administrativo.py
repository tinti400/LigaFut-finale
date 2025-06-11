# 25_Painel_Administrativo.py

import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="🛠️ Painel Administrativo", layout="centered")
st.title("🛠️ Painel Administrativo - LigaFut")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.subheader("⚖️ Aplicar Punição")

# 📥 Buscar times
try:
    res = supabase.table("times").select("id, nome, saldo").execute()
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

# 🛑 Tipo de punição
tipo_punicao = st.radio("Tipo de punição", ["Perda de pontos", "Multa financeira"])

# 🔢 Valor
valor = st.number_input(
    "Quantos pontos retirar?" if tipo_punicao == "Perda de pontos" else "Qual valor da multa? (R$)",
    min_value=1, step=1
)

# 📝 Motivo (opcional)
motivo = st.text_input("Motivo da punição (opcional)").strip()

# 🔘 Aplicar punição
if st.button("✅ Aplicar Punição"):
    try:
        if tipo_punicao == "Perda de pontos":
            # Registrar punição desportiva
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
            # Atualizar saldo
            novo_saldo = max(0, saldo_atual - valor)
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

            # Registrar movimentação financeira
            supabase.table("movimentacoes").insert({
                "id_time": id_time,
                "jogador": "Punição Financeira",
                "tipo": "punição",
                "categoria": "saída",
                "valor": valor,
                "origem": nome_escolhido,
                "data": datetime.now().isoformat()
            }).execute()

            # Registrar punição
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

