# utils.py
import streamlit as st
from supabase import create_client
from datetime import datetime

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

def verificar_login():
    if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()

# 🧾 Registro no BID
def registrar_movimentacao_simples(id_time, tipo, valor, descricao):
    supabase.table("movimentacoes").insert({
        "id_time": id_time,
        "tipo": tipo,
        "valor": valor,
        "descricao": descricao,
        "data": datetime.now().isoformat()
    }).execute()

# 💰 Salário + Premiação por Jogo
def pagar_salario_e_premiacao_resultado(id_mandante, id_visitante, gols_m, gols_v, divisao):
    # Premiação por divisão
    premiacoes = {
        1: {"vitoria": 12_000_000, "empate": 9_000_000, "derrota": 4_500_000},
        2: {"vitoria": 9_000_000,  "empate": 6_000_000, "derrota": 3_000_000},
        3: {"vitoria": 6_000_000,  "empate": 4_500_000, "derrota": 2_000_000},
    }

    # 🔍 Buscar salários
    def calcular_salario_total(id_time):
        res = supabase.table("elenco").select("salario").eq("id_time", id_time).execute()
        salarios = [p["salario"] for p in res.data if p.get("salario")]
        return sum(salarios)

    # 🧮 Resultado
    if gols_m > gols_v:
        resultado = {id_mandante: "vitoria", id_visitante: "derrota"}
    elif gols_m < gols_v:
        resultado = {id_mandante: "derrota", id_visitante: "vitoria"}
    else:
        resultado = {id_mandante: "empate", id_visitante: "empate"}

    for id_time, gols_feitos, gols_sofridos in [(id_mandante, gols_m, gols_v), (id_visitante, gols_v, gols_m)]:
        # Premiação por resultado
        r = resultado[id_time]
        premio_resultado = premiacoes[divisao][r]

        # Bônus de gols
        bonus_gols = (gols_feitos * 200_000) - (gols_sofridos * 25_000)

        # Total a receber
        valor_credito = premio_resultado + bonus_gols

        # 💰 Crédito
        supabase.table("times").update({
            "saldo": f"saldo + {valor_credito}"
        }).eq("id", id_time).execute()

        registrar_movimentacao_simples(
            id_time, "entrada", valor_credito,
            f"Premiação por {r} | Gols: +{gols_feitos} / -{gols_sofridos}"
        )

        # 🧾 Salário
        total_salario = calcular_salario_total(id_time)
        supabase.table("times").update({
            "saldo": f"saldo - {total_salario}"
        }).eq("id", id_time).execute()

        registrar_movimentacao_simples(
            id_time, "saida", total_salario, "Pagamento de salários da rodada"
        )

