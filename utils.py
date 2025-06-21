from supabase import create_client
import uuid
from datetime import datetime
import streamlit as st

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None):
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

def pagar_salario(id_time):
    res = supabase.table("elenco").select("nome", "valor").eq("id_time", id_time).execute()
    jogadores = res.data or []
    total_salario = sum(round(j["valor"] * 0.02) for j in jogadores)
    
    if total_salario > 0:
        supabase.table("times").update({"saldo": f"saldo - {total_salario}"}).eq("id", id_time).execute()
        registrar_movimentacao(id_time, "Todos", "salario", "mensal", -total_salario)

def pagar_premiacao(id_mandante, id_visitante, gols_m, gols_v, divisao):
    premiacao_vitoria = {
        1: 5000000,
        2: 4000000,
        3: 3000000
    }
    premiacao_empate = {
        1: 1000000,
        2: 800000,
        3: 600000
    }
    valor_vitoria = premiacao_vitoria.get(divisao, 0)
    valor_empate = premiacao_empate.get(divisao, 0)

    if gols_m > gols_v:
        # Mandante venceu
        supabase.table("times").update({"saldo": f"saldo + {valor_vitoria}"}).eq("id", id_mandante).execute()
        registrar_movimentacao(id_mandante, "Vitória", "premiacao", "vitoria", valor_vitoria)
    elif gols_v > gols_m:
        # Visitante venceu
        supabase.table("times").update({"saldo": f"saldo + {valor_vitoria}"}).eq("id", id_visitante).execute()
        registrar_movimentacao(id_visitante, "Vitória", "premiacao", "vitoria", valor_vitoria)
    else:
        # Empate
        supabase.table("times").update({"saldo": f"saldo + {valor_empate}"}).eq("id", id_mandante).execute()
        supabase.table("times").update({"saldo": f"saldo + {valor_empate}"}).eq("id", id_visitante).execute()
        registrar_movimentacao(id_mandante, "Empate", "premiacao", "empate", valor_empate)
        registrar_movimentacao(id_visitante, "Empate", "premiacao", "empate", valor_empate)

