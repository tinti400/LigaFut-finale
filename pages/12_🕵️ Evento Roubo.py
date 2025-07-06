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
    try:
        supabase.table("movimentacoes_financeiras").insert({
            "id": str(uuid.uuid4()),
            "id_time": id_time,
            "tipo": tipo,
            "valor": valor,
            "descricao": f"{tipo.title()} de {jogador}",
            "data": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")

def registrar_bid(origem, destino, jogador, tipo, valor):
    try:
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
    except Exception as e:
        st.error(f"Erro ao registrar BID: {e}")
# ✅ Obter configurações do evento
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
concluidos = config.get("concluidos", [])

# 🔄 Início do evento
st.title("🕵️ Evento de Roubo - LigaFut")

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
            "roubos": {},
            "concluidos": []
        }).eq("id", ID_CONFIG).execute()
        st.success("✅ Evento iniciado.")
        st.experimental_rerun()
# 🔐 Fase de bloqueio - Jogadores protegidos
if ativo and fase == "bloqueio":
    st.subheader("🔐 Proteja seus jogadores")

    limite_bloqueios = config.get("limite_bloqueios", 4)
    bloqueios_atual = bloqueios.get(id_time, [])
    bloqueios_anteriores = ultimos_bloqueios.get(id_time, [])
    nomes_bloqueados = [j["nome"] for j in bloqueios_atual]
    nomes_anteriores = [j["nome"] for j in bloqueios_anteriores]

    elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data or []
    jogadores_livres = [j for j in elenco if j["nome"] not in nomes_bloqueados + nomes_anteriores]
    nomes_livres = [j["nome"] for j in jogadores_livres]

    if len(nomes_bloqueados) < limite_bloqueios:
        max_selecao = limite_bloqueios - len(nomes_bloqueados)
        selecionados = st.multiselect(f"Selecione até {max_selecao} jogador(es):", nomes_livres)

        if selecionados and st.button("🔐 Confirmar proteção"):
            novos_bloqueios = []
            for j in jogadores_livres:
                if j["nome"] in selecionados:
                    bloqueio = {"nome": j["nome"], "posicao": j["posicao"]}
                    novos_bloqueios.append(bloqueio)
                    try:
                        supabase.table("jogadores_bloqueados_roubo").insert({
                            "id": str(uuid.uuid4()),
                            "id_jogador": j["id"],
                            "id_time": id_time,
                            "temporada": 1,
                            "evento": "roubo",
                            "data_bloqueio": str(datetime.utcnow())
                        }).execute()
                    except Exception as e:
                        st.warning(f"Erro ao salvar bloqueio no histórico: {e}")

            bloqueios[id_time] = bloqueios_atual + novos_bloqueios
            supabase.table("configuracoes").update({"bloqueios": bloqueios}).eq("id", ID_CONFIG).execute()
            st.success("✅ Proteção realizada.")
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("🛡️ Seus jogadores protegidos:")
    if bloqueios_atual or bloqueios_anteriores:
        for j in bloqueios_atual + bloqueios_anteriores:
            st.markdown(f"- **{j['nome']}** ({j['posicao']})")
    else:
        st.info("Você ainda não protegeu nenhum jogador.")

    if eh_admin and st.button("➡️ Iniciar fase de Ação"):
        supabase.table("configuracoes").update({"fase": "acao", "vez": 0, "concluidos": []}).eq("id", ID_CONFIG).execute()
        st.experimental_rerun()
