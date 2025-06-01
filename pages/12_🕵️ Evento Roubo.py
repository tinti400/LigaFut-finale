# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random
import pandas as pd
from utils import verificar_login, registrar_movimentacao

st.set_page_config(page_title="Evento de Roubo - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
verificar_login()

id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

st.title("🕵️ Evento de Roubo - LigaFut")

ID_CONFIG = "56f3af29-a4ac-4a76-aeb3-35400aa2a773"

# 📥 Carrega dados do evento
admin_ref = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = admin_ref.data and len(admin_ref.data) > 0 and admin_ref.data[0]["administrador"] == True

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

# 🔁 Atualizar manualmente
if st.button("🔄 Atualizar Página"):
    st.experimental_rerun()

# 🔁 Reiniciar evento (admin)
if eh_admin:
    st.subheader("🔁 Reiniciar Evento com Nova Ordem (Admin)")
    if st.button("🔀 Embaralhar e Reiniciar Evento"):
        res = supabase.table("times").select("id", "nome").execute()
        nova_ordem = res.data
        random.shuffle(nova_ordem)
        nova_ordem_ids = [t["id"] for t in nova_ordem]
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

# 🔐 Começar bloqueios
if ativo and fase == "sorteio" and eh_admin:
    st.subheader("🛡️ Iniciar Fase de Bloqueio")
    if st.button("➡️ Começar Bloqueios"):
        supabase.table("configuracoes").update({"fase": "bloqueio"}).eq("id", ID_CONFIG).execute()
        st.experimental_rerun()

# 🔐 Fase de bloqueio
if ativo and fase == "bloqueio":
    st.subheader("🔐 Proteja seus jogadores")
    bloqueios_atual = bloqueios.get(id_time, [])
    elenco_ref = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
    elenco = elenco_ref.data if elenco_ref.data else []
    nomes_bloqueados = [j["nome"] for j in bloqueios_atual]
    jogadores_disponiveis = [j["nome"] for j in elenco if j["nome"] not in nomes_bloqueados]
    max_bloqueios = limite_bloqueios

    if len(nomes_bloqueados) < max_bloqueios:
        opcoes = [j for j in jogadores_disponiveis if j not in nomes_bloqueados]
        selecionado = st.selectbox("Selecione um jogador para proteger:", [""] + opcoes)
        if selecionado and st.button("🔒 Proteger jogador"):
            jogador_obj = next((j for j in elenco if j["nome"] == selecionado), None)
            if jogador_obj:
                bloqueios_atual.append({
                    "nome": jogador_obj["nome"],
                    "posicao": jogador_obj["posicao"]
                })
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

                elenco_ref = supabase.table("elenco").select("*").eq("id_time", time["id"]).execute()
                elenco = elenco_ref.data if elenco_ref.data else []
                bloqueados = [j["nome"] for j in bloqueios.get(time["id"], [])]

                with st.expander(f"📂 {time['nome']}"):
                    for jogador in elenco:
                        nome_j = jogador["nome"]
                        posicao = jogador["posicao"]
                        valor = jogador["valor"]
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

                                novo = roubos.get(id_time, [])
                                novo.append({"nome": nome_j, "posicao": posicao, "valor": int(valor), "de": time["id"]})
                                roubos[id_time] = novo
                                ja_perderam[time["id"]] = ja_perderam.get(time["id"], 0) + 1

                                saldo_p = supabase.table("times").select("saldo").eq("id", time["id"]).execute().data[0]["saldo"]
                                supabase.table("times").update({"saldo": saldo_r - valor // 2}).eq("id", id_time).execute()
                                supabase.table("times").update({"saldo": saldo_p + valor // 2}).eq("id", time["id"]).execute()

                                registrar_movimentacao(id_time, nome_j, "Roubo", "Compra", valor // 2)
                                supabase.table("configuracoes").update({"roubos": roubos, "ja_perderam": ja_perderam}).eq("id", ID_CONFIG).execute()
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

# ✅ Evento finalizado
if evento.get("finalizado"):
    st.success("✅ Evento encerrado. Iniciando transferências...")
    try:
        for id_destino, lista_roubos in roubos.items():
            for jogador in lista_roubos:
                id_origem = jogador["de"]
                nome = jogador["nome"]
                supabase.table("elenco").delete().eq("id_time", id_origem).eq("nome", nome).execute()
                novo_jogador = {
                    "id_time": id_destino,
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "valor": jogador["valor"]
                }
                supabase.table("elenco").insert(novo_jogador).execute()

        st.success("✅ Todos os jogadores foram transferidos com sucesso.")
    except Exception as e:
        st.error(f"❌ Erro ao transferir jogadores: {e}")

    st.info("O evento foi finalizado. Para começar um novo, use o botão de reinício no topo da tela (Admin).")

    # 📊 Resumo das Transferências
    st.subheader("📋 Resumo das Transferências")
    resumo = []
    for id_destino, lista_roubos in roubos.items():
        time_destino = supabase.table("times").select("nome").eq("id", id_destino).execute().data
        nome_destino = time_destino[0]["nome"] if time_destino else "Desconhecido"
        for jogador in lista_roubos:
            id_origem = jogador["de"]
            time_origem = supabase.table("times").select("nome").eq("id", id_origem).execute().data
            nome_origem = time_origem[0]["nome"] if time_origem else "Desconhecido"
            resumo.append({
                "🏆 Time que Roubou": nome_destino,
                "👤 Jogador": jogador["nome"],
                "🎯 Posição": jogador["posicao"],
                "💰 Valor Pago (50%)": f"R$ {jogador['valor']//2:,.0f}",
                "❌ Time Roubado": nome_origem
            })

    if resumo:
        df_resumo = pd.DataFrame(resumo)
        st.dataframe(df_resumo, use_container_width=True)
    else:
        st.info("Nenhuma transferência registrada.")
