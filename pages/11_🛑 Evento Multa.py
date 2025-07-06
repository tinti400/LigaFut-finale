# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
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

# ✅ Verifica se é admin
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0]["administrador"]

# 🔄 Recuperar dados do evento
ID_CONFIG = "evento_multa"
res_config = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute()
if not res_config.data:
    st.error("Evento de Multa não encontrado.")
    st.stop()
evento = res_config.data[0]

ativo = evento.get("ativo", False)
fase = evento.get("fase", "bloqueio")
ordem = evento.get("ordem", [])
vez = int(evento.get("vez", 0))
concluidos = evento.get("concluidos", [])
ja_perderam = evento.get("ja_perderam", {})
bloqueios = evento.get("bloqueios", {})
limite_bloqueio = evento.get("limite_bloqueio", 3)
roubos = evento.get("roubos", {})

# ✅ Utilitários

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
        supabase.table("bid_transferencias").insert({
            "id": str(uuid.uuid4()),
            "id_time_origem": id_time_origem,
            "id_time_destino": id_time_destino,
            "nome_jogador": jogador["nome"],
            "posicao": jogador.get("posicao", "?"),
            "valor": int(valor),
            "tipo": tipo,
            "data": str(datetime.utcnow())
        }).execute()
    except Exception as e:
        st.error(f"Erro ao registrar no BID: {e}")

# 🔒 BLOQUEIO
if fase == "bloqueio":
    st.title("🕵️ Evento de Roubo - LigaFut")
    st.subheader("🔐 Seus jogadores bloqueados")

    meus_bloqueados = bloqueios.get(id_time, [])
    if meus_bloqueados:
        st.success("Jogadores bloqueados:")
        for nome in meus_bloqueados:
            st.markdown(f"✅ {nome}")
    else:
        st.info("Você ainda não bloqueou nenhum jogador.")

    elenco_res = supabase.table("elenco").select("nome", "posicao", "overall").eq("id_time", id_time).execute()
    elenco = elenco_res.data
    disponiveis = [j for j in elenco if j["nome"] not in meus_bloqueados]
    nomes_disponiveis = [j["nome"] for j in disponiveis]

    if len(meus_bloqueados) < limite_bloqueio:
        jogador = st.selectbox("Selecione um jogador para bloquear", [""] + nomes_disponiveis)
        if jogador and st.button("🔒 Bloquear jogador"):
            meus_bloqueados.append(jogador)
            bloqueios[id_time] = meus_bloqueados
            supabase.table("configuracoes").update({"bloqueios": bloqueios}).eq("id", ID_CONFIG).execute()
            st.success(f"{jogador} bloqueado!")
            st.experimental_rerun()
    else:
        st.warning(f"Você já bloqueou o limite de {limite_bloqueio} jogadores.")

    st.markdown("---")
    st.subheader("🔐 Configurar Limite de Bloqueio")
    if eh_admin:
        novo_limite = st.number_input("Quantos jogadores cada time pode bloquear?", min_value=1, max_value=5, value=limite_bloqueio, step=1)
        if st.button("✅ Salvar limite e iniciar evento"):
            times_res = supabase.table("times").select("id").execute()
            ordem_sorteada = [t["id"] for t in times_res.data]
            random.shuffle(ordem_sorteada)
            supabase.table("configuracoes").update({
                "limite_bloqueio": novo_limite,
                "fase": "acao",
                "ordem": ordem_sorteada,
                "vez": 0,
                "concluidos": [],
                "ja_perderam": {},
                "roubos": {},
                "ativo": True
            }).eq("id", ID_CONFIG).execute()
            st.success("✅ Evento iniciado!")
            st.experimental_rerun()
    else:
        st.info("Aguardando o administrador iniciar o evento.")
    st.stop()

