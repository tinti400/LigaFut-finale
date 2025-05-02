from supabase import create_client
import random

# 🔐 Conexão com o Supabase
url = "https://hceqyuvryhtihhbvacyo.supabase.co"  # URL do seu Supabase
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhjZXF5dXZyeWh0aWhoYnZhY3lvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTQ0NDgwNCwiZXhwIjoyMDYxMDIwODA0fQ.zzQs8YobpxZeFdWJhSyh34I_tzW_tUciEAsTat8setg"  # A chave que você forneceu
supabase = create_client(url, key)

# Função para gerar e cadastrar usuários
def gerar_usuarios(qtd_usuarios, divisao="Divisão 1"):
    # Buscar times cadastrados
    res_times = supabase.table("Times").select("id").execute()
    time_ids = [t["id"] for t in res_times.data]

    if len(time_ids) < 2:
        print("É necessário pelo menos 2 times cadastrados!")
        return

    # Gerar e cadastrar usuários
    for i in range(qtd_usuarios):
        usuario = f"usuario{i + 1}@ligafut.com"  # Exemplo de email gerado automaticamente
        senha = f"senha{i + 1}"  # Senha simples

        # Verifica se o usuário já existe
        res_usuario = supabase.table("usuarios").select("usuario").eq("usuario", usuario).execute()

        if res_usuario.data:  # Se o usuário já existir, pula a criação
            print(f"Usuário {usuario} já existe. Pulando criação.")
            continue

        # Atribui um time aleatório
        time_id = random.choice(time_ids)

        # Cadastra o novo usuário
        supabase.table("usuarios").insert({
            "usuario": usuario,
            "senha": senha,
            "time_id": time_id,
            "divisao": divisao
        }).execute()

        print(f"Usuário {usuario} criado com sucesso e associado ao time {time_id}!")

# Chamar a função para gerar 5 usuários para teste (altere a quantidade conforme necessário)
gerar_usuarios(5, divisao="Divisão 1")

