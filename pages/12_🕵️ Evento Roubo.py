# ✅ FASE 1 — INICIAR EVENTO (somente para admin)
if not ativo and fase == "inicio":
    st.subheader("🚨 Iniciar Evento de Roubo")
    st.markdown("Defina abaixo os limites para o evento:")

    novo_roubos = st.number_input("⚽ Quantos jogadores cada time pode roubar?", min_value=1, max_value=10, value=3, step=1)
    novo_bloqueios = st.number_input("🛡️ Quantos jogadores cada time pode proteger?", min_value=1, max_value=10, value=4, step=1)
    novo_perdas = st.number_input("❌ Quantos jogadores cada time pode perder no máximo?", min_value=1, max_value=10, value=4, step=1)

    # 🔄 Botão para iniciar o evento (somente admin)
    if eh_admin and st.button("✅ Iniciar Evento de Roubo"):
        try:
            # 🔁 Sorteia ordem de participação
            random.shuffle(times_data)
            ordem = [str(t["id"]) for t in times_data]

            # 🛠️ Monta o dicionário de configuração
            config = {
                "id": ID_CONFIG,
                "ativo": True,
                "fase": "bloqueio",
                "ordem": ordem,
                "vez": 0,
                "roubos": {},
                "bloqueios": {},
                "ultimos_bloqueios": {},
                "ja_perderam": {},
                "concluidos": [],
                "inicio": datetime.utcnow().isoformat(),
                "limite_bloqueios": int(novo_bloqueios),
                "limite_roubo": int(novo_roubos),
                "limite_perder": int(novo_perdas),
                "finalizado": False
            }

            # 💾 Salva no Supabase usando UPSERT (para evitar erro de update)
            supabase.table("configuracoes").upsert(config).execute()

            st.success("✅ Evento iniciado com sucesso!")
            st.experimental_rerun()

        except Exception as e:
            st.error(f"Erro ao iniciar o evento: {e}")
# ✅ FASE 2 — BLOQUEIOS
if ativo and fase == "bloqueio":
    st.subheader("🛡️ Proteção de Jogadores")
    st.markdown("Cada time pode proteger seus jogadores contra roubo.")

    limite = int(configuracao.get("limite_bloqueios", 4))
    bloqueios = configuracao.get("bloqueios", {})
    ultimos_bloqueios = configuracao.get("ultimos_bloqueios", {})

    meus_bloqueios = bloqueios.get(str(id_time), [])
    jogadores_elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data

    # 🔢 Exibe o limite e jogadores protegidos
    st.info(f"Você pode proteger até **{limite} jogadores**.")
    st.markdown("Selecione os jogadores que deseja proteger:")

    nomes_bloqueados = []
    for j in jogadores_elenco:
        if j["id"] in meus_bloqueios:
            nomes_bloqueados.append(j["nome"])

    # ✅ Interface de múltipla seleção
    opcoes = [f"{j['nome']} ({j['posicao']}, OVR {j.get('overall', '-')})" for j in jogadores_elenco]
    map_id_por_nome = {f"{j['nome']} ({j['posicao']}, OVR {j.get('overall', '-')})": j["id"] for j in jogadores_elenco}
    selecionados = st.multiselect("👤 Selecione os jogadores para bloquear:", opcoes, default=nomes_bloqueados)

    # ✅ Validações
    if len(selecionados) > limite:
        st.error(f"Você só pode proteger até {limite} jogadores.")
    elif st.button("💾 Salvar Proteções"):
        try:
            ids_bloqueados = [map_id_por_nome[n] for n in selecionados]
            bloqueios[str(id_time)] = ids_bloqueados
            ultimos_bloqueios[str(id_time)] = ids_bloqueados

            supabase.table("configuracoes").update({
                "bloqueios": bloqueios,
                "ultimos_bloqueios": ultimos_bloqueios
            }).eq("id", ID_CONFIG).execute()

            st.success("✅ Proteções salvas com sucesso!")
            st.experimental_rerun()

        except Exception as e:
            st.error(f"Erro ao salvar proteções: {e}")

    # ✅ ADMIN AVANÇA PARA PRÓXIMA FASE
    if eh_admin:
        st.markdown("---")
        if st.button("➡️ Avançar para fase de ROUBO"):
            try:
                supabase.table("configuracoes").update({
                    "fase": "acao"
                }).eq("id", ID_CONFIG).execute()
                st.success("✅ Fase de proteção encerrada. Iniciando fase de roubo.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao avançar fase: {e}")