# 🛒 FASE DE AÇÃO
if ativo and fase == "acao" and vez < len(ordem):
    id_atual = ordem[vez]
    if id_time == id_atual:
        st.header("💸 Sua vez de aplicar multas")
        if id_time in concluidos:
            st.info("✅ Você já finalizou.")
        else:
            st.info("Você pode comprar até 5 jogadores. Máximo de 2 do mesmo time. Times só podem perder até 4.")
            times_data = supabase.table("times").select("id", "nome").execute().data
            times_dict = {t["id"]: t["nome"] for t in times_data if t["id"] != id_time}

            time_alvo_nome = st.selectbox("Selecione o time alvo:", list(times_dict.values()))
            id_alvo = next(i for i, n in times_dict.items() if n == time_alvo_nome)

            if ja_perderam.get(id_alvo, 0) >= 4:
                st.warning("❌ Esse time já perdeu 4 jogadores.")
                st.stop()
            if len([r for r in roubos.get(id_time, []) if r["de"] == id_alvo]) >= 2:
                st.warning("❌ Já aplicou 2 multas neste time.")
                st.stop()

            elenco_alvo = supabase.table("elenco").select("*").eq("id_time", id_alvo).execute().data
            bloqueados_alvo = bloqueios.get(id_alvo, [])
            disponiveis = [j for j in elenco_alvo if j["nome"] not in bloqueados_alvo]

            opcoes_jogadores = {f"{j['nome']} | {j['posicao']} | OVR: {j.get('overall', '?')} | R$ {j['valor']:,.0f}": j for j in disponiveis}
            jogador_selecionado = st.selectbox("Escolha um jogador:", [""] + list(opcoes_jogadores.keys()))

            if jogador_selecionado:
                jogador = opcoes_jogadores[jogador_selecionado]
                valor_pago = int(jogador["valor"])
                st.info(f"💰 Valor do jogador: R$ {valor_pago:,.0f}")

                if st.button("💰 Comprar via multa"):
                    supabase.table("elenco").delete().eq("id_time", id_alvo).eq("nome", jogador["nome"]).execute()
                    supabase.table("elenco").insert({**jogador, "id_time": id_time}).execute()

                    registrar_movimentacao(id_time, jogador["nome"], "saida", valor_pago)
                    registrar_movimentacao(id_alvo, jogador["nome"], "entrada", valor_pago)
                    registrar_bid(id_alvo, id_time, jogador, "multa", valor_pago)

                    saldo = supabase.table("times").select("id", "saldo").in_("id", [id_time, id_alvo]).execute().data
                    saldo_dict = {s["id"]: s["saldo"] for s in saldo}
                    supabase.table("times").update({"saldo": saldo_dict[id_time] - valor_pago}).eq("id", id_time).execute()
                    supabase.table("times").update({"saldo": saldo_dict[id_alvo] + valor_pago}).eq("id", id_alvo).execute()

                    roubos.setdefault(id_time, []).append({
                        "nome": jogador["nome"],
                        "posicao": jogador["posicao"],
                        "valor": valor_pago,
                        "de": id_alvo
                    })
                    ja_perderam[id_alvo] = ja_perderam.get(id_alvo, 0) + 1

                    supabase.table("configuracoes").update({
                        "roubos": roubos,
                        "ja_perderam": ja_perderam
                    }).eq("id", ID_CONFIG).execute()

                    st.success("✅ Jogador adquirido!")
                    st.experimental_rerun()

            if st.button("➡️ Finalizar minha vez"):
                concluidos.append(id_time)
                supabase.table("configuracoes").update({"concluidos": concluidos, "vez": str(vez + 1)}).eq("id", ID_CONFIG).execute()
                st.success("✅ Vez encerrada.")
                st.experimental_rerun()
    else:
        nome_proximo = supabase.table("times").select("nome").eq("id", id_atual).execute().data[0]["nome"]
        st.info(f"⏳ Aguardando: {nome_proximo}")
        if eh_admin and st.button("⏭️ Pular vez"):
            supabase.table("configuracoes").update({"vez": str(vez + 1), "concluidos": concluidos + [id_atual]}).eq("id", ID_CONFIG).execute()
            st.success("⏭️ Pulado.")
            st.experimental_rerun()

# ✅ Finaliza evento
if ativo and fase == "acao" and vez >= len(ordem):
    st.success("✅ Evento Finalizado!")
    supabase.table("configuracoes").update({"ativo": False, "finalizado": True}).eq("id", ID_CONFIG).execute()
    st.experimental_rerun()

# 📋 Ordem de Participação
st.subheader("📋 Ordem de Participação (Sorteio)")
if ordem:
    times_ordenados = supabase.table("times").select("id", "nome").in_("id", ordem).execute().data
    mapa_times = {t["id"]: t["nome"] for t in times_ordenados}
    for i, idt in enumerate(ordem):
        indicador = "🔛" if i == vez else "⏳" if i > vez else "✅"
        st.markdown(f"{indicador} {i+1}º - **{mapa_times.get(idt, 'Desconhecido')}**")
else:
    st.warning("Ainda não foi definido o sorteio dos times.")
