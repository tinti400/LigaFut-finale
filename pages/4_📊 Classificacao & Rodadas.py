# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Classificação", page_icon="📊", layout="centered")
st.markdown("## 🏆 Tabela de Classificação")
st.markdown(f"🗓️ Atualizada em: `{datetime.now().strftime('%d/%m/%Y %H:%M')}`")

if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

col1, col2 = st.columns(2)
divisao = col1.selectbox("Selecione a divisão", ["Divisão 1", "Divisão 2", "Divisão 3"])
temporada = col2.selectbox("Selecione a temporada", ["Temporada 1", "Temporada 2", "Temporada 3"])
numero_divisao = int(divisao.split()[-1])
numero_temporada = int(temporada.split()[-1])

def calcular_renda_jogo(estadio, desempenho=0, posicao=10, vitorias=0, derrotas=0):
    capacidade = estadio.get("capacidade", 25000)
    nivel = estadio.get("nivel", 1)

    setores = {
        "geral": 0.40,
        "norte": 0.20,
        "sul": 0.20,
        "central": 0.15,
        "camarote": 0.05
    }

    precos_maximos_por_nivel = {
        1: {"geral": 50, "norte": 75, "sul": 75, "central": 100, "camarote": 250},
        2: {"geral": 75, "norte": 100, "sul": 100, "central": 150, "camarote": 400},
        3: {"geral": 100, "norte": 150, "sul": 150, "central": 200, "camarote": 600},
        4: {"geral": 125, "norte": 200, "sul": 200, "central": 300, "camarote": 800},
        5: {"geral": 150, "norte": 250, "sul": 250, "central": 400, "camarote": 1000}
    }

    precos_maximos = precos_maximos_por_nivel.get(nivel, precos_maximos_por_nivel[1])

    precos = {
        setor: min(float(estadio.get(f"preco_{setor}", 20.0)), precos_maximos[setor])
        for setor in setores
    }

    def calcular_publico_setor(lugares, preco, desempenho, posicao, vitorias, derrotas):
        fator_base = 0.8 + desempenho * 0.007 + (20 - posicao) * 0.005 + vitorias * 0.01 - derrotas * 0.005
        fator_base = max(min(fator_base, 1.0), 0.3)

        if preco <= 20:
            fator_preco = 1.0
        elif preco <= 50:
            fator_preco = 0.85
        elif preco <= 100:
            fator_preco = 0.65
        elif preco <= 200:
            fator_preco = 0.4
        elif preco <= 500:
            fator_preco = 0.25
        elif preco <= 1000:
            fator_preco = 0.1
        else:
            fator_preco = 0.05

        publico_estimado = int(min(lugares, lugares * fator_base * fator_preco))
        renda = publico_estimado * preco
        return publico_estimado, renda

    renda_total = 0
    publico_total = 0

    for setor, proporcao in setores.items():
        lugares = int(capacidade * proporcao)
        preco = precos[setor]
        publico, renda = calcular_publico_setor(
            lugares, preco, desempenho, posicao, vitorias, derrotas
        )
        renda_total += renda
        publico_total += publico

    ocupacao = publico_total / capacidade
    if ocupacao < 0.4:
        fator_penalizacao = 0.5 * (1 - ocupacao / 0.4)
        renda_total *= (1 - fator_penalizacao)

    return int(renda_total), publico_total

@st.cache(ttl=60)
def buscar_resultados(temporada, divisao):
    try:
        res = supabase.table("rodadas").select("*").eq("temporada", temporada).eq("divisao", divisao).order("numero").execute()
        return res.data
    except:
        return []

@st.cache(ttl=60)
def obter_nomes_times(divisao):
    try:
        usuarios = supabase.table("usuarios").select("time_id").eq("Divisão", f"Divisão {divisao}").execute().data
        time_ids = list({u["time_id"] for u in usuarios if u.get("time_id")})
        if not time_ids:
            return {}
        res = supabase.table("times").select("id", "nome", "logo", "tecnico").in_("id", time_ids).execute()
        return {
            t["id"]: {
                "nome": t["nome"],
                "logo": t.get("logo", ""),
                "tecnico": t.get("tecnico", "")
            } for t in res.data
        }
    except:
        return {}

def buscar_posicao_vitorias(time_id):
    res = supabase.table("classificacao").select("id_time", "vitorias").order("pontos", desc=True).execute()
    ids = [t["id_time"] for t in res.data]
    posicao = ids.index(time_id) + 1 if time_id in ids else 20
    vitorias = next((t["vitorias"] for t in res.data if t["id_time"] == time_id), 0)
    return posicao, vitorias

# [continua no próximo comentário...]
# [continuação do código anterior...]

# 🔄 Processar rodadas
dados_rodadas = buscar_resultados(numero_temporada, numero_divisao)
nomes_times = obter_nomes_times(numero_divisao)

tabela = {}

for rodada in dados_rodadas:
    for jogo in rodada.get("jogos", []):
        mandante_id = jogo.get("mandante")
        visitante_id = jogo.get("visitante")
        gols_mandante = jogo.get("gols_mandante")
        gols_visitante = jogo.get("gols_visitante")

        if mandante_id not in nomes_times or visitante_id not in nomes_times:
            continue

        if gols_mandante is None or gols_visitante is None:
            continue

        for time_id in [mandante_id, visitante_id]:
            if time_id not in tabela:
                tabela[time_id] = {
                    "id": time_id,
                    "nome": nomes_times[time_id]["nome"],
                    "logo": nomes_times[time_id]["logo"],
                    "p": 0, "j": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0, "sg": 0
                }

        tabela[mandante_id]["j"] += 1
        tabela[visitante_id]["j"] += 1
        tabela[mandante_id]["gp"] += gols_mandante
        tabela[mandante_id]["gc"] += gols_visitante
        tabela[visitante_id]["gp"] += gols_visitante
        tabela[visitante_id]["gc"] += gols_mandante

        if gols_mandante > gols_visitante:
            tabela[mandante_id]["v"] += 1
            tabela[visitante_id]["d"] += 1
            tabela[mandante_id]["p"] += 3
        elif gols_mandante < gols_visitante:
            tabela[visitante_id]["v"] += 1
            tabela[mandante_id]["d"] += 1
            tabela[visitante_id]["p"] += 3
        else:
            tabela[mandante_id]["e"] += 1
            tabela[visitante_id]["e"] += 1
            tabela[mandante_id]["p"] += 1
            tabela[visitante_id]["p"] += 1

for time in tabela.values():
    time["sg"] = time["gp"] - time["gc"]

classificacao = sorted(tabela.values(), key=lambda x: (-x["p"], -x["sg"], -x["gp"], x["nome"]))

st.markdown("### 📋 Classificação Atual")

df_classificacao = pd.DataFrame(classificacao)
df_classificacao.index = range(1, len(df_classificacao) + 1)

df_classificacao_exibicao = df_classificacao[["nome", "p", "j", "v", "e", "d", "gp", "gc", "sg"]]
st.dataframe(df_classificacao_exibicao, use_container_width=True)

# 🔚 Rodapé
st.markdown("---")
st.markdown("🧠 Powered by LigaFut · Desenvolvido por Tinti400")

