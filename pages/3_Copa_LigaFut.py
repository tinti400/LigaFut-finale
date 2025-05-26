
 # -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import random

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🏆 Copa LigaFut", page_icon="🏆", layout="centered")
st.title("🏆 Gerar Copa LigaFut (Mata-mata)")

# 🔐 Verifica login e permissão
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

if not eh_admin:
    st.warning("🔒 Apenas administradores podem gerar a Copa.")
    st.stop()

# 📊 Buscar todos os times da Liga (1ª e 2ª divisão)
res = supabase.table("usuarios").select("time_id").execute()
time_ids = list({u["time_id"] for u in res.data if u.get("time_id")})

if len(time_ids) < 2:
    st.warning("⚠️ Mínimo de 2 times para gerar a Copa.")
    st.stop()

# 📊 Gerar confrontos
if st.button("⚙️ Gerar Copa LigaFut"):
    try:
        supabase.table("copa_ligafut").delete().neq("numero_fase", -1).execute()

        random.shuffle(time_ids)
        fase_numero = 1
        jogos = []
        fase = "Oitavas de Final"

        # Ajustar para múltiplos de 2 com fase preliminar
        total = len(time_ids)
        while (total & (total - 1)) != 0:  # não é potência de 2
            total += 1

        byes = total - len(time_ids)
        participantes = time_ids[:]

        if byes > 0:
            st.info(f"🎟 {byes} times avançarão automaticamente para a próxima fase.")
            for i in range(byes):
                jogos.append({
                    "numero_fase": fase_numero,
                    "fase": "Bye",
                    "numero_jogo": i + 1,
                    "id_mandante": participantes.pop(),
                    "id_visitante": None,
                    "gols_mandante": None,
                    "gols_visitante": None,
                    "vencedor": None
                })

        # Confrontos iniciais
        numero_jogo = 1
        for i in range(0, len(participantes), 2):
            jogos.append({
                "numero_fase": fase_numero,
                "fase": fase,
                "numero_jogo": numero_jogo,
                "id_mandante": participantes[i],
                "id_visitante": participantes[i+1],
                "gols_mandante": None,
                "gols_visitante": None,
                "vencedor": None
            })
            numero_jogo += 1

        supabase.table("copa_ligafut").insert(jogos).execute()
        st.success(f"✅ Copa LigaFut criada com {len(jogos)} confrontos iniciais!")

    except Exception as e:
        st.error(f"Erro ao gerar a copa: {e}")
