# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random
import pandas as pd
from utils import verificar_login, registrar_movimentacao

st.set_page_config(page_title="Evento de Roubo - LigaFut", layout="wide")

# 🔗 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🔐 Verifica login
verificar_login()

id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

# 🔒 Verifica se o time está proibido de participar
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

# ⚙️ Configurações do evento
admin_ref = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = admin_ref.data and admin_ref.data[0]["administrador"]

res = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute()
evento = res.data[0] if res.data else {}

ativo = evento.get("ativo", False)
fase = evento.get("fase", "sorteio")
ordem = evento.get("ordem", [])
vez = int(evento.get("vez", "0"))
concluidos = evento.get("concluidos", [])
bloqueios = evento.get("bloqueios", {})
ultimos_bloqueios = evento.get("ultimos_bloqueios", {})
ja_perderam = evento.get("ja_perderam", {})
roubos = evento.get("roubos", {})
limite_bloqueios = evento.get("limite_bloqueios", 4)

if st.button("🔄 Atualizar Página"):
    st.rerun()

# 🔁 ADMIN - Reiniciar evento
if eh_admin:
    st.subheader("🔁 Reiniciar Evento com Nova Ordem")
    if st.button("🔀 Embaralhar e Iniciar Evento"):
        res_times = supabase.table("times").select("id", "nome").execute()
        if not res_times.data:
            st.error("❌ Nenhum time encontrado.")
        else:
            times_data = res_times.data
            random.shuffle(times_data)
            nova_ordem_ids = [t["id"] for t in times_data]
            supabase.table("configuracoes").update({
                "ativo": True,
                "finalizado": False,
                "fase": "bloqueio",
                "ordem": nova_ordem_ids,
                "vez": "0",
                "roubos": {},
                "bloqueios": {},
                "ultimos_bloqueios": bloqueios,
                "ja_perderam": {},
                "concluidos": [],
                "inicio": str(datetime.utcnow())
            }).eq("id", ID_CONFIG).execute()
            st.success("✅ Evento reiniciado.")
            st.rerun()

# 🔐 Fase de Bloqueio
if ativo and fase == "bloqueio":
    st.subheader("🔐 Proteja seus jogadores")
    bloqueios_atual = bloqueios.get(id_time, [])
    bloqueios_anteriores = ultimos_bloqueios.get(id_time, [])
    nomes_bloqueados = [j["nome"] for j in bloqueios_atual]
    nomes_anteriores = [j["nome"] for j in bloqueios_anteriores]

    elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data or []
    jogadores_livres = [j["nome"] for j in elenco if j["nome"] not in nomes_bloqueados + nomes_anteriores]

    if len(nomes_bloqueados) < limite_bloqueios:
        selecionado = st.selectbox("Selecione um jogador para proteger:", [""] + jogadores_livres)
        if selecionado and st.button("🔒 Proteger jogador"):
            jogador = next(j for j in elenco if j["nome"] == selecionado)
            bloqueios_atual.append({"nome": jogador["nome"], "posicao": jogador["posicao"]})
            bloqueios[id_time] = bloqueios_atual
            supabase.table("configuracoes").update({"bloqueios": bloqueios}).eq("id", ID_CONFIG).execute()
            st.rerun()
    else:
        for j in bloqueios_atual:
            st.markdown(f"- 🔐 {j['nome']} ({j['posicao']})")

    if eh_admin and st.button("👉 Iniciar Fase de Ação"):
        supabase.table("configuracoes").update({"fase": "acao", "vez": "0", "concluidos": []}).eq("id", ID_CONFIG).execute()
        st.success("🚀 Fase de ação iniciada.")
        st.rerun()

