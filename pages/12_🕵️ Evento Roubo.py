# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
import random

st.set_page_config(page_title="🕵️ Evento Roubo - Fase 1", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica se usuário é admin
email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("admins").select("*").eq("email", email_usuario).execute()
is_admin = len(res_admin.data) > 0

st.title("🕵️ Evento de Roubo - Fase 1: Regras e Sorteio")

# ✅ Apenas admins podem configurar
if is_admin:
    st.subheader("🔧 Definir Regras do Evento")

    col1, col2 = st.columns(2)
    with col1:
        max_bloqueios = st.number_input("🔒 Jogadores que cada time pode proteger:", min_value=1, max_value=10, value=3)
    with col2:
        max_perdas = st.number_input("❌ Limite de jogadores que um time pode perder:", min_value=1, max_value=10, value=4)

    if st.button("🎲 Sortear Ordem dos Times"):
        res_times = supabase.table("times").select("id", "nome").execute()
        times = res_times.data
        ordem = random.sample(times, len(times))
        ordem_formatada = [{"id": t["id"], "nome": t["nome"]} for t in ordem]

        supabase.table("configuracoes").upsert({
            "id": "evento_roubo",
            "tipo": "evento_roubo",
            "fase": 1,
            "ordem_times": ordem_formatada,
            "max_bloqueios": max_bloqueios,
            "max_perdas": max_perdas,
            "indice_atual": 0,
            "perdas": {},
            "inicio": datetime.now().isoformat(),
            "finalizado": False
        }).execute()

        st.success("✅ Ordem dos times sorteada com sucesso!")

evento = supabase.table("configuracoes").select("*").eq("id", "evento_roubo").execute()
if evento.data:
    dados = evento.data[0]
    st.markdown("## 📋 Ordem dos Times para o Evento")
    for i, time in enumerate(dados.get("ordem_times", [])):
        st.markdown(f"**{i+1}. {time['nome']}**")
else:
    st.info("Aguardando o início do evento pelo administrador.")
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid

st.set_page_config(page_title="🕵️ Evento Roubo - Fase 2", layout="wide")

url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

usuario = st.session_state.get("usuario", "")
id_time = st.session_state.get("id_time", "")
nome_time = st.session_state.get("nome_time", "")

res_evento = supabase.table("configuracoes").select("*").eq("id", "evento_roubo").execute()
evento = res_evento.data[0] if res_evento.data else {}

if not evento or evento.get("fase") != 2:
    st.warning("⏳ Aguardando admin iniciar a fase 2.")
    st.stop()

ordem = evento.get("ordem_times", [])
indice_atual = evento.get("indice_atual", 0)
time_vez = ordem[indice_atual]["id"]
nome_vez = ordem[indice_atual]["nome"]

res_admin = supabase.table("admins").select("email").eq("email", usuario).execute()
is_admin = len(res_admin.data) > 0

if id_time != time_vez:
    st.warning(f"⏳ Aguarde sua vez. Agora é a vez de **{nome_vez}**.")
    if is_admin and st.button("⏭️ Pular vez"):
        supabase.table("configuracoes").update({"indice_atual": indice_atual + 1}).eq("id", "evento_roubo").execute()
        st.rerun()
    st.stop()

st.title(f"🕵️ Sua vez de roubar! - {nome_vez}")

res_times = supabase.table("times").select("id", "nome").neq("id", id_time).execute()
times_disponiveis = res_times.data
time_alvo = st.selectbox("🎯 Escolha um time para visualizar o elenco:", options=times_disponiveis, format_func=lambda x: x["nome"])

if time_alvo:
    id_alvo = time_alvo["id"]
    nome_alvo = time_alvo["nome"]
    perdas = evento.get("perdas", {})

    if perdas.get(id_alvo, 0) >= evento["max_perdas"]:
        st.warning(f"❌ O time {nome_alvo} já atingiu o limite de perdas.")
        st.stop()

    res_bloqueados = supabase.table("jogadores_bloqueados").select("*").eq("id_time", id_alvo).execute()
    bloqueados = [j["id_jogador"] for j in res_bloqueados.data]

    res_elenco = supabase.table("elencos").select("*").eq("id_time", id_alvo).execute()
    elenco = [j for j in res_elenco.data if j["id"] not in bloqueados]

    st.subheader(f"👥 Elenco de {nome_alvo} (bloqueados ocultos)")

    for jogador in elenco:
        nome = jogador["nome"]
        pos = jogador["posição"]
        overall = jogador["overall"]
        valor = jogador["valor"]
        preco = int(valor * 0.5)

        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        with col1:
            st.markdown(f"**{nome}**")
        with col2:
            st.markdown(f"{pos} | OVR {overall}")
        with col3:
            st.markdown(f"💰 R$ {preco:,}".replace(",", "."))
        with col4:
            if st.button("💸 Roubar", key=jogador["id"]):
                saldo_resp = supabase.table("times").select("saldo").eq("id", id_time).execute()
                saldo_atual = saldo_resp.data[0]["saldo"]
                if saldo_atual < preco:
                    st.error("❌ Saldo insuficiente.")
                    st.stop()

                novo_saldo = saldo_atual - preco
                supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                supabase.table("elencos").delete().eq("id", jogador["id"]).execute()
                jogador["id_time"] = id_time
                jogador["id"] = str(uuid.uuid4())
                supabase.table("elencos").insert(jogador).execute()

                supabase.table("bid").insert({
                    "id": str(uuid.uuid4()),
                    "id_jogador": jogador["id"],
                    "nome": jogador["nome"],
                    "valor": preco,
                    "origem": id_alvo,
                    "destino": id_time,
                    "data": datetime.now().isoformat()
                }).execute()

                supabase.table("movimentacoes_financeiras").insert({
                    "id": str(uuid.uuid4()),
                    "id_time": id_time,
                    "tipo": "compra_roubo",
                    "descricao": f"Roubo de {jogador['nome']} de {nome_alvo}",
                    "valor": -preco,
                    "data": datetime.now().isoformat()
                }).execute()

                perdas[id_alvo] = perdas.get(id_alvo, 0) + 1
                supabase.table("configuracoes").update({"perdas": perdas}).eq("id", "evento_roubo").execute()

                st.success(f"✅ Você roubou {jogador['nome']} por R$ {preco:,}!")
                st.rerun()
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="📄 Resumo - Evento Roubo", layout="wide")

