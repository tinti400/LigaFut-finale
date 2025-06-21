from supabase import create_client
import streamlit as st
from datetime import datetime
import uuid

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
def verificar_login():
    if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
        st.warning("Você precisa estar logado.")
        st.stop()

# 💰 Registrar movimentações
def registrar_movimentacao_simples(id_time, tipo, valor, descricao):
    supabase.table("movimentacoes_financeiras").insert({
        "id": str(uuid.uuid4()),
        "id_time": id_time,
        "tipo": tipo,
        "valor": valor,
        "descricao": descricao,
        "data": datetime.now().isoformat()
    }).execute()

# 🧾 Pagamento de salário e premiação por resultado
def pagar_salario_e_premiacao_resultado(id_time_1, id_time_2, gols_1, gols_2, divisao):

    premiacoes = {
        1: {"vitoria": 12_000_000, "empate": 9_000_000, "derrota": 4_500_000},
        2: {"vitoria": 9_000_000, "empate": 6_000_000, "derrota": 3_000_000},
        3: {"vitoria": 6_000_000, "empate": 4_500_000, "derrota": 2_000_000},
    }

    bonus_gol = 200_000
    desconto_gol_sofrido = 25_000

    # Função para processar um time
    def processar_time(id_time, gols_feitos, gols_sofridos, resultado):
        # 🟢 Buscar elenco
        res = supabase.table("elenco").select("salario").eq("id_time", id_time).execute()
        salarios = [j["salario"] for j in res.data if j.get("salario")]
        total_salario = sum(salarios)

        # 🟢 Premiação base por resultado
        valor_resultado = premiacoes[divisao][resultado]

        # 🟢 Bonus por gols e descontos por gols sofridos
        bonus_gols = gols_feitos * bonus_gol
        desconto_gols = gols_sofridos * desconto_gol_sofrido

        # 🟢 Valor final a ser creditado
        valor_credito = valor_resultado + bonus_gols - desconto_gols

        # 🔄 Buscar saldo atual
        res_saldo = supabase.table("times").select("saldo").eq("id", id_time).single().execute()
        saldo_atual = res_saldo.data["saldo"] if res_saldo.data else 0

        # 💰 Atualizar com a premiação
        novo_saldo = saldo_atual + valor_credito
        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
        registrar_movimentacao_simples(
            id_time, "entrada", valor_credito,
            f"Premiação por {resultado} | Gols: +{gols_feitos} / -{gols_sofridos}"
        )

        # 💸 Atualizar com salário
        saldo_pos_credito = novo_saldo
        novo_saldo_final = saldo_pos_credito - total_salario
        supabase.table("times").update({"saldo": novo_saldo_final}).eq("id", id_time).execute()
        registrar_movimentacao_simples(
            id_time, "saida", total_salario, "Pagamento de salários da rodada"
        )

    # 🧠 Definir resultados individuais
    if gols_1 > gols_2:
        r1, r2 = "vitoria", "derrota"
    elif gols_1 < gols_2:
        r1, r2 = "derrota", "vitoria"
    else:
        r1 = r2 = "empate"

    # ⚙️ Executar processamento dos dois times
    processar_time(id_time_1, gols_1, gols_2, r1)
    processar_time(id_time_2, gols_2, gols_1, r2)