# ⚔️ Fase de Ação
if ativo and fase == "acao" and vez < len(ordem):
    id_atual = ordem[vez]
    if id_time == id_atual:
        st.header("⚔️ Sua vez de roubar")
        if id_time in concluidos:
            st.info("✅ Você já finalizou sua vez.")
        else:
            st.info("Você pode roubar até 5 jogadores. Máximo de 2 do mesmo time.")
            times = supabase.table("times").select("id", "nome").execute().data or []
            times_dict = {t["id"]: t["nome"] for t in times if t["id"] != id_time}
            opcoes = list(times_dict.values())
            time_alvo = st.selectbox("Selecione o time alvo:", opcoes)
            id_alvo = next(i for i, n in times_dict.items() if n == time_alvo)

            if ja_perderam.get(id_alvo, 0) >= 4:
                st.warning("❌ Este time já perdeu 4 jogadores. Bloqueado.")
            else:
                if roubos.get(id_time):
                    ja_roubados = [r for r in roubos[id_time] if r["de"] == id_alvo]
                    if len(ja_roubados) >= 2:
                        st.warning("❌ Você já roubou 2 jogadores desse time.")
                        st.stop()

                elenco_alvo = supabase.table("elenco").select("*").eq("id_time", id_alvo).execute().data or []
                bloqueados = [j["nome"] for j in bloqueios.get(id_alvo, [])]
                disponiveis = [j for j in elenco_alvo if j["nome"] not in bloqueados]
                nomes_disponiveis = [j["nome"] for j in disponiveis]

                jogador_nome = st.selectbox("Escolha um jogador:", [""] + nomes_disponiveis)
                if jogador_nome and st.button("💰 Roubar jogador"):
                    jogador = next(j for j in disponiveis if j["nome"] == jogador_nome)
                    valor = jogador["valor"]
                    valor_pago = valor // 2

                    supabase.table("elenco").delete().eq("id_time", id_alvo).eq("nome", jogador_nome).execute()
                    supabase.table("elenco").insert({**jogador, "id_time": id_time}).execute()
                    registrar_movimentacao(id_time, jogador_nome, "roubo", "entrada", valor_pago)
                    registrar_movimentacao(id_alvo, jogador_nome, "roubo", "saida", valor_pago)

                    roubos.setdefault(id_time, []).append({"nome": jogador_nome, "posicao": jogador["posicao"], "valor": valor, "de": id_alvo})
                    ja_perderam[id_alvo] = ja_perderam.get(id_alvo, 0) + 1
                    supabase.table("configuracoes").update({"roubos": roubos, "ja_perderam": ja_perderam}).eq("id", ID_CONFIG).execute()
                    st.success("✅ Jogador roubado com sucesso!")
                    st.rerun()

            if st.button("➡️ Finalizar minha vez"):
                concluidos.append(id_time)
                supabase.table("configuracoes").update({"concluidos": concluidos, "vez": str(vez + 1)}).eq("id", ID_CONFIG).execute()
                st.success("🔄 Sua vez foi encerrada.")
                st.rerun()
    else:
        nome_proximo = supabase.table("times").select("nome").eq("id", id_atual).execute().data[0]["nome"]
        st.warning(f"⏳ Aguarde, é a vez de **{nome_proximo}**")

# ✅ Finalizar evento
if ativo and fase == "acao" and vez >= len(ordem):
    st.success("✅ Evento Finalizado. Veja o resumo.")
    supabase.table("configuracoes").update({"ativo": False, "finalizado": True}).eq("id", ID_CONFIG).execute()
    st.rerun()

# 📊 Resumo
if evento.get("finalizado"):
    st.success("✅ Evento encerrado. Veja as transferências:")
    resumo = []
    for id_destino, lista in roubos.items():
        nome_destino = supabase.table("times").select("nome").eq("id", id_destino).execute().data[0]["nome"]
        for jogador in lista:
            nome_origem = supabase.table("times").select("nome").eq("id", jogador["de"]).execute().data[0]["nome"]
            resumo.append({
                "🏆 Time que Roubou": nome_destino,
                "👤 Jogador": jogador["nome"],
                "🎯 Posição": jogador["posicao"],
                "💰 Valor Pago (50%)": f"R$ {jogador['valor']//2:,.0f}",
                "❌ Time Roubado": nome_origem
            })
    if resumo:
        st.dataframe(pd.DataFrame(resumo), use_container_width=True)
    else:
        st.info("Nenhuma transferência foi registrada.")