# ✅ FASE 3 — AÇÃO (ROUBO DE JOGADORES)
if ativo and fase == "acao":
    st.subheader("🕵️ Fase de Ação - Roubo de Jogadores")
    vez = int(configuracao.get("vez", 0))
    ordem = configuracao.get("ordem", [])
    concluido = str(id_time) in configuracao.get("concluidos", [])
    limite_roubos = int(configuracao.get("limite_roubo", 3))
    limite_perder = int(configuracao.get("limite_perder", 4))
    bloqueios = configuracao.get("bloqueios", {})
    ja_perderam = configuracao.get("ja_perderam", {})

    # 👉 ID do time da vez
    id_time_vez = ordem[vez] if vez < len(ordem) else None

    if str(id_time) != id_time_vez:
        st.info("⏳ Aguarde sua vez de roubar jogadores.")
    elif concluido:
        st.success("✅ Você já concluiu sua fase de roubo.")
    else:
        st.markdown(f"🟢 É a sua vez! Você pode roubar até **{limite_roubos} jogadores**.")
        st.markdown("---")

        # 🔍 Lista de todos os outros times
        for time in times_data:
            id_adversario = str(time["id"])
            if id_adversario == str(id_time):
                continue

            nome_adversario = time["nome"]
            qtd_perdas = len(ja_perderam.get(id_adversario, []))
            if qtd_perdas >= limite_perder:
                continue  # Esse time já perdeu jogadores demais

            st.markdown(f"### 🔻 {nome_adversario}")

            # 📋 Buscar jogadores do elenco
            elenco = supabase.table("elenco").select("*").eq("id_time", id_adversario).execute().data
            protegidos = bloqueios.get(id_adversario, [])
            roubaveis = [j for j in elenco if j["id"] not in protegidos]

            if not roubaveis:
                st.markdown("_Nenhum jogador disponível para roubo._")
                continue

            for jogador in roubaveis:
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 2])
                with col1:
                    st.markdown(f"**{jogador['nome']}**")
                with col2:
                    st.markdown(f"📌 {jogador['posicao']}")
                with col3:
                    st.markdown(f"🎯 {jogador['overall']}")
                with col4:
                    st.markdown(f"💰 R$ {jogador['valor']:,}".replace(",", "."))
                with col5:
                    if st.button("🚨 Roubar", key=f"roubar_{jogador['id']}"):
                        try:
                            # ✅ Verifica limites
                            meus_roubos = configuracao.get("roubos", {}).get(str(id_time), [])
                            if len(meus_roubos) >= limite_roubos:
                                st.warning("❌ Limite de roubos atingido.")
                                st.stop()

                            # ✅ Atualiza config
                            configuracao["roubos"].setdefault(str(id_time), []).append(jogador["id"])
                            ja_perderam.setdefault(id_adversario, []).append(jogador["id"])

                            # 🔄 Transferência de jogador
                            supabase.table("elenco").update({
                                "id_time": id_time
                            }).eq("id", jogador["id"]).execute()

                            # 💾 Atualiza config no Supabase
                            supabase.table("configuracoes").update({
                                "roubos": configuracao["roubos"],
                                "ja_perderam": ja_perderam
                            }).eq("id", ID_CONFIG).execute()

                            st.success(f"✅ Jogador {jogador['nome']} roubado com sucesso!")
                            st.experimental_rerun()

                        except Exception as e:
                            st.error(f"Erro ao roubar jogador: {e}")

        # ✅ Botão para encerrar a vez
        if st.button("✅ Finalizar minha vez"):
            try:
                configuracao["concluidos"].append(str(id_time))
                proxima_vez = vez + 1
                nova_fase = "relatorio" if proxima_vez >= len(ordem) else "acao"

                supabase.table("configuracoes").update({
                    "concluidos": configuracao["concluidos"],
                    "vez": proxima_vez,
                    "fase": nova_fase
                }).eq("id", ID_CONFIG).execute()

                st.success("✅ Fase finalizada com sucesso.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao finalizar sua vez: {e}")

    # 🔒 Botão só para ADM finalizar evento manualmente (em caso de erro)
    if eh_admin:
        st.markdown("---")
        if st.button("❌ Encerrar Evento (Admin)"):
            try:
                supabase.table("configuracoes").update({
                    "fase": "relatorio",
                    "finalizado": True
                }).eq("id", ID_CONFIG).execute()
                st.success("Evento encerrado manualmente.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao encerrar manualmente: {e}")