# 🎯 Fase de ação - Roubo de jogadores
if ativo and fase == "acao":
    st.subheader("🎯 Ação de Roubo")

    if vez < len(ordem):
        id_vez = ordem[vez]
        nome_vez = supabase.table("times").select("nome").eq("id", id_vez).execute().data[0]["nome"]

        if id_time == id_vez:
            st.success(f"🎯 É sua vez: **{nome_time}**")

            # Listar times que ainda podem perder jogadores (máximo 4)
            times_disponiveis = [t["id"] for t in supabase.table("times").select("id").execute().data]
            alvos_possiveis = []

            for tid in times_disponiveis:
                perdeu = ja_perderam.get(tid, 0)
                if tid != id_time and perdeu < 4:
                    alvos_possiveis.append(tid)

            if alvos_possiveis:
                id_alvo = st.selectbox("👥 Escolha um time para roubar:", alvos_possiveis, format_func=lambda x: supabase.table("times").select("nome").eq("id", x).execute().data[0]["nome"])

                # Pegar jogadores disponíveis (não bloqueados)
                elenco_alvo = supabase.table("elenco").select("*").eq("id_time", id_alvo).execute().data or []
                bloqueados = bloqueios.get(id_alvo, [])
                nomes_bloqueados = [j["nome"] for j in bloqueados]
                jogadores_disponiveis = [j for j in elenco_alvo if j["nome"] not in nomes_bloqueados]

                if jogadores_disponiveis:
                    jogador_escolhido = st.selectbox("🎯 Escolha o jogador para roubar:", jogadores_disponiveis, format_func=lambda x: f"{x['nome']} - {x['posicao']} - R$ {x['valor']:,}")

                    if st.button("💣 Roubar jogador"):
                        # 50% do valor do jogador
                        valor_roubo = int(jogador_escolhido["valor"] * 0.5)

                        # Transferência do jogador
                        supabase.table("elenco").update({"id_time": id_time}).eq("id", jogador_escolhido["id"]).execute()

                        # Atualiza finanças
                        registrar_movimentacao(id_time, jogador_escolhido["nome"], "compra", -valor_roubo)
                        registrar_movimentacao(id_alvo, jogador_escolhido["nome"], "venda", valor_roubo)
                        registrar_bid(id_alvo, id_time, jogador_escolhido, "roubo", valor_roubo)

                        # Atualiza contadores
                        ja_perderam[id_alvo] = ja_perderam.get(id_alvo, 0) + 1
                        if str(id_time) not in roubos:
                            roubos[str(id_time)] = []
                        roubos[str(id_time)].append(jogador_escolhido)

                        # Marca vez como concluída
                        supabase.table("configuracoes").update({
                            "vez": vez + 1,
                            "ja_perderam": ja_perderam,
                            "roubos": roubos
                        }).eq("id", ID_CONFIG).execute()

                        st.success(f"✅ {jogador_escolhido['nome']} roubado com sucesso!")
                        st.experimental_rerun()
                else:
                    st.warning("❌ Esse time não tem jogadores disponíveis para roubo.")
            else:
                st.warning("Nenhum time disponível para roubo.")
        else:
            st.info(f"Aguardando a vez de **{nome_vez}**...")
    else:
        st.success("✅ Evento Finalizado!")
        supabase.table("configuracoes").update({"ativo": False, "finalizado": True}).eq("id", ID_CONFIG).execute()
        st.experimental_rerun()
# 📋 Resumo do Evento
if fase in ["acao", "concluido"] and roubos:
    st.subheader("📋 Resumo dos Roubos")

    try:
        # 🔁 Recarrega os nomes dos times
        times_data = supabase.table("times").select("id", "nome").execute().data

        resumo = []
        for time_id, lista in roubos.items():
            nome = next((t["nome"] for t in times_data if t["id"] == int(time_id)), f"Time {time_id}")
            for jogador in lista:
                resumo.append({
                    "Time que Roubou": nome,
                    "Jogador": jogador["nome"],
                    "Posição": jogador["posicao"],
                    "Overall": jogador["overall"],
                    "Valor": f"R$ {jogador['valor']:,}"
                })

        if resumo:
            df_resumo = pd.DataFrame(resumo)
            st.data_editor(df_resumo, use_container_width=True)
        else:
            st.info("Nenhum roubo registrado até agora.")

    except Exception as e:
        st.error(f"Erro ao exibir resumo: {e}")

# 🛑 Botão de Finalizar Evento (Admin)
if eh_admin and ativo and st.button("🛑 Finalizar Evento Manualmente"):
    supabase.table("configuracoes").update({
        "ativo": False,
        "fase": "concluido",
        "finalizado": True
    }).eq("id", ID_CONFIG).execute()
    st.success("✅ Evento finalizado manualmente.")
    st.experimental_rerun()

