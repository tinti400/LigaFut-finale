# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
import pandas as pd
import random

st.set_page_config(page_title="Evento de Roubo - LigaFut", layout="wide")

# FASE 1 - CONEXÃO E LOGIN
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0]["administrador"]

# FASE 2 - CONFIGURAÇÃO INICIAL DO EVENTO
ID_CONFIG = "56f3af29-a4ac-4a76-aeb3-35400aa2a773"
config_data = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute()
evento = config_data.data[0] if config_data.data else {}

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
limite_roubos = evento.get("limite_roubos", 5)
limite_perdas = evento.get("limite_perdas", 4)

if st.button("🔄 Atualizar Página"):
    st.experimental_rerun()

# FASE 3 - ADMIN CONFIGURA O EVENTO
if eh_admin and not ativo:
    st.subheader("🔐 Configurar Parâmetros do Evento de Roubo")
    novo_bloqueios = st.number_input("Quantos jogadores cada time pode bloquear?", 1, 5, 3)
    novo_roubos = st.number_input("Quantos jogadores cada time pode roubar?", 1, 6, 5)
    novo_perdas = st.number_input("Quantos jogadores cada time pode perder?", 1, 6, 4)

    if st.button("✅ Salvar e Iniciar Evento"):
        times_data = supabase.table("times").select("id", "nome").execute().data
        random.shuffle(times_data)
        ordem_aleatoria = [t["id"] for t in times_data]

        config = {
            "ativo": True,
            "fase": "bloqueio",
            "ordem": ordem_aleatoria,
            "vez": "0",
            "roubos": {},
            "bloqueios": {},
            "ultimos_bloqueios": bloqueios,
            "ja_perderam": {},
            "concluidos": [],
            "inicio": str(datetime.utcnow()),
            "limite_bloqueios": novo_bloqueios,
            "limite_roubos": novo_roubos,
            "limite_perdas": novo_perdas
        }

        supabase.table("configuracoes").update(config).eq("id", ID_CONFIG).execute()
        st.success("✅ Evento iniciado com sucesso!")
        st.experimental_rerun()

# EM BREVE: Fase 4 - Proteção de jogadores
# EM BREVE: Fase 5 - Ação de roubo
# EM BREVE: Fase 6 - Relatório Final e Finalização
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
import pandas as pd
import random

st.set_page_config(page_title="Evento de Roubo - LigaFut", layout="wide")

# FASE 1 - CONEXÃO E LOGIN
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0]["administrador"]

# FASE 2 - CONFIGURAÇÃO INICIAL DO EVENTO
ID_CONFIG = "56f3af29-a4ac-4a76-aeb3-35400aa2a773"
config_data = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute()
evento = config_data.data[0] if config_data.data else {}

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
limite_roubos = evento.get("limite_roubos", 5)
limite_perdas = evento.get("limite_perdas", 4)

if st.button("🔄 Atualizar Página"):
    st.experimental_rerun()

# FASE 3 - ADMIN CONFIGURA O EVENTO
if eh_admin and not ativo:
    st.subheader("🔐 Configurar Parâmetros do Evento de Roubo")
    novo_bloqueios = st.number_input("Quantos jogadores cada time pode bloquear?", 1, 5, 3)
    novo_roubos = st.number_input("Quantos jogadores cada time pode roubar?", 1, 6, 5)
    novo_perdas = st.number_input("Quantos jogadores cada time pode perder?", 1, 6, 4)

    if st.button("✅ Salvar e Iniciar Evento"):
        times_data = supabase.table("times").select("id", "nome").execute().data
        random.shuffle(times_data)
        ordem_aleatoria = [t["id"] for t in times_data]

        config = {
            "ativo": True,
            "fase": "bloqueio",
            "ordem": ordem_aleatoria,
            "vez": "0",
            "roubos": {},
            "bloqueios": {},
            "ultimos_bloqueios": bloqueios,
            "ja_perderam": {},
            "concluidos": [],
            "inicio": str(datetime.utcnow()),
            "limite_bloqueios": novo_bloqueios,
            "limite_roubos": novo_roubos,
            "limite_perdas": novo_perdas
        }

        supabase.table("configuracoes").update(config).eq("id", ID_CONFIG).execute()
        st.success("✅ Evento iniciado com sucesso!")
        st.experimental_rerun()