# ✅ FASE 4 — RELATÓRIO FINAL
if ativo and fase == "relatorio":
    st.subheader("📋 Relatório Final do Evento Roubo")

    roubos = configuracao.get("roubos", {})
    ja_perderam = configuracao.get("ja_perderam", {})
    ordem = configuracao.get("ordem", [])
    times_por_id = {str(t["id"]): t["nome"] for t in times_data}

    st.markdown("### 🔄 Ordem de Participação")
    for i, id_ in enumerate(ordem):
        nome = times_por_id.get(str(id_), "Desconhecido")
        st.markdown(f"**{i+1}º - {nome}**")

    st.markdown("---")

    st.markdown("### 🔐 Jogadores Roubados por Time")

    if not roubos:
        st.info("Nenhum jogador foi roubado.")
    else:
        for id_ladrao, lista_jogadores in roubos.items():
            nome_ladrao = times_por_id.get(str(id_ladrao), "Desconhecido")
            st.markdown(f"#### 🟢 {nome_ladrao}")
            for id_jogador in lista_jogadores:
                res = supabase.table("elenco").select("*").eq("id", id_jogador).execute()
                if res.data:
                    jogador = res.data[0]
                    nome_jogador = jogador.get("nome", "")
                    posicao = jogador.get("posicao", "")
                    overall = jogador.get("overall", "")
                    valor = jogador.get("valor", 0)
                    st.markdown(f"- {nome_jogador} ({posicao}, OVR {overall}) — 💰 R$ {valor:,}".replace(",", "."))

    st.markdown("---")
    st.markdown("### 😵‍💫 Jogadores Perdidos por Time")

    if not ja_perderam:
        st.info("Nenhum time perdeu jogadores.")
    else:
        for id_perdedor, lista_jogadores in ja_perderam.items():
            nome_perdedor = times_por_id.get(str(id_perdedor), "Desconhecido")
            st.markdown(f"#### 🔴 {nome_perdedor}")
            for id_jogador in lista_jogadores:
                res = supabase.table("elenco").select("*").eq("id", id_jogador).execute()
                if res.data:
                    jogador = res.data[0]
                    nome_jogador = jogador.get("nome", "")
                    posicao = jogador.get("posicao", "")
                    overall = jogador.get("overall", "")
                    valor = jogador.get("valor", 0)
                    st.markdown(f"- {nome_jogador} ({posicao}, OVR {overall}) — 💰 R$ {valor:,}".replace(",", "."))

    # ✅ Botão para admins finalizarem o evento
    if eh_admin:
        st.markdown("---")
        if st.button("🧹 Finalizar e Limpar Evento"):
            try:
                supabase.table("configuracoes").update({
                    "evento_roubo_ativo": False,
                    "fase": None,
                    "ordem": [],
                    "vez": 0,
                    "bloqueios": {},
                    "ultimos_bloqueios": {},
                    "roubos": {},
                    "ja_perderam": {},
                    "concluidos": [],
                    "limite_roubo": 3,
                    "limite_perder": 4,
                    "limite_bloqueios": 4
                }).eq("id", ID_CONFIG).execute()
                st.success("✅ Evento finalizado e dados limpos.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao limpar evento: {e}")

