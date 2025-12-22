# auth.py
import streamlit as st
import bcrypt
import pandas as pd
from database import run_query

def check_admin_exists():
    """Crea admin por defecto si no existe"""
    if not run_query("SELECT id FROM usuarios WHERE username=%s", ('admin',)):
        h = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        run_query("INSERT INTO usuarios (username, nombre_completo, password_hash, rol) VALUES (%s,%s,%s,%s)", ('admin', 'System Admin', h, 'admin'))

def login_user(user, password):
    res = run_query("SELECT * FROM usuarios WHERE username=%s AND estado=1", (user,))
    if res:
        u_data = res[0]
        if bcrypt.checkpw(password.encode(), bytes(u_data['password_hash'])):
            return u_data
    return None

def show_users_manager():
    st.title("🔐 Acceso al Sistema Pukamani")
    
    with st.form("new_u"):
        u = st.text_input("Usuario (Login)")
        n = st.text_input("Nombre Completo")
        p = st.text_input("Contraseña", type="password")
        r = st.selectbox("Rol", ["digitador", "lector", "admin"])
        
        if st.form_submit_button("Crear Usuario"):
            try:
                h = bcrypt.hashpw(p.encode(), bcrypt.gensalt())
                run_query("INSERT INTO usuarios (username, nombre_completo, password_hash, rol) VALUES (%s,%s,%s,%s)", (u, n, h, r))
                st.success(f"Usuario {u} creado.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
                
    st.divider()
    df = pd.DataFrame(run_query("SELECT id, username, nombre_completo, rol, estado FROM usuarios ORDER BY id"))
    st.dataframe(df, use_container_width=True)