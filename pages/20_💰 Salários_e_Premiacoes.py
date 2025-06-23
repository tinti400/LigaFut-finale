# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao

st.set_page_config(page_title="💰 Salários e Premiações", layout="wide")
st.markdown("## 💰 Pagamento de Salários e Premiações")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or "usuario" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 🔽 Seleção da divisão e temporada
col1, col2 = st.columns(2)
divisao = col1.selectbox("Divisão", ["Divisão 1", "Divisão 2", "Divisão 3"])
temporada = col2.selectbox("Temporada", ["Temporada 1", "Temporada 2", "Temporada 3"])
numero_divisao = int(divisao.split()[-1])
numero_temporada = int(temporada.split()[-1])

# 🧮 Tabela de rodadas
tabela_rodadas = f"rodadas_temporada_{numero_temporada}_divisao_{numero_divisao}"

# 📥 Buscar rodadas
try:
    res_rodadas = supabase.table(tabela_rodadas).select("*").order("numero", asc=True).execute()
    rodadas = res_rodadas.data if res_rodadas.data else []
except Exception as e:
    st.error(f"Erro ao buscar rodadas: {e}")
    st.stop()

# 💰 Regras financeiras
PREMIO_VITORIA = 3_000_000
PREMIO_EMPATE = 1_500_000
BONUS_GOL = 250_000
MULTA_GOL_SOFRIDO = 150_000

# 🔄 Funções
def buscar_salario_total(id_time):
    try:
        res = supabase.table("times").select("salario_total").eq("id", id_time).execute()
        if res.data:
            return res.data[0].get("salario_total") or 0
    except:
        return 0
    return 0

def atualizar_saldo(id_time, valor, tipo, descricao):
    if tipo == "saida":
        valor = -abs(valor)
    registrar_movimentacao(id_time, tipo, abs(valor), descricao)

def exibir_botoes_jogo(jogo, numero_rodada):
    id_m = jogo["mandante_id"]
    id_v = jogo["visitante_id"]
    nome_m = jogo["mandante"]
    nome_v = jogo["visitante"]
    gol_m = jogo.get("gols_mandante")
    gol_v = jogo.get("gols_visitante")

    if gol_m is None or gol_v is None:
        return

    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    with col1:
        st.markdown(f"**{nome_m}** {gol_m} ⚽ {gol_v} **{nome_v}**")
    with col2:
        if st.button("💸 Salários", key=f"sal_{id_m}_{numero_rodada}"):
            valor = buscar_salario_total(id_m)
            atualizar_saldo(id_m, valor, "saida", f"Salário Rodada {numero_rodada}")
            st.success(f"Salários pagos: R$ {valor:,.0f}".replace(",", "."))
    with col3:
        if st.button("🏆 Premiação", key=f"premio_{id_m}_{numero_rodada}"):
            if gol_m > gol_v:
                atualizar_saldo(id_m, PREMIO_VITORIA, "entrada", f"Vitória Rodada {numero_rodada}")
            elif gol_m == gol_v:
                atualizar_saldo(id_m, PREMIO_EMPATE, "entrada", f"Empate Rodada {numero_rodada}")
            st.success("Premiação aplicada")
    with col4:
        if st.button("⚽ Bônus Gols", key=f"bonus_{id_m}_{numero_rodada}"):
            total_bonus = gol_m * BONUS_GOL
            atualizar_saldo(id_m, total_bonus, "entrada", f"Bônus Gols Rodada {numero_rodada}")
            st.success(f"Bônus por gols: R$ {total_bonus:,.0f}".replace(",", "."))
    with col5:
        if st.button("💀 Multa Gols Sofridos", key=f"multa_{id_m}_{numero_rodada}"):
            total_multa = gol_v * MULTA_GOL_SOFRIDO
            atualizar_saldo(id_m, total_multa, "saida", f"Multa Gols Sofridos Rodada {numero_rodada}")
            st.success(f"Multa aplicada: R$ {total_multa:,.0f}".replace(",", "."))

# 🧾 Exibir rodadas com jogos com placar
for rodada in rodadas:
    jogos = rodada.get("jogos", [])
    jogos_com_placar = [j for j in jogos if j.get("gols_mandante") is not None and j.get("gols_visitante") is not None]
    if not jogos_com_placar:
        continue
    st.markdown(f"### 🗓️ Rodada {rodada['numero']}")
    for jogo in jogos_com_placar:
        exibir_botoes_jogo(jogo, rodada["numero"])
