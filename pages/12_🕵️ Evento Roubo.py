# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random
import pandas as pd
from utils import verificar_login, registrar_movimentacao

st.set_page_config(page_title="Evento de Roubo - LigaFut", layout="wide")

url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

verificar_login()

id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

st.title("🕵️ Evento de Roubo - LigaFut")

ID_CONFIG = "56f3af29-a4ac-4a76-aeb3-35400aa2a773"

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
    st.experimental_rerun()

# 🔁 Reiniciar evento
if eh_admin:
    st.subheader("🔁 Reiniciar Evento com Nova Ordem (Admin)")
    if st.button("🔀 Embaralhar e Reiniciar Evento"):
        times_data = supabase.table("times").select("id", "nome").execute().data
        random.shuffle(times_data)
        nova_ordem_ids = [t["id"] for t in times_data]
        supabase.table("configuracoes").update({
            "ativo": True,
            "finalizado": False,
            "fase": "sorteio",
            "ordem": nova_ordem_ids,
            "vez": "0",
            "roubos": {},
            "bloqueios": {},
            "ultimos_bloqueios": bloqueios,
            "ja_perderam": {},
            "concluidos": [],
            "inicio": str(datetime.utcnow())
        }).eq("id", ID_CONFIG).execute()
        st.experimental_rerun()

# 🔐 Fase de bloqueio
if ativo and fase == "sorteio" and eh_admin:
    st.subheader("🛡️ Iniciar Fase de Bloqueio")
    if st.button("➡️ Começar Bloqueios"):
        supabase.table("configuracoes").update({"fase": "bloqueio"}).eq("id", ID_CONFIG).execute()
        st.experimental_rerun()

if ativo and fase == "bloqueio":
    st.subheader("🔐 Proteja seus jogadores")
    bloqueios_atual = bloqueios.get(id_time, [])
    elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data or []
    nomes_bloqueados = [j["nome"] for j in bloqueios_atual]
    jogadores_disponiveis = [j["nome"] for j in elenco if j["nome"] not in nomes_bloqueados]

    if len(nomes_bloqueados) < limite_bloqueios:
        selecionado = st.selectbox("Selecione um jogador para proteger:", [""] + jogadores_disponiveis)
        if selecionado and st.button("🔒 Proteger jogador"):
            jogador = next(j for j in elenco if j["nome"] == selecionado)
            bloqueios_atual.append({"nome": jogador["nome"], "posicao": jogador["posicao"]})
            bloqueios[id_time] = bloqueios_atual
            supabase.table("configuracoes").update({"bloqueios": bloqueios}).eq("id", ID_CONFIG).execute()
            st.experimental_rerun()
    else:
        for j in bloqueios_atual:
            st.markdown(f"- 🔐 {j['nome']} ({j['posicao']})")

    if eh_admin:
        if st.button("👉 Iniciar Fase de Ação"):
            supabase.table("configuracoes").update({"fase": "acao", "vez": "0", "concluidos": []}).eq("id", ID_CONFIG).execute()
            st.experimental_rerun()

# 🎯 Fase de ação
if ativo and fase == "acao":
    if vez >= len(ordem):
        st.success("✅ Evento concluído!")
        st.stop()

    try:
        nome_vez = supabase.table("times").select("nome").eq("id", ordem[vez]).execute().data[0]["nome"]
        st.markdown(f"🟡 **Vez do time:** {nome_vez}")

        if id_time == ordem[vez]:
            st.subheader("🔍 Escolha os jogadores para roubar")
            times = supabase.table("times").select("id", "nome").execute().data
            limite_alcancado = len(roubos.get(id_time, [])) >= 5

            if limite_alcancado:
                st.info("✅ Você já escolheu os 5 jogadores permitidos.")

            for time in times:
                if time["id"] == id_time or ja_perderam.get(time["id"], 0) >= 4:
                    continue

                elenco = supabase.table("elenco").select("*").eq("id_time", time["id"]).execute().data or []
                bloqueados = [j["nome"] for j in bloqueios.get(time["id"], [])]

                with st.expander(f"📂 {time['nome']}"):
                    for jogador in elenco:
                        nome_j = jogador["nome"]
                        posicao = jogador["posicao"]
                        valor = jogador["valor"]
                        overall = jogador.get("overall", 0)
                        ja_roubado = any(r.get("nome") == nome_j and r.get("de") == time["id"] for lista in roubos.values() for r in lista)
                        bloqueado = nome_j in bloqueados
                        btn_id = f"{time['id']}_{nome_j}_{posicao}"

                        if bloqueado:
                            st.markdown(f"🔒 {nome_j} - {posicao} (R$ {valor:,.0f})")
                        elif ja_roubado:
                            st.markdown(f"❌ {nome_j} - já roubado")
                        else:
                            if not limite_alcancado and st.button(f"Roubar {nome_j} (R$ {valor/2:,.0f})", key=btn_id):
                                saldo_r = supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]["saldo"]
                                if saldo_r < valor // 2:
                                    st.error("❌ Seu time não tem saldo suficiente para este roubo.")
                                    st.stop()

                                saldo_p = supabase.table("times").select("saldo").eq("id", time["id"]).execute().data[0]["saldo"]

                                supabase.table("times").update({"saldo": saldo_r - valor // 2}).eq("id", id_time).execute()
                                supabase.table("times").update({"saldo": saldo_p + valor // 2}).eq("id", time["id"]).execute()

                                novo = roubos.get(id_time, [])
                                novo.append({"nome": nome_j, "posicao": posicao, "valor": int(valor), "de": time["id"]})
                                roubos[id_time] = novo
                                ja_perderam[time["id"]] = ja_perderam.get(time["id"], 0) + 1

                                supabase.table("elenco").delete().eq("id_time", time["id"]).eq("nome", nome_j).execute()
                                supabase.table("elenco").insert({
                                    "id_time": id_time,
                                    "nome": nome_j,
                                    "posicao": posicao,
                                    "valor": valor,
                                    "overall": overall
                                }).execute()

                                registrar_movimentacao(id_time, nome_j, "Roubo", "Compra", valor // 2)

                                supabase.table("configuracoes").update({
                                    "roubos": roubos,
                                    "ja_perderam": ja_perderam
                                }).eq("id", ID_CONFIG).execute()
                                st.experimental_rerun()

            if st.button("✅ Finalizar minha participação"):
                concluidos.append(id_time)
                supabase.table("configuracoes").update({"concluidos": concluidos, "vez": str(vez + 1)}).eq("id", ID_CONFIG).execute()
                st.experimental_rerun()

        if eh_admin:
            if st.button("⏭️ Avançar time (Admin)"):
                supabase.table("configuracoes").update({"vez": str(vez + 1)}).eq("id", ID_CONFIG).execute()
                st.experimental_rerun()

            if vez + 1 >= len(ordem):
                if st.button("🏁 Encerrar Evento e Transferir Jogadores"):
                    supabase.table("configuracoes").update({"finalizado": True, "ativo": False}).eq("id", ID_CONFIG).execute()
                    st.experimental_rerun()

    except Exception as e:
        st.error(f"Erro ao buscar nome do time da vez: {e}")

# ✅ Evento finalizado - exibe resumo
if evento.get("finalizado"):
    st.success("✅ Evento encerrado. Jogadores já foram transferidos.")
    st.subheader("📋 Resumo das Transferências")

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