# FASE 4 - BLOQUEIO DE JOGADORES
if ativo and fase == "bloqueio":
    st.subheader("🛡️ Proteja seus jogadores")
    bloqueios_atual = bloqueios.get(id_time, [])
    bloqueios_anteriores = ultimos_bloqueios.get(id_time, [])
    nomes_bloqueados = [j["nome"] for j in bloqueios_atual]
    nomes_anteriores = [j["nome"] for j in bloqueios_anteriores]

    elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data or []
    jogadores_livres = [j for j in elenco if j["nome"] not in nomes_bloqueados + nomes_anteriores]
    nomes_livres = [j["nome"] for j in jogadores_livres]

    max_selecao = limite_bloqueios - len(nomes_bloqueados)
    if max_selecao > 0:
        selecionados = st.multiselect(f"Selecione até {max_selecao} jogador(es) para proteger:", nomes_livres)
        if selecionados and st.button("🔐 Confirmar Proteção"):
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
            st.success("✅ Jogadores protegidos com sucesso.")
            st.experimental_rerun()

    if eh_admin and st.button("➡️ Avançar para Fase de Ação"):
        supabase.table("configuracoes").update({"fase": "acao", "vez": "0", "concluidos": []}).eq("id", ID_CONFIG).execute()
        st.experimental_rerun()# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
import pandas as pd
import random

st.set_page_config(page_title="Evento de Roubo - LigaFut", layout="wide")

# FASE 1 - CONEXÃO E LOGIN
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0]["administrador"]

# FASE 2 - CONFIGURAÇÃO INICIAL DO EVENTO
ID_CONFIG = "56f3af29-a4ac-4a76-aeb3-35400aa2a773"
config_data = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute()
evento = config_data.data[0] if config_data.data else {}

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
limite_roubos = evento.get("limite_roubos", 5)
limite_perdas = evento.get("limite_perdas", 4)

if st.button("🔄 Atualizar Página"):
    st.experimental_rerun()

# FASE 3 - ADMIN CONFIGURA O EVENTO
if eh_admin and not ativo:
    st.subheader("🔐 Configurar Parâmetros do Evento de Roubo")
    novo_bloqueios = st.number_input("Quantos jogadores cada time pode bloquear?", 1, 5, 3)
    novo_roubos = st.number_input("Quantos jogadores cada time pode roubar?", 1, 6, 5)
    novo_perdas = st.number_input("Quantos jogadores cada time pode perder?", 1, 6, 4)

    if st.button("✅ Salvar e Iniciar Evento"):
        times_data = supabase.table("times").select("id", "nome").execute().data
        random.shuffle(times_data)
        ordem_aleatoria = [t["id"] for t in times_data]

        config = {
            "ativo": True,
            "fase": "bloqueio",
            "ordem": ordem_aleatoria,
            "vez": "0",
            "roubos": {},
            "bloqueios": {},
            "ultimos_bloqueios": bloqueios,
            "ja_perderam": {},
            "concluidos": [],
            "inicio": str(datetime.utcnow()),
            "limite_bloqueios": novo_bloqueios,
            "limite_roubos": novo_roubos,
            "limite_perdas": novo_perdas
        }

        supabase.table("configuracoes").update(config).eq("id", ID_CONFIG).execute()
        st.success("✅ Evento iniciado com sucesso!")
        st.experimental_rerun()

# FASE 4 - BLOQUEIO DE JOGADORES
if ativo and fase == "bloqueio":
    st.subheader("🛡️ Proteja seus jogadores")
    bloqueios_atual = bloqueios.get(id_time, [])
    bloqueios_anteriores = ultimos_bloqueios.get(id_time, [])
    nomes_bloqueados = [j["nome"] for j in bloqueios_atual]
    nomes_anteriores = [j["nome"] for j in bloqueios_anteriores]

    elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data or []
    jogadores_livres = [j for j in elenco if j["nome"] not in nomes_bloqueados + nomes_anteriores]
    nomes_livres = [j["nome"] for j in jogadores_livres]

    max_selecao = limite_bloqueios - len(nomes_bloqueados)
    if max_selecao > 0:
        selecionados = st.multiselect(f"Selecione até {max_selecao} jogador(es) para proteger:", nomes_livres)
        if selecionados and st.button("🔐 Confirmar Proteção"):
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
            st.success("✅ Jogadores protegidos com sucesso.")
            st.experimental_rerun()

    if eh_admin and st.button("➡️ Avançar para Fase de Ação"):
        supabase.table("configuracoes").update({"fase": "acao", "vez": "0", "concluidos": []}).eq("id", ID_CONFIG).execute()
        st.experimental_rerun()

