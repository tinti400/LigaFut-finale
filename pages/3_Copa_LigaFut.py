# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import random
from datetime import datetime
import uuid

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🏆 Copa LigaFut", page_icon="🏆", layout="centered")
st.title("🏆 Copa LigaFut - Mata-mata")

# 🔐 Verifica login e permissão
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

if not eh_admin:
    st.warning("🔐 Apenas administradores podem acessar esta página.")
    st.stop()

# 📊 Buscar todos os times
res_times = supabase.table("usuarios").select("time_id").execute()
time_ids = list({u["time_id"] for u in res_times.data if u.get("time_id")})

res_info = supabase.table("times").select("id", "nome", "logo").in_("id", time_ids).execute()
times_map = {t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")} for t in res_info.data}

# 🔹 Geração da Copa
if st.button("⚙️ Gerar Nova Copa LigaFut"):
    if len(time_ids) < 2:
        st.warning("⚠️ Mínimo de 2 times para gerar a Copa.")
        st.stop()

    try:
        supabase.table("copa_ligafut").delete().execute()
        random.shuffle(time_ids)

        fase = "Preliminar" if len(time_ids) > 16 else "Oitavas"
        jogos = []
        ids = time_ids[:]

        if fase == "Preliminar":
            preliminar = ids[:6]
            ids = ids[6:]
            for i in range(0, 6, 2):
                jogos.append({
                    "id": str(uuid.uuid4()),
                    "fase": fase,
                    "numero": 1,
                    "id_mandante": preliminar[i],
                    "id_visitante": preliminar[i + 1],
                    "gols_mandante": None,
                    "gols_visitante": None
                })
            fase = "Oitavas"

        for i in range(0, len(ids), 2):
            if i + 1 < len(ids):
                jogos.append({
                    "id": str(uuid.uuid4()),
                    "fase": fase,
                    "numero": 1,
                    "id_mandante": ids[i],
                    "id_visitante": ids[i + 1],
                    "gols_mandante": None,
                    "gols_visitante": None
                })

        for j in jogos:
            supabase.table("copa_ligafut").insert(j).execute()

        st.success("✅ Copa LigaFut gerada com sucesso!")
    except Exception as e:
        st.error(f"Erro ao gerar a copa: {e}")

# 📅 Exibição por fases
st.markdown("---")
st.subheader("🕛 Jogos da Copa")
try:
    res_copa = supabase.table("copa_ligafut").select("*").order("fase").order("numero").execute()
    jogos = res_copa.data

    if not jogos:
        st.info("Nenhum jogo encontrado. Gere a copa para iniciar.")
    else:
        fases = sorted(set(j["fase"] for j in jogos))
        for fase in fases:
            st.markdown(f"### 🌟 Fase: {fase}")
            jogos_fase = [j for j in jogos if j["fase"] == fase]

            for j in jogos_fase:
                m_id = j.get("id_mandante")
                v_id = j.get("id_visitante")
                m_nome = times_map.get(m_id, {}).get("nome", "?")
                v_nome = times_map.get(v_id, {}).get("nome", "?")
                m_logo = times_map.get(m_id, {}).get("logo", "")
                v_logo = times_map.get(v_id, {}).get("logo", "")

                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
                with col1:
                    if m_logo:
                        st.image(m_logo, width=40)
                    st.markdown(f"**{m_nome}**")

                with col2:
                    gm = st.number_input("", key=f"gm_{j['id']}", min_value=0, value=j.get("gols_mandante") or 0)
                with col3:
                    st.markdown("**x**")
                with col4:
                    gv = st.number_input("", key=f"gv_{j['id']}", min_value=0, value=j.get("gols_visitante") or 0)

                with col5:
                    if v_logo:
                        st.image(v_logo, width=40)
                    st.markdown(f"**{v_nome}**")

                if st.button("Salvar", key=f"btn_{j['id']}"):
                    try:
                        supabase.table("copa_ligafut").update({
                            "gols_mandante": gm,
                            "gols_visitante": gv
                        }).eq("id", j["id"]).execute()
                        st.success("Resultado salvo!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

        # 🔄 Gerar próxima fase
        st.markdown("---")
        st.subheader("🔄 Avançar Copa")

        fases_ordem = ["Preliminar", "Oitavas", "Quartas", "Semifinal", "Final"]
        fase_atual = None

        for fase in fases_ordem:
            if any(j["fase"] == fase for j in jogos):
                fase_atual = fase
                break

        jogos_atual = [j for j in jogos if j["fase"] == fase_atual]
        vencedores = []

        incompletos = [j for j in jogos_atual if j["gols_mandante"] is None or j["gols_visitante"] is None]
        if incompletos:
            st.warning(f"⚠️ Existem {len(incompletos)} jogos sem resultado na fase {fase_atual}. Finalize todos os placares antes de avançar.")
        else:
            if st.button("➡️ Gerar próxima fase"):
                try:
                    for j in jogos_atual:
                        if j["gols_mandante"] > j["gols_visitante"]:
                            vencedores.append(j["id_mandante"])
                        elif j["gols_visitante"] > j["gols_mandante"]:
                            vencedores.append(j["id_visitante"])
                        else:
                            vencedores.append(random.choice([j["id_mandante"], j["id_visitante"]]))

                    idx_atual = fases_ordem.index(fase_atual)
                    if idx_atual + 1 >= len(fases_ordem):
                        st.success("🏆 Final já foi jogada. A Copa terminou.")
                    else:
                        proxima_fase = fases_ordem[idx_atual + 1]
                        novos_jogos = []

                        for i in range(0, len(vencedores), 2):
                            if i + 1 < len(vencedores):
                                novos_jogos.append({
                                    "id": str(uuid.uuid4()),
                                    "fase": proxima_fase,
                                    "numero": 1,
                                    "id_mandante": vencedores[i],
                                    "id_visitante": vencedores[i + 1],
                                    "gols_mandante": None,
                                    "gols_visitante": None
                                })

                        for jogo in novos_jogos:
                            supabase.table("copa_ligafut").insert(jogo).execute()

                        st.success(f"✅ Fase {proxima_fase} criada com sucesso!")
                        st.rerun()

                except Exception as e:
                    st.error(f"Erro ao avançar fase: {e}")

except Exception as e:
    st.error(f"Erro ao carregar jogos: {e}")
