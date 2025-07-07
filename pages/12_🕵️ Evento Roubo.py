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
def registrar_movimentacao(id_time, jogador, tipo, valor):
    try:
        supabase.table("movimentacoes_financeiras").insert({
            "id": str(uuid.uuid4()),
            "id_time": id_time,
            "tipo": tipo,
            "descricao": f"{tipo.capitalize()} de {jogador}",
            "valor": valor,
            "data": str(datetime.utcnow())
        }).execute()
    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")

def registrar_bid(id_time_origem, id_time_destino, jogador, tipo, valor):
    try:
        if not jogador or not isinstance(jogador, dict):
            st.error("❌ Dados do jogador inválidos para o BID.")
            return

        supabase.table("bid_transferencias").insert({
            "id": str(uuid.uuid4()),
            "id_time_origem": id_time_origem,
            "id_time_destino": id_time_destino,
            "nome_jogador": jogador.get("nome", "Desconhecido"),
            "posicao": jogador.get("posicao", "?"),
            "valor": int(valor),
            "tipo": tipo,
            "data": str(datetime.utcnow())
        }).execute()
    except Exception as e:
        st.error(f"Erro ao registrar no BID: {e}")
# 🚫 Verifica restrições
try:
    res_restricoes = supabase.table("times").select("restricoes").eq("id", id_time).execute()
    restricoes = res_restricoes.data[0].get("restricoes", {}) if res_restricoes.data else {}
    if restricoes.get("roubo", False):
        st.error("🚫 Seu time está proibido de participar do Evento de Roubo.")
        st.stop()
except Exception as e:
    st.warning(f"⚠️ Erro ao verificar restrições: {e}")
st.title("🕵️ Evento de Roubo - LigaFut")

ID_CONFIG = "56f3af29-a4ac-4a76-aeb3-35400aa2a773"
res_evento = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute().data
if not res_evento:
    st.error("⚠️ Configuração do evento não encontrada.")
    st.stop()
evento = res_evento[0]

ativo = evento.get("ativo", False)
fase = evento.get("fase", "sorteio")
ordem = evento.get("ordem", [])
vez = int(evento.get("vez", "0"))
concluidos = evento.get("concluidos", [])
bloqueios = evento.get("bloqueios", {})
ultimos_bloqueios = evento.get("ultimos_bloqueios", {})
ja_perderam = evento.get("ja_perderam", {})
roubos = evento.get("roubos", {})
limite_bloqueios = evento.get("limite_bloqueios", 3)
limite_perda = evento.get("limite_perda", 5)
limite_roubo = evento.get("limite_roubo", 5)

res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0]["administrador"]

if st.button("🔄 Atualizar Página"):
    st.experimental_rerun()
st.subheader("🛡️ Seus jogadores bloqueados")

bloqueios_atual = bloqueios.get(id_time, [])
ultimos_bloqueios_time = ultimos_bloqueios.get(id_time, [])
todos_bloqueados = bloqueios_atual + ultimos_bloqueios_time

if todos_bloqueados:
    for jogador in todos_bloqueados:
        st.markdown(f"- **{jogador['nome']}** ({jogador['posicao']})")
else:
    st.info("Você ainda não bloqueou nenhum jogador.")
if eh_admin:
    st.subheader("🔐 Configuração do Evento de Roubo")

    novo_limite = st.number_input("🔒 Quantos jogadores cada time pode bloquear?", min_value=1, max_value=5, value=limite_bloqueios, step=1)
    novo_limite_perda = st.number_input("❌ Quantos jogadores cada time pode perder?", min_value=1, max_value=10, value=limite_perda, step=1)
    novo_limite_roubo = st.number_input("⚔️ Quantos jogadores cada time pode roubar?", min_value=1, max_value=10, value=limite_roubo, step=1)

    if st.button("✅ Salvar e iniciar evento"):
        times_data = supabase.table("times").select("id", "nome").execute().data
        palmeiras = next((t for t in times_data if t.get("nome", "").strip().lower() == "palmeiras"), None)
        restantes = [t for t in times_data if t != palmeiras]
        random.shuffle(restantes)
        nova_ordem = [palmeiras["id"]] + [t["id"] for t in restantes] if palmeiras else [t["id"] for t in times_data]

        supabase.table("configuracoes").update({
            "ativo": True,
            "fase": "bloqueio",
            "ordem": nova_ordem,
            "vez": "0",
            "roubos": {},
            "bloqueios": {},
            "ultimos_bloqueios": bloqueios,
            "ja_perderam": {},
            "concluidos": [],
            "inicio": str(datetime.utcnow()),
            "limite_bloqueios": novo_limite,
            "limite_perda": novo_limite_perda,
            "limite_roubo": novo_limite_roubo
        }).eq("id", ID_CONFIG).execute()

        st.success("✅ Evento iniciado.")
        st.experimental_rerun()
