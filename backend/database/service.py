import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

async def StoreUser (email: str, hashed_password: str):
    response = supabase.table("users").insert({
        "email": email, 
        "password": hashed_password
        }).execute()
    return response.data[0]

async def getUser(email: str):
    response = supabase.table("users").select("*").eq("email", email).execute()
    return response.data[0] if response.data else None

