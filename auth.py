# modules/auth.py
import streamlit as st
import bcrypt
import pandas as pd
import time
from database import run_query

# --- 1. FUNCIONES AUXILIARES (Lógica) ---

def check_admin_exists():
    """Crea admin por defecto si no existe"""
    if not run_query("SELECT id FROM usuarios WHERE username=%s", ('admin',)):
        # La contraseña por defecto es: admin123
        h = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        run_query("INSERT INTO usuarios (username, nombre_completo, password_hash, rol) VALUES (%s,%s,%s,%s)", ('admin', 'System Admin', h, 'admin'))

def login_user(user, password):
    """Verifica usuario y contraseña en la BD"""
    res = run_query("SELECT * FROM usuarios WHERE username=%s AND estado=1", (user,))
    if res:
        u_data = res[0]
        # Verificamos el hash
        if bcrypt.checkpw(password.encode(), bytes(u_data['password_hash'])):
            return u_data
    return None

# --- 2. PANTALLA DE LOGIN (Lo que se ve al entrar) ---

def show_login_screen():
    # AQUÍ ES DONDE CAMBIAMOS EL TÍTULO PRINCIPAL
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>⛰️ Pukamani</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Sistema de Control de Costos Mineros</p>", unsafe_allow_html=True)
        st.divider()
        
        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            
            if st.form_submit_button("Ingresar al Sistema", type="primary"):
                user_data = login_user(u, p)
                if user_data:
                    st.session_state['authenticated'] = True
                    st.session_state['usuario'] = user_data['username']
                    st.session_state['rol'] = user_data['rol']
                    st.session_state['user_id'] = user_data['id']
                    st.success(f"¡Bienvenido, {user_data['nombre_completo']}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")

# --- 3. PANTALLA DE GESTIÓN DE USUARIOS (Solo Admins) ---

def show_users_manager():
    st.title("👤 Gestión de Usuarios - Pukamani")
    
    with st.expander("➕ Crear Nuevo Usuario", expanded=False):
        with st.form("new_u"):
            u = st.text_input("Usuario (Login)")
            n = st.text_input("Nombre Completo")
            p = st.text_input("Contraseña", type="password")
            r = st.selectbox("Rol", ["digitador", "lector", "admin"])
            
            if st.form_submit_button("Crear Usuario"):
                if u and p and n:
                    try:
                        h = bcrypt.hashpw(p.encode(), bcrypt.gensalt())
                        run_query("INSERT INTO usuarios (username, nombre_completo, password_hash, rol) VALUES (%s,%s,%s,%s)", (u, n, h, r))
                        st.success(f"✅ Usuario {u} creado correctamente.")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Completa todos los campos.")
                
    st.divider()
    st.subheader("Lista de Usuarios Activos")
    df = pd.DataFrame(run_query("SELECT id, username, nombre_completo, rol, estado FROM usuarios ORDER BY id"))
    st.dataframe(df, use_container_width=True)