if rodadas_existentes:
    st.subheader("📝 Editar Resultados das Rodadas")
    lista_numeros = [r["numero"] for r in rodadas_existentes]
    rodada_escolhida = st.selectbox("Rodada", lista_numeros)
    rodada = next(r for r in rodadas_existentes if r["numero"] == rodada_escolhida)
    times_map = obter_nomes_times()

    for jogo in rodada["jogos"]:
        mandante = jogo["mandante"]
        visitante = jogo["visitante"]
        nome_m = times_map.get(mandante, "FOLGA" if mandante == "FOLGA" else "?")
        nome_v = times_map.get(visitante, "FOLGA" if visitante == "FOLGA" else "?")
        gols_mandante = jogo.get("gols_mandante") or 0
        gols_visitante = jogo.get("gols_visitante") or 0

        with st.container():
            st.markdown(f"### ⚔️ {nome_m} vs {nome_v}")

            if "FOLGA" in [mandante, visitante]:
                st.markdown("🚫 Este time folgou nesta rodada.")
                continue

            col1, col2, col3 = st.columns([4, 1, 4])
            with col1:
                gm = st.number_input("Gols Mandante", min_value=0, value=gols_mandante, key=f"gm_{mandante}_{visitante}")
            with col2:
                st.markdown("**x**")
            with col3:
                gv = st.number_input("Gols Visitante", min_value=0, value=gols_visitante, key=f"gv_{mandante}_{visitante}")

            if st.button("💾 Salvar resultado", key=f"salvar_{mandante}_{visitante}"):
                novos_jogos = []
                for j in rodada["jogos"]:
                    if j["mandante"] == mandante and j["visitante"] == visitante:
                        j["gols_mandante"] = gm
                        j["gols_visitante"] = gv
                    novos_jogos.append(j)

                supabase.table(nome_tabela_rodadas).update({"jogos": novos_jogos}).eq("numero", rodada_escolhida).execute()
                st.success(f"✅ Resultado salvo: {nome_m} {gm} x {gv} {nome_v}")
                st.rerun()

