# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Classificação", page_icon="📊", layout="centered")
st.markdown("## 🏆 Tabela de Classificação")
st.markdown(f"🗓️ Atualizada em: `{datetime.now().strftime('%d/%m/%Y %H:%M')}`")

# 🔒 Login
if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

# 📧 Verifica se é admin
email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

# 🔹 Divisão
divisao = st.selectbox("Selecione a divisão", ["Divisão 1", "Divisão 2"])
numero_divisao = divisao.split()[-1]
nome_tabela_rodadas = f"rodadas_divisao_{numero_divisao}"

# 📅 Buscar rodadas
def buscar_resultados():
    try:
        res = supabase.table(nome_tabela_rodadas).select("*").order("numero").execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"Erro ao buscar rodadas: {e}")
        return []

# 👥 Buscar times com base nos usuários
def obter_nomes_times():
    try:
        usuarios = supabase.table("usuarios").select("time_id").eq("Divisão", divisao).execute().data
        time_ids = list({u["time_id"] for u in usuarios if u.get("time_id")})
        if not time_ids:
            return {}
        res = supabase.table("times").select("id", "nome", "logo").in_("id", time_ids).execute()
        return {t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")} for t in res.data}
    except Exception as e:
        st.error(f"Erro ao buscar nomes dos times: {e}")
        return {}

# 🧠 Classificação com punições
def calcular_classificacao(rodadas, times_map):
    tabela = {}

    for rodada in rodadas:
        for jogo in rodada.get("jogos", []):
            m = jogo.get("mandante")
            v = jogo.get("visitante")
            gm = jogo.get("gols_mandante")
            gv = jogo.get("gols_visitante")
            if None in [m, v, gm, gv]:
                continue
            try:
                gm, gv = int(gm), int(gv)
            except:
                continue

            for t in (m, v):
                if t not in tabela:
                    tabela[t] = {
                        "nome": times_map.get(t, {}).get("nome", "Desconhecido"),
                        "logo": times_map.get(t, {}).get("logo", ""),
                        "pontos": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0, "sg": 0
                    }

            tabela[m]["gp"] += gm
            tabela[m]["gc"] += gv
            tabela[m]["sg"] += gm - gv
            tabela[v]["gp"] += gv
            tabela[v]["gc"] += gm
            tabela[v]["sg"] += gv - gm

            if gm > gv:
                tabela[m]["pontos"] += 3
                tabela[m]["v"] += 1
                tabela[v]["d"] += 1
            elif gm < gv:
                tabela[v]["pontos"] += 3
                tabela[v]["v"] += 1
                tabela[m]["d"] += 1
            else:
                tabela[m]["pontos"] += 1
                tabela[v]["pontos"] += 1
                tabela[m]["e"] += 1
                tabela[v]["e"] += 1

    for tid in times_map:
        if tid not in tabela:
            tabela[tid] = {
                "nome": times_map[tid]["nome"],
                "logo": times_map[tid]["logo"],
                "pontos": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0, "sg": 0
            }

    # ➖ Aplicar punições de pontos
    try:
        res_punicoes = supabase.table("punicoes").select("id_time, pontos_retirados").execute()
        puni_map = {}
        for p in res_punicoes.data:
            tid = p["id_time"]
            puni_map[tid] = puni_map.get(tid, 0) + p["pontos_retirados"]

        for tid in tabela:
            if tid in puni_map:
                tabela[tid]["pontos"] = max(0, tabela[tid]["pontos"] - puni_map[tid])
    except Exception as e:
        st.error(f"Erro ao aplicar punições: {e}")

    return sorted(tabela.items(), key=lambda x: (x[1]["pontos"], x[1]["sg"], x[1]["gp"]), reverse=True)

# 🔄 Dados
rodadas = buscar_resultados()
times_map = obter_nomes_times()
classificacao = calcular_classificacao(rodadas, times_map)

# 📊 Tabela
# (mantém igual)

# 🏁 Checagem e botão
if todos_os_jogos_preenchidos(rodadas):
    st.success("🏁 Temporada concluída!")
    if st.button("🔄 Avançar para a próxima temporada"):
        campeao = classificacao[0][1]["nome"]
        melhor_ataque = max(classificacao, key=lambda x: x[1]["gp"])[1]["nome"]
        melhor_defesa = min(classificacao, key=lambda x: x[1]["gc"])[1]["nome"]

        temporada_data = {
            "data_fim": datetime.now().isoformat(),
            "divisao": divisao,
            "campeao": campeao,
            "melhor_ataque": melhor_ataque,
            "melhor_defesa": melhor_defesa
        }
        try:
            supabase.table("historico_temporadas").insert(temporada_data).execute()
        except:
            pass

        # Atualizar promovidos e rebaixados
        try:
            if divisao == "Divisão 1":
                rebaixados = [classificacao[-1][0], classificacao[-2][0]]
                for tid in rebaixados:
                    supabase.table("usuarios").update({"Divisão": "Divisão 2"}).eq("time_id", tid).execute()
            elif divisao == "Divisão 2":
                promovidos = [classificacao[0][0], classificacao[1][0]]
                for tid in promovidos:
                    supabase.table("usuarios").update({"Divisão": "Divisão 1"}).eq("time_id", tid).execute()

            st.success("✅ Divisões atualizadas com sucesso!")
        except Exception as e:
            st.error(f"Erro ao atualizar divisões: {e}")

