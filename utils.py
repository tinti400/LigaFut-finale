from datetime import datetime
import uuid
import streamlit as st
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

def verificar_login():
    if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()

# 💰 Registrar movimentações financeiras simples
def registrar_movimentacao_simples(id_time, tipo, valor, descricao):
    try:
        supabase.table("movimentacoes_financeiras").insert({
            "id": str(uuid.uuid4()),
            "id_time": id_time,
            "tipo": tipo,
            "valor": float(valor),
            "descricao": str(descricao),
            "data": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")

# 💸 Salário + Premiação por resultado
def pagar_salario_e_premiacao_resultado(id_time_1, id_time_2, gols_1, gols_2, divisao):
    def processar_time(id_time, gols_pro, gols_sofridos, resultado):
        # Valores base por divisão
        valores = {
            1: {"vitoria": 12_000_000, "empate": 9_000_000, "derrota": 4_500_000},
            2: {"vitoria": 9_000_000, "empate": 6_000_000, "derrota": 3_000_000},
            3: {"vitoria": 6_000_000, "empate": 4_500_000, "derrota": 2_000_000},
        }

        bonus_gols = gols_pro * 200_000
        desconto_gols = gols_sofridos * 25_000

        premio = 0
        if resultado == "vitoria":
            premio = valores[divisao]["vitoria"]
        elif resultado == "empate":
            premio = valores[divisao]["empate"]
        else:
            premio = valores[divisao]["derrota"]

        # 💵 Valor final da premiação
        total_receber = premio + bonus_gols - desconto_gols

        # Buscar salários
        elenco = supabase.table("elencos").select("salario").eq("id_time", id_time).execute().data
        total_salarios = sum(jogador.get("salario", 0) for jogador in elenco)

        # Atualiza saldo do time
        res_time = supabase.table("times").select("saldo").eq("id", id_time).execute()
        if res_time.data:
            saldo_atual = res_time.data[0]["saldo"]
            novo_saldo = saldo_atual + total_receber - total_salarios

            supabase.table("times").update({
                "saldo": novo_saldo
            }).eq("id", id_time).execute()

        # Registrar movimentações
        registrar_movimentacao_simples(id_time, "entrada", premio, f"Premiação por {resultado}")
        registrar_movimentacao_simples(id_time, "entrada", bonus_gols, f"Bônus por {gols_pro} gol(s) feito(s)")
        if desconto_gols > 0:
            registrar_movimentacao_simples(id_time, "saida", desconto_gols, f"Desconto por {gols_sofridos} gol(s) sofrido(s)")
        if total_salarios > 0:
            registrar_movimentacao_simples(id_time, "saida", total_salarios, f"Pagamento de salários ({len(elenco)} jogadores)")

    # Resultado de cada time
    if gols_1 > gols_2:
        r1, r2 = "vitoria", "derrota"
    elif gols_1 < gols_2:
        r1, r2 = "derrota", "vitoria"
    else:
        r1 = r2 = "empate"

    processar_time(id_time_1, gols_1, gols_2, r1)
    processar_time(id_time_2, gols_2, gols_1, r2)
