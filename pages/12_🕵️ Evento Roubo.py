# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
import pandas as pd
import random

st.set_page_config(page_title="Evento de Roubo - LigaFut", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verificar login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

# ✅ Verifica admin
res_admin = supabase.table("admins").select("email").eq("email", email_usuario).execute()
eh_admin = len(res_admin.data) > 0

# ✅ Utilitários
def registrar_movimentacao(id_time, jogador, tipo, valor):
    supabase.table("movimentacoes_financeiras").insert({
        "id": str(uuid.uuid4()),
        "id_time": id_time,
        "tipo": tipo,
        "valor": valor,
        "descricao": f"{tipo.title()} de {jogador}",
        "data": datetime.now().isoformat()
    }).execute()

def registrar_bid(origem, destino, jogador, tipo, valor):
    supabase.table("bid_transferencias").insert({
        "id": str(uuid.uuid4()),
        "id_time_origem": origem,
        "id_time_destino": destino,
        "nome_jogador": jogador["nome"],
        "posicao": jogador["posicao"],
        "valor": valor,
        "tipo": tipo,
        "data": datetime.now().isoformat()
    }).execute()

# ⚙️ Carregar configuração
res = supabase.table("configuracoes").select("*").eq("tipo", "evento_roubo").execute()
if not res.data:
    st.warning("Evento de Roubo não configurado.")
    st.stop()

config = res.data[0]
ID_CONFIG = config["id"]
fase = config.get("fase", "inicio")
ativo = config.get("ativo", False)
ordem = config.get("ordem", [])
bloqueios = config.get("bloqueios", {})
ultimos_bloqueios = config.get("ultimos_bloqueios", {})
roubos = config.get("roubos", {})
ja_perderam = config.get("ja_perderam", {})
vez = config.get("vez", 0)

st.title("🕵️ Evento de Roubo - LigaFut")

# 🚀 Iniciar evento
if not ativo and eh_admin:
    if st.button("🚀 Iniciar Evento de Roubo"):
        times = supabase.table("times").select("id").execute().data
        ordem = random.sample([t["id"] for t in times], len(times))
        supabase.table("configuracoes").update({
            "ativo": True,
            "fase": "bloqueio",
            "ordem": ordem,
            "vez": 0,
            "bloqueios": {},
            "ultimos_bloqueios": bloqueios,
            "ja_perderam": {},
            "roubos": {}
        }).eq("id", ID_CONFIG).execute()
        st.success("✅ Evento iniciado.")
        st.experimental_rerun()

# 🔐 Fase de Bloqueio
if ativo and fase == "bloqueio":
    st.subheader("🔐 Proteja seus jogadores")

    limite = 4
    bloqueios_atuais = bloqueios.get(id_time, [])
    ultimos = ultimos_bloqueios.get(id_time, [])
    nomes_bloqueados = [j["nome"] for j in bloqueios_atuais + ultimos]

    elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data or []
    disponiveis = [j for j in elenco if j["nome"] not in nomes_bloqueados]

    if len(bloqueios_atuais) < limite:
        selecao = st.multiselect("Selecione jogadores para proteger:", [j["nome"] for j in disponiveis])
        if selecao and st.button("🔒 Proteger jogadores"):
            novos = [j for j in disponiveis if j["nome"] in selecao][:limite - len(bloqueios_atuais)]
            bloqueios[id_time] = bloqueios_atuais + [{"nome": j["nome"], "posicao": j["posicao"]} for j in novos]
            for j in novos:
                supabase.table("jogadores_bloqueados_roubo").insert({
                    "id": str(uuid.uuid4()),
                    "id_jogador": j["id"],
                    "id_time": id_time,
                    "temporada": 1,
                    "evento": "roubo",
                    "data_bloqueio": str(datetime.utcnow())
                }).execute()
            supabase.table("configuracoes").update({"bloqueios": bloqueios}).eq("id", ID_CONFIG).execute()
            st.success("✅ Jogadores protegidos.")
            st.experimental_rerun()

    if bloqueios_atuais:
        st.markdown("#### Jogadores protegidos:")
        for j in bloqueios_atuais:
            st.markdown(f"- **{j['nome']}** ({j['posicao']})")

    if eh_admin and st.button("➡️ Iniciar fase de Ação"):
        supabase.table("configuracoes").update({"fase": "acao", "vez": 0}).eq("id", ID_CONFIG).execute()
        st.experimental_rerun()

# 🎯 Fase de Ação
if ativo and fase == "acao":
    st.subheader("🎯 Ação de Roubo")

    if vez < len(ordem):
        id_vez = ordem[vez]
        nome_vez = supabase.table("times").select("nome").eq("id", id_vez).execute().data[0]["nome"]

        if id_time == id_vez:
            st.success(f"🎯 É sua vez: **{nome_time}**")

            todos_times = supabase.table("times").select("id").execute().data
            alvos = [t["id"] for t in todos_times if t["id"] != id_time and ja_perderam.get(t["id"], 0) < 4]

            if alvos:
                id_alvo = st.selectbox("👥 Escolha o time alvo:", alvos, format_func=lambda x: supabase.table("times").select("nome").eq("id", x).execute().data[0]["nome"])
                elenco_alvo = supabase.table("elenco").select("*").eq("id_time", id_alvo).execute().data or []
                bloqueados = bloqueios.get(id_alvo, [])
                nomes_bloqueados = [j["nome"] for j in bloqueados]
                livres = [j for j in elenco_alvo if j["nome"] not in nomes_bloqueados]

                if livres:
                    escolhido = st.selectbox("🎯 Escolha o jogador:", livres, format_func=lambda j: f"{j['nome']} - {j['posicao']} - R$ {j['valor']:,}")
                    if st.button("💣 Roubar jogador"):
                        valor = int(escolhido["valor"] * 0.5)
                        supabase.table("elenco").update({"id_time": id_time}).eq("id", escolhido["id"]).execute()
                        registrar_movimentacao(id_time, escolhido["nome"], "compra", -valor)
                        registrar_movimentacao(id_alvo, escolhido["nome"], "venda", valor)
                        registrar_bid(id_alvo, id_time, escolhido, "roubo", valor)

                        ja_perderam[id_alvo] = ja_perderam.get(id_alvo, 0) + 1
                        if str(id_time) not in roubos:
                            roubos[str(id_time)] = []
                        roubos[str(id_time)].append(escolhido)

                        supabase.table("configuracoes").update({
                            "vez": vez + 1,
                            "ja_perderam": ja_perderam,
                            "roubos": roubos
                        }).eq("id", ID_CONFIG).execute()

                        st.success(f"✅ Jogador roubado com sucesso!")
                        st.experimental_rerun()
                else:
                    st.warning("❌ Nenhum jogador disponível para roubo neste time.")
            else:
                st.warning("❌ Nenhum time disponível para ser roubado.")
        else:
            st.info(f"Aguardando a vez de **{nome_vez}**...")
    else:
        st.success("✅ Evento Finalizado.")
        supabase.table("configuracoes").update({"ativo": False, "fase": "concluido"}).eq("id", ID_CONFIG).execute()
        st.experimental_rerun()

# 📋 Resumo
if roubos:
    st.subheader("📋 Resumo dos Roubos")
    try:
        times_data = supabase.table("times").select("id", "nome").execute().data
        resumo = []
        for time_id, jogadores in roubos.items():
            nome = next((t["nome"] for t in times_data if t["id"] == int(time_id)), f"Time {time_id}")
            for j in jogadores:
                resumo.append({
                    "Time que Roubou": nome,
                    "Jogador": j["nome"],
                    "Posição": j["posicao"],
                    "Overall": j["overall"],
                    "Valor": f"R$ {j['valor']:,}"
                })

        if resumo:
            df = pd.DataFrame(resumo)
            st.dataframe(df)
        else:
            st.info("Nenhum roubo registrado.")
    except Exception as e:
        st.error(f"Erro ao exibir resumo: {e}")

# 🛑 Finalizar evento (manual)
if eh_admin and ativo and st.button("🛑 Finalizar Evento Manualmente"):
    supabase.table("configuracoes").update({
        "ativo": False,
        "fase": "concluido"
    }).eq("id", ID_CONFIG).execute()
    st.success("✅ Evento encerrado.")
    st.experimental_rerun()

