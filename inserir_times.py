from supabase import create_client, Client

url = "https://hceqyuvryhtihhbvacyo.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhjZXF5dXZyeWh0aWhoYnZhY3lvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTQ0NDgwNCwiZXhwIjoyMDYxMDIwODA0fQ.zzQs8YobpxZeFdWJhSyh34I_tzW_tUciEAsTat8setg"

supabase: Client = create_client(url, key)

# Lista de times para inserir
times = [
    {"nome": "Palmeiras", "saldo": 350000000.0, "tecnico": "Abel Ferreira"},
    {"nome": "Flamengo", "saldo": 350000000.0, "tecnico": "Tite"},
    {"nome": "São Paulo", "saldo": 350000000.0, "tecnico": "Zubeldía"},
    {"nome": "Atlético-MG", "saldo": 350000000.0, "tecnico": "Milito"},
    {"nome": "Grêmio", "saldo": 350000000.0, "tecnico": "Renato Gaúcho"},
    {"nome": "Cruzeiro", "saldo": 350000000.0, "tecnico": "Larcamón"},
    {"nome": "Internacional", "saldo": 350000000.0, "tecnico": "Coudet"},
    {"nome": "Botafogo", "saldo": 350000000.0, "tecnico": "Artur Jorge"},
    {"nome": "Bahia", "saldo": 350000000.0, "tecnico": "Rogério Ceni"},
    {"nome": "Fortaleza", "saldo": 350000000.0, "tecnico": "Vojvoda"},
]

# Inserindo os times
try:
    for time in times:
        response = supabase.table("Times").insert(time).execute()
        print(f"✅ Inserido: {time['nome']}")
except Exception as e:
    print("❌ Erro ao inserir times:", e)
