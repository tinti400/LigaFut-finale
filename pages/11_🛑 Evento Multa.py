# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao

st.set_page_config(page_title="🛑 Evento de Multa - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
usuario = st.session_state["usuario"]

# ⚙️ ID da configuração do evento
ID_CONFIG = "evento_multa"

# 🔍 Busca configurações
config = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute().data
if not config:
    st.warning("Evento de multa ainda não foi iniciado.")
    st.stop()
config = config[0]

ativo = config.get("ativo", False)
fase = config.get("fase", "")
ordem = config.get("ordem", [])
vez = config.get("vez", 0)
bloqueios = config.get("bloqueios", {})
roubos = config.get("roubos", {})
concluidos = config.get("concluidos", [])
ja_perderam = config.get("ja_perderam", {})
finalizado = config.get("finalizado", False)

# Verifica se admin
admin = supabase.table("usuarios").select("administrador").eq("usuario", usuario).execute().data
eh_admin = admin[0]["administrador"] if admin else False

# Cabeçalho
st.title("🛑 Evento de Multa - LigaFut")
st.markdown("---")

# Admin - iniciar evento
if eh_admin and not ativo:
    if st.button("🚀 Iniciar Evento de Multa"):
        times = supabase.table("times").select("id").execute().data
        ordem = [t["id"] for t in times]
        import random
        random.shuffle(ordem)
        supabase.table("configuracoes").upsert({
            "id": ID_CONFIG,
            "ativo": True,
            "fase": "bloqueio",
            "ordem": ordem,
            "vez": 0,
            "bloqueios": {},
            "roubos": {},
            "concluidos": [],
            "ja_perderam": {},
            "finalizado": False
        }).execute()
        st.success("Evento de multa iniciado.")
        st.rerun()

# Admin - encerrar evento
if eh_admin and ativo:
    if st.button("🛑 Encerrar Evento"):
        supabase.table("configuracoes").update({"ativo": False, "finalizado": True}).eq("id", ID_CONFIG).execute()
        st.success("Evento encerrado.")
        st.rerun()

# Evento Ativo
if ativo:

    st.success(f"Evento ativo - Fase: {fase.upper()}")

    # 🔐 Bloqueio
    if fase == "bloqueio":
        st.subheader("⛔ Bloqueie até 4 jogadores do seu elenco")

        elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data
        nomes_bloqueados = [f"{j['nome']} - {j['posicao']}" for j in bloqueios.get(id_time, [])]
        opcoes = [f"{j['nome']} - {j['posicao']}" for j in elenco if f"{j['nome']} - {j['posicao']}" not in nomes_bloqueados]

        escolhidos = st.multiselect("Escolha os jogadores:", opcoes, default=nomes_bloqueados, max_selections=4)

        if st.button("💾 Salvar bloqueios"):
            novos = [j for j in elenco if f"{j['nome']} - {j['posicao']}" in escolhidos]
            bloqueios[id_time] = novos
            supabase.table("configuracoes").update({"bloqueios": bloqueios}).eq("id", ID_CONFIG).execute()
            st.success("Jogadores bloqueados com sucesso.")
            st.rerun()

        if eh_admin:
            if st.button("➡️ Avançar para fase de ação"):
                supabase.table("configuracoes").update({"fase": "acao"}).eq("id", ID_CONFIG).execute()
                st.rerun()

    # 🎯 Fase de Ação
    elif fase == "acao":

        st.subheader("📋 Ordem dos Times")
        for i, tid in enumerate(ordem):
            nome = supabase.table("times").select("nome").eq("id", tid).execute().data[0]["nome"]
            if tid in concluidos:
                st.markdown(f"✅ {nome}")
            elif i == vez:
                st.markdown(f"➡️ {nome} (vez atual)")
            else:
                st.markdown(f"🔹 {nome}")

        if vez < len(ordem):
            id_vez = ordem[vez]
            if id_vez == id_time:

                st.success("🏆 É sua vez de realizar as multas!")

                times = supabase.table("times").select("id", "nome").execute().data
                for time in times:
                    tid = time["id"]
                    if tid == id_time or ja_perderam.get(tid, 0) >= 4:
                        continue

                    elenco_adversario = supabase.table("elenco").select("*").eq("id_time", tid).execute().data
                    if not elenco_adversario:
                        continue

                    with st.expander(f"🎽 {time['nome']}"):
                        for j in elenco_adversario:
                            nome_jogador = j.get("nome")
                            posicao = j.get("posicao")
                            valor = j.get("valor")

                            bloqueado = any(j['nome'] == b['nome'] for b in bloqueios.get(tid, []))
                            ja_roubado = any(j['nome'] == r.get("nome") and r.get("de") == tid for r in roubos.get(id_time, []))

                            if ja_roubado or bloqueado:
                                st.markdown(f"🔒 {nome_jogador} - {posicao}")
                                continue

                            if st.button(f"⚡ Multar {nome_jogador} (R$ {valor:,.0f})", key=f"{tid}_{nome_jogador}"):
                                # 1. Transferir jogador
                                supabase.table("elenco").delete().eq("id_time", tid).eq("nome", nome_jogador).execute()
                                supabase.table("elenco").insert({
                                    "id_time": id_time,
                                    "nome": nome_jogador,
                                    "posicao": posicao,
                                    "overall": j.get("overall"),
                                    "valor": valor
                                }).execute()

                                # 2. Ajustar saldos
                                time_atual = supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]
                                time_dono = supabase.table("times").select("saldo").eq("id", tid).execute().data[0]

                                novo_saldo_atual = time_atual["saldo"] - valor
                                novo_saldo_dono = time_dono["saldo"] + valor

                                supabase.table("times").update({"saldo": novo_saldo_atual}).eq("id", id_time).execute()
                                supabase.table("times").update({"saldo": novo_saldo_dono}).eq("id", tid).execute()

                                # 3. Registra movimentações
                                registrar_movimentacao(id_time, f"Compra por multa: {nome_jogador}", -valor)
                                registrar_movimentacao(tid, f"Venda por multa: {nome_jogador}", valor)

                                # 4. Registra no evento
                                novo = roubos.get(id_time, [])
                                novo.append({"nome": nome_jogador, "posicao": posicao, "valor": valor, "de": tid})
                                roubos[id_time] = novo
                                ja_perderam[tid] = ja_perderam.get(tid, 0) + 1

                                supabase.table("configuracoes").update({
                                    "roubos": roubos,
                                    "ja_perderam": ja_perderam
                                }).eq("id", ID_CONFIG).execute()

                                st.success(f"{nome_jogador} comprado com sucesso!")
                                st.rerun()

                if len(roubos.get(id_time, [])) >= 5:
                    st.info("Limite de 5 multas atingido.")

                if st.button("✅ Finalizar minha vez"):
                    supabase.table("configuracoes").update({
                        "concluidos": concluidos + [id_time],
                        "vez": vez + 1
                    }).eq("id", ID_CONFIG).execute()
                    st.success("Vez finalizada.")
                    st.rerun()

            elif eh_admin:
                if st.button("⏭️ Pular vez"):
                    supabase.table("configuracoes").update({"vez": vez + 1}).eq("id", ID_CONFIG).execute()
                    st.rerun()

    elif finalizado:
        st.success("🏁 Evento finalizado!")
        st.markdown("### 📊 Resumo das transações:")
        for tid, acoes in roubos.items():
            nome_time = supabase.table("times").select("nome").eq("id", tid).execute().data[0]["nome"]
            st.markdown(f"#### 🟢 {nome_time}")
            for j in acoes:
                nome_dono = supabase.table("times").select("nome").eq("id", j['de']).execute().data[0]["nome"]
                st.markdown(f"- {j['nome']} ({j['posicao']}) comprado de {nome_dono} por R$ {j['valor']:,.0f}")

else:
    st.warning("Evento de multa não está ativo no momento.")