# FASE 5 - AÇÃO DE ROUBO
if ativo and fase == "acao" and vez < len(ordem):
    id_atual = ordem[vez]
    if id_time == id_atual:
        st.header("⚔️ Sua vez de roubar")
        if id_time in concluidos:
            st.info("✅ Você já finalizou.")
        else:
            st.markdown(f"Você pode roubar até **{limite_roubos}** jogadores (máximo **2 por time**).")
            times_data = supabase.table("times").select("id", "nome").neq("id", id_time).execute().data
            times_dict = {t["id"]: t["nome"] for t in times_data}
            time_alvo_nome = st.selectbox("Selecione o time alvo:", list(times_dict.values()))
            id_alvo = next(i for i, n in times_dict.items() if n == time_alvo_nome)

            if ja_perderam.get(id_alvo, 0) >= limite_perdas:
                st.warning("❌ Esse time já atingiu o limite de perdas.")
            elif len([r for r in roubos.get(id_time, []) if r["de"] == id_alvo]) >= 2:
                st.warning("❌ Você já roubou 2 jogadores deste time.")
            else:
                elenco_alvo = supabase.table("elenco").select("*").eq("id_time", id_alvo).execute().data
                bloqueados = [j["nome"] for j in bloqueios.get(id_alvo, [])]
                ja_roubados = [r["nome"] for sub in roubos.values() for r in sub]
                disponiveis = [j for j in elenco_alvo if j["nome"] not in bloqueados + ja_roubados]

                st.subheader(f"🎯 Jogadores disponíveis para roubo de {time_alvo_nome}:")
                for j in disponiveis:
                    col1, col2 = st.columns([6, 1])
                    with col1:
                        st.markdown(f"**{j['nome']}** ({j['posicao']}) - R$ {int(j['valor']):,.0f}")
                    with col2:
                        if st.button("💰 Roubar", key=f"roubar_{j['id']}"):
                            valor = int(j["valor"])
                            pago = valor // 2
                            supabase.table("elenco").delete().eq("id", j["id"]).execute()
                            supabase.table("elenco").insert({**j, "id_time": id_time}).execute()
                            registrar_movimentacao(id_time, j["nome"], "saida", pago)
                            registrar_movimentacao(id_alvo, j["nome"], "entrada", pago)
                            registrar_bid(id_alvo, id_time, j, "roubo", pago)
                            saldo = supabase.table("times").select("id", "saldo").in_("id", [id_time, id_alvo]).execute().data
                            saldo_dict = {s["id"]: s["saldo"] for s in saldo}
                            supabase.table("times").update({"saldo": saldo_dict[id_time] - pago}).eq("id", id_time).execute()
                            supabase.table("times").update({"saldo": saldo_dict[id_alvo] + pago}).eq("id", id_alvo).execute()
                            roubos.setdefault(id_time, []).append({"nome": j["nome"], "posicao": j["posicao"], "valor": valor, "de": id_alvo})
                            ja_perderam[id_alvo] = ja_perderam.get(id_alvo, 0) + 1
                            supabase.table("configuracoes").update({"roubos": roubos, "ja_perderam": ja_perderam}).eq("id", ID_CONFIG).execute()
                            st.success("✅ Jogador roubado com sucesso!")
                            st.experimental_rerun()

            if st.button("✅ Finalizar minha vez"):
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
# ✅ Finaliza evento (admin)
if ativo and fase == "acao" and vez >= len(ordem):
    st.success("✅ Todas as rodadas concluídas!")
    if eh_admin and st.button("🔚 Encerrar Evento de Roubo"):
        supabase.table("configuracoes").update({
            "ativo": False,
            "fase": "finalizado",
            "finalizado": True
        }).eq("id", ID_CONFIG).execute()
        st.success("✅ Evento encerrado com sucesso!")
        st.rerun()

# 📊 Relatório Final
if evento.get("fase") == "finalizado":
    st.subheader("📊 Relatório Final - Evento de Roubo")
    resumo = []
    for id_destino, lista in roubos.items():
        nome_destino = supabase.table("times").select("nome").eq("id", id_destino).execute().data[0]["nome"]
        for jogador in lista:
            nome_origem = supabase.table("times").select("nome").eq("id", jogador["de"]).execute().data[0]["nome"]
            resumo.append({
                "🏆 Time que Roubou": nome_destino,
                "👤 Jogador": jogador["nome"],
                "⚽ Posição": jogador["posicao"],
                "💰 Valor Pago": f"R$ {int(jogador['valor']) // 2:,.0f}",
                "🔴 Time Roubado": nome_origem
            })

    if resumo:
        df_resumo = pd.DataFrame(resumo)
        df_resumo = df_resumo[["🏆 Time que Roubou", "👤 Jogador", "⚽ Posição", "💰 Valor Pago", "🔴 Time Roubado"]]
        st.dataframe(df_resumo, use_container_width=True, hide_index=True)
    else:
        st.info("⚠️ Nenhuma movimentação registrada.")

# 📋 Ordem de Participação
st.subheader("📋 Ordem de Participação (Sorteio)")
try:
    if ordem:
        times_ordenados = supabase.table("times").select("id", "nome").in_("id", ordem).execute().data
        mapa_times = {t["id"]: t["nome"] for t in times_ordenados}
        for i, idt in enumerate(ordem):
            indicador = "🔛" if i == vez else "⏳" if i > vez else "✅"
            st.markdown(f"{indicador} {i+1}º - **{mapa_times.get(idt, 'Desconhecido')}**")
    else:
        st.warning("Ainda não foi definido o sorteio dos times.")
except Exception as e:
    st.error(f"Erro ao exibir a ordem dos times: {e}")


