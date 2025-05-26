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
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import random
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

# 📊 Buscar todos os times válidos (nome preenchido e ≠ EMPTY)
res_info = supabase.table("times").select("id", "nome", "logo").execute()
times_map = {
    t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")}
    for t in res_info.data
    if t.get("nome") and t["nome"].strip().upper() != "EMPTY"
}
time_ids = list(times_map.keys())

# 🧠 Geração da estrutura da copa completa
def gerar_chaveamento_completo(times_validos):
    random.shuffle(times_validos)
    jogos = []
    ids_oitavas = []

    # Preliminar (caso haja mais de 16 times)
    while len(times_validos) > 16:
        t1 = times_validos.pop()
        t2 = times_validos.pop()
        jogos.append({
            "id": str(uuid.uuid4()),
            "fase": "Preliminar",
            "numero": len(jogos) + 1,
            "id_mandante": t1,
            "id_visitante": t2,
            "gols_mandante": None,
            "gols_visitante": None
        })
        ids_oitavas.append("vencedor_de_" + str(len(jogos)))

    # Restantes vão direto pras oitavas
    while times_validos:
        ids_oitavas.append(times_validos.pop())

    # Gera fases seguintes
    fases = ["Oitavas", "Quartas", "Semifinal", "Final"]
    fase_atual = ids_oitavas

    for fase in fases:
        nova_fase = []
        for i in range(0, len(fase_atual), 2):
            id1 = fase_atual[i]
            id2 = fase_atual[i+1] if i+1 < len(fase_atual) else None
            jogo_id = str(uuid.uuid4())
            jogos.append({
                "id": jogo_id,
                "fase": fase,
                "numero": len(jogos) + 1,
                "id_mandante": id1,
                "id_visitante": id2,
                "gols_mandante": None,
                "gols_visitante": None
            })
            nova_fase.append("vencedor_de_" + str(len(jogos)))
        fase_atual = nova_fase

    return jogos

# 🔘 Botão para gerar toda a copa
if st.button("⚙️ Gerar Nova Copa LigaFut"):
    if len(time_ids) < 2:
        st.warning("⚠️ Mínimo de 2 times válidos para gerar a Copa.")
        st.stop()

    try:
        supabase.table("copa_ligafut").delete().execute()
        jogos = gerar_chaveamento_completo(time_ids[:])
        for j in jogos:
            supabase.table("copa_ligafut").insert(j).execute()
        st.success("✅ Copa LigaFut completa gerada com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao gerar a copa: {e}")

# 📅 Exibir confrontos por fase
st.markdown("---")
st.subheader("🕛 Jogos da Copa")
try:
    res_copa = supabase.table("copa_ligafut").select("*").order("numero").execute()
    jogos = res_copa.data

    if not jogos:
        st.info("Nenhum jogo encontrado. Gere a copa para iniciar.")
    else:
        fases = sorted(set(j["fase"] for j in jogos), key=lambda x: ["Preliminar", "Oitavas", "Quartas", "Semifinal", "Final"].index(x))
        for fase in fases:
            st.markdown(f"### 🌟 Fase: {fase}")
            jogos_fase = [j for j in jogos if j["fase"] == fase]

            for j in jogos_fase:
                m_id = j.get("id_mandante")
                v_id = j.get("id_visitante")

                m_nome = times_map.get(m_id, {}).get("nome", m_id if m_id else "?")
                v_nome = times_map.get(v_id, {}).get("nome", v_id if v_id else "?")
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
    st.error(f"Erro ao carregar jogos: {e}")
