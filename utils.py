# utils.py
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

def verificar_login():
    if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()

# 💸 Função de movimentação financeira
def registrar_movimentacao_simples(id_time, valor, descricao):
    data = {
        "id": str(uuid.uuid4()),
        "id_time": id_time,
        "valor": valor,
        "descricao": descricao,
        "data": datetime.now().isoformat()
    }
    supabase.table("movimentacoes").insert(data).execute()

# 💼 Função de pagamento de salários e premiações
def pagar_salario_e_premiacao_resultado(id_mandante, id_visitante, gols_m, gols_v, divisao):
    divisao = int(divisao)

    # 💰 Configurações de premiação por divisão
    premiacoes = {
        1: {"vitoria": 12_000_000, "empate": 9_000_000, "derrota": 4_500_000},
        2: {"vitoria": 9_000_000, "empate": 6_000_000, "derrota": 3_000_000},
        3: {"vitoria": 6_000_000, "empate": 4_500_000, "derrota": 2_000_000},
    }

    salarios = {
        1: 5_000_000,
        2: 4_000_000,
        3: 3_000_000,
    }

    # ⚽️ Resultado do jogo
    if gols_m > gols_v:
        resultado = {id_mandante: "vitoria", id_visitante: "derrota"}
    elif gols_m < gols_v:
        resultado = {id_mandante: "derrota", id_visitante: "vitoria"}
    else:
        resultado = {id_mandante: "empate", id_visitante: "empate"}

    for id_time in [id_mandante, id_visitante]:
        r = resultado[id_time]
        premio = premiacoes[divisao][r]
        salario = salarios[divisao]
        total = premio + salario

        # Atualizar saldo
        supabase.table("times").update({
            "saldo": f"saldo + {total}"
        }).eq("id", id_time).execute()

        registrar_movimentacao_simples(id_time, total, f"Premiação ({r}) + Salário")