# 🔐 Fase de Bloqueio
if ativo and fase == "bloqueio":
    st.subheader("🔐 Proteja seus jogadores")

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

    if eh_admin and st.button("👉 Iniciar Fase de Ação"):
        supabase.table("configuracoes").update({"fase": "acao", "vez": "0", "concluidos": []}).eq("id", ID_CONFIG).execute()
        st.experimental_rerun()
# ⚔️ Fase de Ação
if ativo and fase == "acao" and vez < len(ordem):
    id_atual = ordem[vez]
    if id_time == id_atual:
        st.header("⚔️ Sua vez de roubar")

        if id_time in concluidos:
            st.info("✅ Você já finalizou.")
        else:
            if len(roubos.get(id_time, [])) >= limite_roubo:
                st.warning("❌ Você já atingiu o limite total de roubos permitidos.")
                st.stop()

            st.info(f"Você pode roubar até {limite_roubo} jogadores. Máximo de 2 do mesmo time.")

            times_data = supabase.table("times").select("id", "nome").execute().data
            times_dict = {t["id"]: t["nome"] for t in times_data if t["id"] != id_time}
            time_alvo_nome = st.selectbox("Selecione o time alvo:", list(times_dict.values()))
            id_alvo = next(i for i, n in times_dict.items() if n == time_alvo_nome)

            if ja_perderam.get(id_alvo, 0) >= limite_perda:
                st.warning("❌ Esse time já atingiu o limite de jogadores que pode perder.")
            elif len([r for r in roubos.get(id_time, []) if r["de"] == id_alvo]) >= 2:
                st.warning("❌ Você já roubou 2 jogadores desse time.")
            else:
                elenco_alvo = supabase.table("elenco").select("*").eq("id_time", id_alvo).execute().data
                bloqueados = [j["nome"] for j in bloqueios.get(id_alvo, [])]
                ja_roubados = [r["nome"] for sub in roubos.values() for r in sub]
                disponiveis = [j for j in elenco_alvo if j["nome"] not in bloqueados + ja_roubados]

                opcoes_jogadores = {
                    f"{j['nome']} | {j['posicao']} | OVR: {j.get('overall', '?')} | 🇧🇷 {j.get('nacionalidade', 'Desconhecida')} | R$ {j['valor']:,.0f}": j
                    for j in disponiveis
                }

                jogador_selecionado = st.selectbox("Escolha um jogador:", [""] + list(opcoes_jogadores.keys()))

                if jogador_selecionado:
                    jogador = opcoes_jogadores[jogador_selecionado]
                    valor = int(jogador["valor"])
                    valor_pago = valor // 2
                    st.info(f"💰 Valor do jogador: R$ {valor:,.0f} | Valor a ser pago: R$ {valor_pago:,.0f}")

                    if st.button("💰 Roubar jogador"):
                        supabase.table("elenco").delete().eq("id_time", id_alvo).eq("nome", jogador["nome"]).execute()
                        supabase.table("elenco").insert({**jogador, "id_time": id_time}).execute()

                        registrar_movimentacao(id_time, jogador["nome"], "saida", valor_pago)
                        registrar_movimentacao(id_alvo, jogador["nome"], "entrada", valor_pago)
                        registrar_bid(id_alvo, id_time, jogador, "roubo", valor_pago)

                        saldo = supabase.table("times").select("id", "saldo").in_("id", [id_time, id_alvo]).execute().data
                        saldo_dict = {s["id"]: s["saldo"] for s in saldo}
                        supabase.table("times").update({"saldo": saldo_dict[id_time] - valor_pago}).eq("id", id_time).execute()
                        supabase.table("times").update({"saldo": saldo_dict[id_alvo] + valor_pago}).eq("id", id_alvo).execute()

                        roubos.setdefault(id_time, []).append({
                            "nome": jogador["nome"],
                            "posicao": jogador["posicao"],
                            "valor": valor,
                            "de": id_alvo
                        })
                        ja_perderam[id_alvo] = ja_perderam.get(id_alvo, 0) + 1

                        supabase.table("configuracoes").update({
                            "roubos": roubos,
                            "ja_perderam": ja_perderam
                        }).eq("id", ID_CONFIG).execute()

                        st.success("✅ Jogador roubado!")
                        st.experimental_rerun()

            if st.button("➡️ Finalizar minha vez"):
                concluidos.append(id_time)
                supabase.table("configuracoes").update({
                    "concluidos": concluidos,
                    "vez": str(vez + 1)
                }).eq("id", ID_CONFIG).execute()
                st.success("✅ Vez encerrada.")
                st.experimental_rerun()
    else:
        proximo = supabase.table("times").select("nome").eq("id", id_atual).execute().data[0]["nome"]
        st.info(f"⏳ Aguardando: {proximo}")

        if eh_admin and st.button("⏭️ Pular vez"):
            supabase.table("configuracoes").update({
                "vez": str(vez + 1),
                "concluidos": concluidos + [id_atual]
            }).eq("id", ID_CONFIG).execute()
            st.success("⏭️ Pulado.")
            st.experimental_rerun()
