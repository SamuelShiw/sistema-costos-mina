# database.py
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Establece la conexión segura con Supabase"""
    try:
        return psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            database=st.secrets["postgres"]["dbname"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            port=st.secrets["postgres"]["port"]
        )
    except Exception as e:
        st.error(f"🔌 Error crítico de conexión: {e}")
        st.stop()

def run_query(query, params=None):
    """Ejecuta una consulta SQL y maneja la transacción"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                return cur.fetchall()
            else:
                conn.commit()
                return True
    except Exception as e:
        st.error(f"❌ Error SQL: {e}")
        return None
    finally:
        conn.close()