url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

usuario = st.session_state.get("usuario", "")
id_time = st.session_state.get("id_time", "")
nome_time = st.session_state.get("nome_time", "")

res_admin = supabase.table("admins").select("email").eq("email", usuario).execute()
is_admin = len(res_admin.data) > 0

res = supabase.table("configuracoes").select("*").eq("id", "evento_roubo").execute()
evento = res.data[0] if res.data else {}

if not evento:
    st.error("⚠️ Evento não encontrado.")
    st.stop()

if not evento.get("finalizado"):
    st.info("📌 O evento ainda não foi encerrado.")
    if is_admin and st.button("⛔ Encerrar Evento Agora"):
        supabase.table("configuracoes").update({
            "fase": 3,
            "finalizado": True,
            "encerrado_em": datetime.now().isoformat()
        }).eq("id", "evento_roubo").execute()
        st.success("✅ Evento encerrado com sucesso!")
        st.rerun()
    else:
        st.stop()

st.title("📄 Resumo do Evento de Roubo")

st.subheader("📉 Jogadores Perdidos por Time")
perdas = evento.get("perdas", {})
for id_perdedor, qtd in perdas.items():
    res = supabase.table("times").select("nome").eq("id", id_perdedor).execute()
    nome = res.data[0]["nome"] if res.data else "Desconhecido"
    st.markdown(f"- **{nome}** perdeu **{qtd} jogador(es)**")

st.subheader("🔒 Jogadores Protegidos")
res_bloqueados = supabase.table("jogadores_bloqueados").select("*").execute()
protegidos_por_time = {}
for item in res_bloqueados.data:
    tid = item["id_time"]
    if tid not in protegidos_por_time:
        protegidos_por_time[tid] = []
    protegidos_por_time[tid].append(item["nome"])

for tid, nomes in protegidos_por_time.items():
    res = supabase.table("times").select("nome").eq("id", tid).execute()
    nome = res.data[0]["nome"] if res.data else "Desconhecido"
    st.markdown(f"**{nome}** protegeu: {', '.join(nomes)}")

st.subheader("💸 Gastos de cada time no Evento")
res_mov = supabase.table("movimentacoes_financeiras").select("*").eq("tipo", "compra_roubo").execute()
gastos_por_time = {}
for mov in res_mov.data:
    tid = mov["id_time"]
    gastos_por_time[tid] = gastos_por_time.get(tid, 0) + abs(mov["valor"])

for tid, gasto in gastos_por_time.items():
    res = supabase.table("times").select("nome").eq("id", tid).execute()
    nome = res.data[0]["nome"] if res.data else "Desconhecido"
    st.markdown(f"**{nome}** gastou R$ {gasto:,}".replace(",", "."))

st.subheader("📑 Jogadores Roubados")
res_bid = supabase.table("bid").select("*").order("data", desc=False).execute()
bid_roubos = [b for b in res_bid.data if b["origem"] != b["destino"]]

for bid in bid_roubos:
    res_o = supabase.table("times").select("nome").eq("id", bid["origem"]).execute()
    res_d = supabase.table("times").select("nome").eq("id", bid["destino"]).execute()
    origem = res_o.data[0]["nome"] if res_o.data else "Desconhecido"
    destino = res_d.data[0]["nome"] if res_d.data else "Desconhecido"
    nome_jogador = bid["nome"]
    preco = bid["valor"]
    data = datetime.fromisoformat(bid["data"]).strftime("%d/%m %H:%M")

    st.markdown(f"- **{nome_jogador}** foi de **{origem}** para **{destino}** por R$ {preco:,} em {data}".replace(",", "."))

if is_admin and st.button("🔄 Iniciar Novo Evento"):
    supabase.table("configuracoes").delete().eq("id", "evento_roubo").execute()
    supabase.table("jogadores_bloqueados").delete().execute()
    st.success("🧼 Evento resetado. Pronto para novo ciclo!")
    st.rerun()
