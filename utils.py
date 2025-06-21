from supabase import create_client
from datetime import datetime
import uuid
import streamlit as st

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 💸 Registrar movimentação
def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None):
    try:
        supabase.table("movimentacoes").insert({
            "id": str(uuid.uuid4()),
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "origem": origem,
            "destino": destino,
            "data": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        print(f"Erro ao registrar movimentação: {e}")

# 🧾 Movimentação simples (sem jogador)
def registrar_movimentacao_simples(id_time, tipo, valor, descricao):
    try:
        supabase.table("movimentacoes").insert({
            "id": str(uuid.uuid4()),
            "id_time": id_time,
            "tipo": tipo,
            "categoria": "ajuste",
            "valor": valor,
            "descricao": descricao,
            "data": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        print(f"Erro ao registrar movimentação simples: {e}")

# 💰 Pagar salários fixos por rodada
def pagar_salarios_fixos(id_time, divisao):
    valor_por_jogador = 1_000_000 if divisao == 1 else 750_000
    res = supabase.table("elenco").select("id").eq("id_time", id_time).execute()
    total_jogadores = len(res.data) if res.data else 0
    total_pagamento = valor_por_jogador * total_jogadores

    # Registrar movimentação
    registrar_movimentacao_simples(id_time, "salario", -total_pagamento, f"Pagamento de salário fixo para {total_jogadores} jogadores")

    # Atualizar saldo
    supabase.table("times").update({
        "saldo": f"saldo - {total_pagamento}"
    }).eq("id", id_time).execute()

# 🏆 Premiação por vitória/empate
def pagar_premiacao_por_resultado(id_time_mandante, id_time_visitante, gols_mandante, gols_visitante, divisao):
    premio_vitoria = 2_500_000 if divisao == 1 else 1_500_000
    premio_empate = 1_000_000

    def premiar(id_time, valor, resultado):
        registrar_movimentacao_simples(
            id_time,
            "premiacao",
            valor,
            f"Premiação por {resultado}"
        )
        supabase.table("times").update({
            "saldo": f"saldo + {valor}"
        }).eq("id", id_time).execute()

    if gols_mandante > gols_visitante:
        premiar(id_time_mandante, premio_vitoria, "vitória")
    elif gols_mandante < gols_visitante:
        premiar(id_time_visitante, premio_vitoria, "vitória")
    else:
        premiar(id_time_mandante, premio_empate, "empate")
        premiar(id_time_visitante, premio_empate, "empate")
