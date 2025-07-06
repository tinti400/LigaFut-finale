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

# ✅ Funções utilitárias
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

        nome_jogador = jogador.get("nome") or "Desconhecido"
        posicao = jogador.get("posicao") or "?"
        valor_final = int(valor) if valor else 0
        tipo_final = tipo or "transferencia"

        supabase.table("bid_transferencias").insert({
            "id": str(uuid.uuid4()),
            "id_time_origem": id_time_origem,
            "id_time_destino": id_time_destino,
            "nome_jogador": nome_jogador,
            "posicao": posicao,
            "valor": valor_final,
            "tipo": tipo_final,
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
# 🔧 Configuração do evento
ID_CONFIG = "56f3af29-a4ac-4a76-aeb3-35400aa2a773"
try:
    evento = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute().data[0]
except Exception as e:
    st.error(f"Erro ao carregar evento: {e}")
    st.stop()

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

# ✅ Verifica se é admin
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

# 🔘 Botão para iniciar o evento (aparece apenas para admin se não estiver ativo)
if eh_admin and not ativo:
    st.subheader("🟢 Iniciar Evento de Roubo")
    if st.button("🚀 Iniciar Evento"):
        # Sorteia a ordem dos times participantes
        todos_times = supabase.table("times").select("id", "nome").execute().data
        ordem_sorteada = [t["id"] for t in todos_times]
        random.shuffle(ordem_sorteada)

        supabase.table("configuracoes").update({
            "ativo": True,
            "fase": "bloqueio",
            "ordem": ordem_sorteada,
            "vez": "0",
            "concluidos": [],
            "roubos": {},
            "bloqueios": {},
            "ja_perderam": {},
            "finalizado": False
        }).eq("id", ID_CONFIG).execute()

        st.success("🚀 Evento iniciado com sucesso! Fase de bloqueio liberada.")
        st.experimental_rerun()

if st.button("🔄 Atualizar Página"):
    st.experimental_rerun()

# 🔍 Mostrar jogadores bloqueados do time atual
st.subheader("🛡️ Seus jogadores bloqueados")

bloqueios_atual = bloqueios.get(id_time, [])
ultimos_bloqueios_time = ultimos_bloqueios.get(id_time, [])
todos_bloqueados = bloqueios_atual + ultimos_bloqueios_time

if todos_bloqueados:
    for jogador in todos_bloqueados:
        st.markdown(f"- **{jogador['nome']}** ({jogador['posicao']})")
else:
    st.info("Você ainda não bloqueou nenhum jogador.")
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
# 🎯 Fase de Ação (Roubo)
if ativo and fase == "acao":
    st.subheader("🎯 Fase de Roubo de Jogadores")

    if vez >= len(ordem):
        st.success("✅ Todos os times finalizaram suas ações de roubo.")
        if eh_admin and st.button("🚨 Finalizar Evento"):
            supabase.table("configuracoes").update({"ativo": False, "fase": "finalizado"}).eq("id", ID_CONFIG).execute()
            st.success("✅ Evento finalizado.")
            st.experimental_rerun()
        st.stop()

    id_da_vez = ordem[vez]
    nome_da_vez = next((t["nome"] for t in supabase.table("times").select("id", "nome").execute().data if t["id"] == id_da_vez), f"Time {id_da_vez}")
    st.info(f"🎯 É a vez do time: **{nome_da_vez}**")

    if id_da_vez != id_time and not eh_admin:
        st.warning("⏳ Aguarde sua vez para realizar ações.")
        st.stop()

    # Selecionar time alvo
    st.subheader("🎯 Selecione um time para visualizar o elenco:")
    todos_times = supabase.table("times").select("id", "nome").execute().data
    ids_bloqueados = [tid for tid, lista in ja_perderam.items() if len(lista) >= 4]
    times_validos = [t for t in todos_times if t["id"] != id_time and t["id"] not in ids_bloqueados]

    if not times_validos:
        st.warning("❌ Nenhum time disponível para roubo.")
    else:
        nomes_validos = [t["nome"] for t in times_validos]
        alvo_nome = st.selectbox("Selecione o time alvo:", nomes_validos)
        alvo_id = next((t["id"] for t in times_validos if t["nome"] == alvo_nome), None)

        if alvo_id:
            elenco_alvo = supabase.table("elenco").select("*").eq("id_time", alvo_id).execute().data or []
            bloqueados = bloqueios.get(alvo_id, [])
            nomes_bloqueados = [j["nome"] for j in bloqueados]

            st.markdown("### 👥 Elenco do Time Alvo:")
            for jogador in elenco_alvo:
                nome = jogador["nome"]
                pos = jogador["posicao"]
                val = jogador["valor"]

                if nome in nomes_bloqueados:
                    st.markdown(f"🔒 **{nome}** ({pos}) - Protegido")
                else:
                    col1, col2 = st.columns([4, 1])
                    col1.markdown(f"**{nome}** ({pos}) - R${val:,.0f}")
                    if col2.button("💰 Roubar", key=f"roubar_{nome}"):
                        # Atualizar saldo
                        saldo_res = supabase.table("times").select("saldo").eq("id", id_time).execute()
                        saldo_atual = saldo_res.data[0]["saldo"] if saldo_res.data else 0

                        if saldo_atual < val:
                            st.error("❌ Saldo insuficiente.")
                        else:
                            # Atualiza saldo e registros
                            supabase.table("times").update({"saldo": saldo_atual - val}).eq("id", id_time).execute()
                            registrar_movimentacao(id_time, nome, "compra", -val)
                            registrar_movimentacao(alvo_id, nome, "venda", val // 2)

                            # Adiciona jogador
                            novo = jogador.copy()
                            novo["id"] = str(uuid.uuid4())
                            novo["id_time"] = id_time
                            supabase.table("elenco").insert(novo).execute()

                            # Remove do time alvo
                            supabase.table("elenco").delete().eq("id", jogador["id"]).execute()

                            # BID
                            registrar_bid(alvo_id, id_time, jogador, "roubo", val)

                            # Atualizar histórico
                            ja_perderam.setdefault(alvo_id, []).append(nome)
                            roubos.setdefault(id_time, []).append(nome)

                            supabase.table("configuracoes").update({
                                "ja_perderam": ja_perderam,
                                "roubos": roubos
                            }).eq("id", ID_CONFIG).execute()

                            st.success(f"✅ Jogador {nome} roubado com sucesso!")
                            st.experimental_rerun()

    if st.button("✅ Finalizar minha rodada"):
        if id_time not in concluidos:
            concluidos.append(id_time)
            supabase.table("configuracoes").update({
                "concluidos": concluidos,
                "vez": vez + 1
            }).eq("id", ID_CONFIG).execute()
            st.success("✅ Sua vez foi finalizada.")
            st.experimental_rerun()
# 📊 Resumo Final
st.subheader("📊 Resumo do Evento")

try:
    resumo = []
    times_data = supabase.table("times").select("id", "nome").execute().data

    for time_id, jogadores in roubos.items():
        nome = next((t["nome"] for t in times_data if t["id"] == time_id), f"Time {time_id}")
        for jogador in jogadores:
            resumo.append({"Time que Roubou": nome, "Jogador": jogador})

    if resumo:
        df_resumo = pd.DataFrame(resumo)
        st.dataframe(df_resumo)
    else:
        st.info("Ainda não houve nenhum roubo registrado.")
except Exception as e:
    st.error(f"Erro ao exibir resumo: {e}")
# ✅ Finaliza evento automaticamente
if ativo and fase == "acao" and vez >= len(ordem):
    st.success("✅ Evento Finalizado!")
    supabase.table("configuracoes").update({"ativo": False, "finalizado": True}).eq("id", ID_CONFIG).execute()
    st.experimental_rerun()

# 📢 Exibição do resumo completo após finalização
if evento.get("finalizado"):
    st.success("✅ Evento finalizado com sucesso! Veja o resumo completo abaixo.")

    resumo = []
    times_data = supabase.table("times").select("id", "nome").execute().data
    mapa_times = {t["id"]: t["nome"] for t in times_data}

    for id_roubador, jogadores in roubos.items():
        for j in jogadores:
            nome_roubador = mapa_times.get(id_roubador, "Desconhecido")
            nome_roubado = mapa_times.get(j["de"], "Desconhecido")
            resumo.append({
                "🟢 Quem Roubou": nome_roubador,
                "👤 Jogador": j["nome"],
                "⚽ Posição": j["posicao"],
                "💰 Valor Pago": f"R$ {j['valor'] // 2:,.0f}",
                "🔴 Time Roubado": nome_roubado
            })

    df = pd.DataFrame(resumo)
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("Nenhum jogador foi roubado.")

    # 🔁 Reiniciar evento (admin)
    if eh_admin:
        st.subheader("🔁 Reiniciar Evento")
        if st.button("🧹 Apagar dados e reiniciar evento"):
            supabase.table("configuracoes").update({
                "ativo": False,
                "fase": "sorteio",
                "ordem": [],
                "vez": "0",
                "roubos": {},
                "bloqueios": {},
                "ultimos_bloqueios": bloqueios,
                "ja_perderam": {},
                "concluidos": [],
                "finalizado": False
            }).eq("id", ID_CONFIG).execute()
            st.success("Evento reiniciado com sucesso.")
            st.experimental_rerun()

