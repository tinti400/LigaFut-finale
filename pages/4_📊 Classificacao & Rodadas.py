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

    # ➖ Aplicar punições de pontos (permitindo pontos negativos)
    try:
        res_punicoes = supabase.table("punicoes").select("id_time, pontos_retirados").execute()
        puni_map = {}
        for p in res_punicoes.data:
            tid = p["id_time"]
            puni_map[tid] = puni_map.get(tid, 0) + p["pontos_retirados"]

        for tid in tabela:
            if tid in puni_map:
                tabela[tid]["pontos"] -= puni_map[tid]
    except Exception as e:
        st.error(f"Erro ao aplicar punições: {e}")

    return sorted(tabela.items(), key=lambda x: (x[1]["pontos"], x[1]["sg"], x[1]["gp"]), reverse=True)

# 🔄 Dados
rodadas = buscar_resultados()
times_map = obter_nomes_times()
classificacao = calcular_classificacao(rodadas, times_map)

# 📊 Tabela
dados = []
for i, (tid, t) in enumerate(classificacao, start=1):
    escudo = f"<img src='{t['logo']}' width='25' style='vertical-align: middle; margin-right: 6px;'>"
    nome = t["nome"].strip().capitalize()
    dados.append({
        "Posição": i,
        "Time": f"{escudo}{nome}",
        "Pontos": t["pontos"],
        "Jogos": t["v"] + t["e"] + t["d"],
        "Vitórias": t["v"],
        "Empates": t["e"],
        "Derrotas": t["d"],
        "Gols Pró": t["gp"],
        "Gols Contra": t["gc"],
        "Saldo de Gols": t["sg"]
    })

# 📋 Estilização da tabela
def aplicar_estilo_linha(df):
    html = "<style>td, th { text-align: center; vertical-align: middle; }</style><table border='1' class='dataframe' style='width: 100%; border-collapse: collapse;'>"
    html += "<thead><tr>"
    for col in df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"

    total = len(df)
    for i, row in df.iterrows():
        cor = "#d4edda" if i < 4 else "#f8d7da" if i >= total - 2 else ""
        html += f"<tr style='background-color: {cor};'>" if cor else "<tr>"
        for val in row:
            html += f"<td>{val}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

if dados:
    df = pd.DataFrame(dados)
    st.markdown(aplicar_estilo_linha(df), unsafe_allow_html=True)
else:
    st.info("Sem dados suficientes para exibir a classificação.")

# 🔧 Admin: reset rodadas
if eh_admin:
    st.markdown("---")
    st.subheader("🔧 Ações administrativas")
    if st.button("🧹 Resetar Tabela de Classificação (apagar rodadas)"):
        try:
            res = supabase.table(nome_tabela_rodadas).select("id").execute()
            for doc in res.data:
                supabase.table(nome_tabela_rodadas).delete().eq("id", doc["id"]).execute()
            st.success("✅ Rodadas da divisão apagadas com sucesso.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao resetar rodadas: {e}")

# 📅 Rodadas - visualização por página
st.markdown("---")
st.subheader("📅 Rodadas da Temporada")

if not rodadas:
    st.info("Nenhuma rodada encontrada para esta divisão.")
else:
    rodadas_ordenadas = sorted(rodadas, key=lambda r: r.get("numero", 0))
    lista_rodadas = [f"Rodada {r.get('numero', '?')}" for r in rodadas_ordenadas]
    selecao = st.selectbox("🔁 Selecione a rodada para visualizar", lista_rodadas)

    rodada_escolhida = rodadas_ordenadas[lista_rodadas.index(selecao)]
    st.markdown(f"### 🕹️ {selecao}")

    for jogo in rodada_escolhida.get("jogos", []):
        m = jogo.get("mandante")
        v = jogo.get("visitante")
        gm = jogo.get("gols_mandante")
        gv = jogo.get("gols_visitante")

        m_info = times_map.get(m, {"nome": "?", "logo": ""})
        v_info = times_map.get(v, {"nome": "?", "logo": ""})

        escudo_m = f"<img src='{m_info['logo']}' width='25' style='vertical-align: middle; margin-right: 5px;'>"
        escudo_v = f"<img src='{v_info['logo']}' width='25' style='vertical-align: middle; margin-left: 5px;'>"

        nome_m = m_info["nome"]
        nome_v = v_info["nome"]
        placar = f"{gm} x {gv}" if gm is not None and gv is not None else "vs"

        st.markdown(f"<div style='font-size: 16px;'>"
                    f"{escudo_m}<b>{nome_m}</b> {placar} <b>{nome_v}</b>{escudo_v}"
                    f"</div>", unsafe_allow_html=True)

    st.markdown("---")

# 🏁 Checagem de fim de temporada e geração de histórico
def todos_os_jogos_preenchidos(rodadas):
    for rodada in rodadas:
        for jogo in rodada.get("jogos", []):
            if jogo.get("gols_mandante") is None or jogo.get("gols_visitante") is None:
                return False
    return True

if todos_os_jogos_preenchidos(rodadas):
    st.success("🏁 Temporada concluída! Gerando histórico...")

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
        ja_salvo = supabase.table("historico_temporadas").select("*").eq("divisao", divisao).eq("data_fim", temporada_data["data_fim"]).execute()
        if not ja_salvo.data:
            supabase.table("historico_temporadas").insert(temporada_data).execute()
    except Exception as e:
        st.error(f"Erro ao salvar histórico da temporada: {e}")

    st.markdown("## 🏅 Resumo da Temporada")
    st.markdown(f"**🏆 Campeão:** `{campeao}`")
    st.markdown(f"**🔥 Melhor Ataque:** `{melhor_ataque}`")
    st.markdown(f"**🧱 Melhor Defesa:** `{melhor_defesa}`")