# ✅ Finaliza evento automaticamente
if ativo and fase == "acao" and vez >= len(ordem):
    st.success("✅ Evento Finalizado!")
    supabase.table("configuracoes").update({
        "ativo": False,
        "finalizado": True
    }).eq("id", ID_CONFIG).execute()
    st.experimental_rerun()
if evento.get("finalizado"):
    st.success("✅ Transferências finalizadas:")
    resumo = []

    try:
        if isinstance(roubos, dict):
            for id_destino, lista in roubos.items():
                res_dest = supabase.table("times").select("nome").eq("id", id_destino).execute().data
                nome_destino = res_dest[0]["nome"] if res_dest else "Desconhecido"

                for jogador in lista:
                    id_origem = jogador.get("de")
                    res_origem = supabase.table("times").select("nome").eq("id", id_origem).execute().data
                    nome_origem = res_origem[0]["nome"] if res_origem else "Desconhecido"

                    resumo.append({
                        "🌟 Time que Roubou": nome_destino,
                        "👤 Jogador": jogador.get("nome", "N/D"),
                        "⚽ Posição": jogador.get("posicao", "N/D"),
                        "💰 Pago": f"R$ {int(jogador.get('valor', 0)) // 2:,.0f}",
                        "🔴 Time Roubado": nome_origem
                    })
        else:
            st.warning("❌ Estrutura de dados inválida para exibir transferências.")
    except Exception as e:
        st.error(f"❌ Erro ao gerar resumo: {e}")

    if isinstance(resumo, list) and resumo:
        df = pd.DataFrame(resumo)
        st.dataframe(df, width=1000, height=500)
    else:
        st.info("Nenhuma movimentação registrada.")
# 📋 Ordem de Participação (Sorteio)
st.subheader("📋 Ordem de Participação (Sorteio)")

try:
    if ordem:
        dados_times = supabase.table("times").select("id", "nome").in_("id", ordem).execute().data
        mapa = {t["id"]: t["nome"] for t in dados_times}

        for i, tid in enumerate(ordem):
            icone = "🔛" if i == vez else "⏳" if i > vez else "✅"
            st.markdown(f"{icone} {i+1}º - **{mapa.get(tid, 'Desconhecido')}**")
    else:
        st.warning("Ainda não foi definido o sorteio dos times.")
except Exception as e:
    st.error(f"Erro ao exibir a ordem dos times: {e}")
