# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd
from utils import registrar_movimentacao

st.set_page_config(page_title="Evento de Multa - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
usuario = st.session_state["usuario"]

st.title("🛑 Evento de Multa - LigaFut")

# ⚙️ Configuração fixa
ID_CONFIG = "evento_multa"

# 🔎 Verifica se é admin
admin_check = supabase.table("usuarios").select("administrador").eq("usuario", usuario).execute()
eh_admin = admin_check.data[0]["administrador"] if admin_check.data else False

# 🔄 Busca configuração
dados_config = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute().data
config = dados_config[0] if dados_config else {}

ativo = config.get("ativo", False)
fase = config.get("fase", "bloqueio")
ordem = config.get("ordem", [])
vez = int(config.get("vez", 0))
bloqueios = config.get("bloqueios", {})
ja_perderam = config.get("ja_perderam", {})
roubos = config.get("roubos", {})
concluidos = config.get("concluidos", [])
finalizado = config.get("finalizado", False)

# -------------------- ADMIN --------------------
if eh_admin:
    st.subheader("👑 Painel do Administrador")
    if not ativo:
        if st.button("🚨 Iniciar Evento de Multa"):
            todos_times = supabase.table("times").select("id").execute().data
            nova_ordem = [t["id"] for t in todos_times]
            random.shuffle(nova_ordem)

            nova_config = {
                "id": ID_CONFIG,
                "ativo": True,
                "fase": "bloqueio",
                "ordem": nova_ordem,
                "vez": 0,
                "bloqueios": {},
                "ja_perderam": {},
                "roubos": {},
                "concluidos": [],
                "finalizado": False,
                "inicio": datetime.utcnow().isoformat()
            }

            supabase.table("configuracoes").upsert(nova_config).execute()
            st.success("Evento de Multa iniciado!")
            st.rerun()

    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏭️ Pular Vez"):
                supabase.table("configuracoes").update({"vez": vez + 1}).eq("id", ID_CONFIG).execute()
                st.rerun()
        with col2:
            if st.button("✅ Encerrar Evento"):
                supabase.table("configuracoes").update({"ativo": False, "finalizado": True}).eq("id", ID_CONFIG).execute()
                st.success("Evento encerrado.")
                st.rerun()

# -------------------- BLOQUEIO --------------------
if ativo and fase == "bloqueio":
    st.subheader("🔒 Bloqueie até 4 jogadores")
    elenco_data = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data
    nomes_bloqueados = [f"{j['nome']} - {j['posicao']}" for j in bloqueios.get(id_time, [])]

    jogadores_disponiveis = [f"{j['nome']} - {j['posicao']}" for j in elenco_data if f"{j['nome']} - {j['posicao']}" not in nomes_bloqueados]
    selecionados = st.multiselect("Escolha até 4 jogadores:", jogadores_disponiveis, default=nomes_bloqueados, max_selections=4)

    if st.button("💾 Salvar Bloqueios"):
        novos_bloqueios = [j for j in elenco_data if f"{j['nome']} - {j['posicao']}" in selecionados]
        bloqueios[id_time] = novos_bloqueios
        supabase.table("configuracoes").update({"bloqueios": bloqueios}).eq("id", ID_CONFIG).execute()
        st.success("Bloqueios salvos!")
        st.rerun()

    if eh_admin:
        if st.button("➡️ Avançar para Ação"):
            supabase.table("configuracoes").update({"fase": "acao"}).eq("id", ID_CONFIG).execute()
            st.rerun()

# -------------------- AÇÃO --------------------
elif ativo and fase == "acao":
    st.subheader("🎯 É hora de multar!")
    if vez < len(ordem):
        id_atual = ordem[vez]
        nome_vez = supabase.table("times").select("nome").eq("id", id_atual).execute().data[0]["nome"]
        st.info(f"🕐 Vez atual: {nome_vez}")

        if id_time == id_atual:
            st.success("🎯 É sua vez de multar até 5 jogadores!")

            times = supabase.table("times").select("id", "nome", "saldo").execute().data
            saldo_data = supabase.table("times").select("saldo").eq("id", id_time).execute().data
            saldo = saldo_data[0]["saldo"] if saldo_data else 0

            for adversario in times:
                if adversario["id"] == id_time or ja_perderam.get(adversario["id"], 0) >= 4:
                    continue

                elenco_adv = supabase.table("elenco").select("*").eq("id_time", adversario["id"]).execute().data
                if not elenco_adv:
                    continue

                with st.expander(f"📂 {adversario['nome']}"):
                    for j in elenco_adv:
                        bloqueado = any(b["nome"] == j["nome"] for b in bloqueios.get(adversario["id"], []))
                        ja_roubado = any(r["nome"] == j["nome"] and r["de"] == adversario["id"] for lst in roubos.values() for r in lst)

                        if bloqueado or ja_roubado:
                            st.markdown(f"🔒 {j['nome']} - {j['posicao']} (R$ {j['valor']:,.0f})")
                        else:
                            if st.button(f"💰 Multar {j['nome']} (R$ {j['valor']:,.0f})", key=f"{adversario['id']}_{j['nome']}"):
                                if saldo < j["valor"]:
                                    st.error("💸 Saldo insuficiente.")
                                else:
                                    # Transfere jogador
                                    supabase.table("elenco").delete().eq("id_time", adversario["id"]).eq("nome", j["nome"]).execute()
                                    supabase.table("elenco").insert({
                                        "id_time": id_time,
                                        "nome": j["nome"],
                                        "posicao": j["posicao"],
                                        "overall": j["overall"],
                                        "valor": j["valor"]
                                    }).execute()

                                    # Atualiza saldo de quem comprou e quem perdeu
                                    novo_saldo_comprador = saldo - j["valor"]
                                    saldo_vendedor = adversario["saldo"] + j["valor"]
                                    supabase.table("times").update({"saldo": novo_saldo_comprador}).eq("id", id_time).execute()
                                    supabase.table("times").update({"saldo": saldo_vendedor}).eq("id", adversario["id"]).execute()

                                    registrar_movimentacao(id_time, f"Multa por {j['nome']}", -j["valor"])
                                    registrar_movimentacao(adversario["id"], f"Jogador {j['nome']} vendido via multa", j["valor"])

                                    # Atualiza estrutura
                                    ja_perderam[adversario["id"]] = ja_perderam.get(adversario["id"], 0) + 1
                                    roubos.setdefault(id_time, []).append({
                                        "nome": j["nome"],
                                        "posicao": j["posicao"],
                                        "valor": j["valor"],
                                        "de": adversario["id"]
                                    })

                                    supabase.table("configuracoes").update({
                                        "ja_perderam": ja_perderam,
                                        "roubos": roubos
                                    }).eq("id", ID_CONFIG).execute()

                                    st.success(f"{j['nome']} multado com sucesso!")
                                    st.rerun()

            if len(roubos.get(id_time, [])) >= 5:
                st.info("🔚 Você já multou 5 jogadores.")

            if st.button("✅ Finalizar minha vez"):
                supabase.table("configuracoes").update({
                    "vez": vez + 1,
                    "concluidos": concluidos + [id_time]
                }).eq("id", ID_CONFIG).execute()
                st.rerun()

# -------------------- FINALIZADO --------------------
elif finalizado:
    st.success("✅ Evento de Multa finalizado!")
    resumo = []
    for tid, acoes in roubos.items():
        nome_time_comprador = supabase.table("times").select("nome").eq("id", tid).execute().data[0]["nome"]
        for j in acoes:
            nome_time_vendido = supabase.table("times").select("nome").eq("id", j["de"]).execute().data[0]["nome"]
            resumo.append({
                "Time": nome_time_comprador,
                "Jogador": j["nome"],
                "Posição": j["posicao"],
                "De": nome_time_vendido,
                "Valor": f"R$ {j['valor']:,.0f}"
            })

    df = pd.DataFrame(resumo)
    st.dataframe(df, use_container_width=True)

else:
    st.warning("⚠️ Evento de Multa ainda não foi iniciado.")
