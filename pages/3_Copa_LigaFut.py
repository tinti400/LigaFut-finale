# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import random
import uuid

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.title("🏆 Copa LigaFut - Mata-mata")

# 🔐 Login
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

if not eh_admin:
    st.warning("Apenas administradores podem acessar esta página.")
    st.stop()

# 📊 Buscar times válidos
res_info = supabase.table("times").select("id", "nome", "logo").execute()
times_map = {
    t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")}
    for t in res_info.data
    if t.get("nome") and t["nome"].strip().upper() != "EMPTY"
}
time_ids = list(times_map.keys())

# 🧠 Geração da primeira fase com proteção total
def gerar_primeira_fase(times):
    random.shuffle(times)
    jogos = []
    fase = "Preliminar" if len(times) > 16 else "Oitavas"

    for i in range(0, len(times), 2):
        id1 = times[i]
        id2 = times[i + 1] if i + 1 < len(times) else None

        if id2:
            jogos.append({
                "id": str(uuid.uuid4()),
                "fase": fase,
                "numero": len(jogos) + 1,
                "id_mandante": id1,
                "id_visitante": id2,
                "gols_mandante": None,
                "gols_visitante": None
            })
        else:
            nome = times_map.get(id1, {}).get("nome", id1)
            st.warning(f"⚠️ O time **{nome}** ficou sem adversário e foi ignorado.")

    return jogos

# 🔘 Botão para gerar
if st.button("⚙️ Gerar Nova Copa LigaFut"):
    if len(time_ids) < 2:
        st.warning("⚠️ Mínimo de 2 times válidos para iniciar a Copa.")
        st.stop()
    try:
        supabase.table("copa_ligafut").delete().neq("id", "").execute()
        jogos = gerar_primeira_fase(time_ids[:])
        for j in jogos:
            supabase.table("copa_ligafut").insert(j).execute()
        st.success("✅ Primeira fase criada com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao gerar a copa: {e}")

# 🔄 Avançar Fases
st.markdown("---")
st.subheader("🔄 Avançar Fase")
fases_ordem = ["Preliminar", "Oitavas", "Quartas", "Semifinal", "Final"]

try:
    res_jogos = supabase.table("copa_ligafut").select("*").order("numero").execute()
    jogos = res_jogos.data

    if not jogos:
        st.info("Nenhuma fase criada ainda.")
    else:
        fase_atual = sorted(set(j["fase"] for j in jogos), key=lambda x: fases_ordem.index(x))[-1]
        jogos_fase = [j for j in jogos if j["fase"] == fase_atual]

        incompletos = [j for j in jogos_fase if j["gols_mandante"] is None or j["gols_visitante"] is None]
        if incompletos:
            st.warning(f"⚠️ Existem {len(incompletos)} jogos sem placar.")
        else:
            if st.button("➡️ Gerar próxima fase"):
                vencedores = []
                for j in jogos_fase:
                    if j["gols_mandante"] > j["gols_visitante"]:
                        vencedores.append(j["id_mandante"])
                    elif j["gols_visitante"] > j["gols_mandante"]:
                        vencedores.append(j["id_visitante"])
                    else:
                        vencedores.append(random.choice([j["id_mandante"], j["id_visitante"]]))

                idx = fases_ordem.index(fase_atual)
                if idx + 1 >= len(fases_ordem):
                    st.success("🏆 Final já jogada. A Copa terminou.")
                else:
                    proxima_fase = fases_ordem[idx + 1]
                    novos_jogos = []
                    for i in range(0, len(vencedores), 2):
                        id1 = vencedores[i]
                        id2 = vencedores[i + 1] if i + 1 < len(vencedores) else None
                        if id2:
                            novos_jogos.append({
                                "id": str(uuid.uuid4()),
                                "fase": proxima_fase,
                                "numero": len(jogos) + i + 1,
                                "id_mandante": id1,
                                "id_visitante": id2,
                                "gols_mandante": None,
                                "gols_visitante": None
                            })
                        else:
                            nome = times_map.get(id1, {}).get("nome", id1)
                            st.warning(f"⚠️ O time **{nome}** ficou sem adversário na próxima fase.")
                    for jogo in novos_jogos:
                        supabase.table("copa_ligafut").insert(jogo).execute()
                    st.success(f"✅ Fase {proxima_fase} criada com sucesso!")
                    st.rerun()
except Exception as e:
    st.error(f"Erro ao avançar fase: {e}")

# 📅 Exibir Jogos
st.markdown("---")
st.subheader("🕛 Jogos da Copa")
try:
    if jogos:
        fases = sorted(set(j["fase"] for j in jogos), key=lambda x: fases_ordem.index(x))
        for fase in fases:
            st.markdown(f"### 🌟 {fase}")
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
                    if m_logo: st.image(m_logo, width=40)
                    st.markdown(f"**{m_nome}**")
                with col2:
                    gm = st.number_input("", key=f"gm_{j['id']}", min_value=0, value=j.get("gols_mandante") or 0)
                with col3:
                    st.markdown("**x**")
                with col4:
                    gv = st.number_input("", key=f"gv_{j['id']}", min_value=0, value=j.get("gols_visitante") or 0)
                with col5:
                    if v_logo: st.image(v_logo, width=40)
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
except Exception as e:
    st.error(f"Erro ao exibir jogos: {e}")
