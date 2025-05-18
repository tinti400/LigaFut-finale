# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime

# ✅ Verificação de login
def verificar_login():
    if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()
    if "id_time" not in st.session_state or "nome_time" not in st.session_state:
        st.warning("Informações do time não encontradas na sessão.")
        st.stop()

# 💰 Registrar movimentação financeira
def registrar_movimentacao(supabase, id_time, jogador, categoria, tipo, valor):
    try:
        movimentacao = {
            "id_time": id_time,
            "jogador": jogador,
            "categoria": categoria,
            "tipo": tipo,
            "valor": valor,
            "data": datetime.utcnow().isoformat()
        }
        supabase.table("movimentacoes").insert(movimentacao).execute()
    except Exception as e:
        st.error(f"❌ Erro ao registrar movimentação financeira: {e}")

# 📊 Calcular classificação com base nas rodadas e times
def calcular_classificacao(rodadas, times_map):
    tabela = {tid: {"nome": nome, "pontos": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0, "sg": 0}
              for tid, nome in times_map.items()}

    for rodada in rodadas:
        for jogo in rodada.get("jogos", []):
            m, v = jogo.get("mandante"), jogo.get("visitante")
            gm, gv = jogo.get("gols_mandante"), jogo.get("gols_visitante")
            if None in [m, v, gm, gv] or "FOLGA" in [m, v]:
                continue
            try:
                gm = int(gm)
                gv = int(gv)
            except:
                continue

            for t in (m, v):
                if t not in tabela:
                    tabela[t] = {"nome": times_map.get(t, "Desconhecido"), "pontos": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0, "sg": 0}

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

    return sorted(tabela.items(), key=lambda x: (x[1]["pontos"], x[1]["sg"], x[1]["gp"]), reverse=True)

# 🔁 Atualiza a classificação no banco Supabase
def atualizar_classificacao(supabase, divisao):
    tabela_rodadas = f"rodadas_divisao_{divisao}"
    tabela_classificacao = f"classificacao_divisao_{divisao}"

    rodadas = supabase.table(tabela_rodadas).select("*").execute().data
    times = supabase.table("times").select("id", "nome").execute().data
    times_map_all = {t["id"]: t["nome"] for t in times if t.get("id") and t.get("nome")}

    usuarios_divisao = supabase.table("usuarios").select("time_id").eq("Divisao", f"Divisão {divisao}").execute().data
    time_ids_validos = [u["time_id"] for u in usuarios_divisao if u.get("time_id") in times_map_all]
    times_map = {tid: times_map_all[tid] for tid in time_ids_validos}

    classif = calcular_classificacao(rodadas, times_map)

    dados_classificacao = []
    for tid, t in classif:
        dados_classificacao.append({
            "id_time": tid,
            "nome": t["nome"],
            "pontos": t["pontos"],
            "v": t["v"],
            "e": t["e"],
            "d": t["d"],
            "gp": t["gp"],
            "gc": t["gc"],
            "sg": t["sg"]
        })

    supabase.table(tabela_classificacao).delete().neq("id_time", "").execute()
    supabase.table(tabela_classificacao).insert(dados_classificacao).execute()
    return classif

# 🔽 Calcular promoções, rebaixamentos e playoff
def calcular_movimentacao_divisoes(classif_div1, classif_div2):
    rebaixados = classif_div1[-2:]
    playoff_div1 = classif_div1[-3]
    promovidos = classif_div2[:2]
    playoff_div2 = classif_div2[2]
    return promovidos, rebaixados, (playoff_div1, playoff_div2)

# ⚙️ Atualizar divisões após resultado do playoff
def aplicar_movimentacao_divisoes(supabase, vencedor_id, perdedor_id):
    try:
        supabase.table("usuarios").update({"Divisao": "Divisão 1"}).eq("time_id", vencedor_id).execute()
        supabase.table("usuarios").update({"Divisao": "Divisão 2"}).eq("time_id", perdedor_id).execute()
        st.success("✅ Divisões atualizadas com base no resultado do playoff!")
    except Exception as e:
        st.error(f"Erro ao aplicar movimentação: {e}")