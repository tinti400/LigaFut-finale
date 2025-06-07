# utils.py
from supabase import create_client
from datetime import datetime
import pytz
import os

# 🔐 Conexão com Supabase
url = os.getenv("SUPABASE_URL") or st.secrets["supabase"]["url"]
key = os.getenv("SUPABASE_KEY") or st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 💰 Registrar movimentação financeira com atualização de saldo
def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None):
    """
    Registra movimentações financeiras e atualiza saldo do time.

    - tipo: Ex: "Transferência", "Leilão", "Mercado"
    - categoria: "Compra" ou "Venda"
    - valor: sempre positivo
    - origem: time de onde veio o jogador (opcional)
    - destino: time para onde foi o jogador (opcional)
    """
    try:
        # Buscar saldo atual
        res = supabase.table("times").select("saldo").eq("id", id_time).execute()
        if not res.data:
            return False

        saldo_atual = res.data[0]["saldo"]

        # Atualizar saldo
        if categoria.lower() == "compra":
            novo_saldo = saldo_atual - valor
        elif categoria.lower() == "venda":
            novo_saldo = saldo_atual + valor
        else:
            return False

        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

        # Data atual
        fuso_brasilia = pytz.timezone("America/Sao_Paulo")
        agora = datetime.now(fuso_brasilia).isoformat()

        # Registro
        registro = {
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "data": agora,
            "origem": origem,
            "destino": destino
        }

        supabase.table("movimentacoes").insert(registro).execute()
        return True
    except Exception:
        return False
