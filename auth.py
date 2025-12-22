# modules/auth.py
# Actualizacion forzada para pukamani
import streamlit as st
import bcrypt
import pandas as pd
import time
from database import run_query

# --- 1. FUNCIONES DE BASE DE DATOS ---

def check_admin_exists():
    """Crea admin por defecto si no existe"""
    if not run_query("SELECT id FROM usuarios WHERE username=%s", ('admin',)):
        h = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        run_query("INSERT INTO usuarios (username, nombre_completo, password_hash, rol) VALUES (%s,%s,%s,%s)", ('admin', 'System Admin', h, 'admin'))

def login_user(user, password):
    """Verifica credenciales"""
    res = run_query("SELECT * FROM usuarios WHERE username=%s AND estado=1", (user,))
    if res:
        u_data = res[0]
        if bcrypt.checkpw(password.encode(), bytes(u_data['password_hash'])):
            return u_data
    return None

# --- 2. PANTALLA DE LOGIN (Esta es la función que faltaba) ---

def show_login_screen():
    # Diseño de columnas para centrar el login
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        # AQUÍ ESTÁ EL TÍTULO QUE QUERÍAS CAMBIAR
        st.markdown("<h1 style='text-align: center;'>⛰️ Pukamani</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Sistema de Control de Costos</p>", unsafe_allow_html=True)
        st.divider()
        
        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            
            if st.form_submit_button("Ingresar", type="primary"):
                user_data = login_user(u, p)
                if user_data:
                    # Guardamos los datos en la sesión
                    st.session_state['authenticated'] = True
                    st.session_state['usuario'] = user_data['username']
                    st.session_state['rol'] = user_data['rol']
                    st.session_state['user_id'] = user_data['id']
                    
                    st.success(f"¡Bienvenido, {user_data['nombre_completo']}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")

# --- 3. GESTOR DE USUARIOS ---

def show_users_manager():
    st.subheader("👤 Gestión de Usuarios")
    
    with st.expander("Crear Nuevo Usuario"):
        with st.form("new_u"):
            u = st.text_input("Usuario")
            n = st.text_input("Nombre Completo")
            p = st.text_input("Contraseña", type="password")
            r = st.selectbox("Rol", ["digitador", "lector", "admin"])
            
            if st.form_submit_button("Crear"):
                if u and p:
                    try:
                        h = bcrypt.hashpw(p.encode(), bcrypt.gensalt())
                        run_query("INSERT INTO usuarios (username, nombre_completo, password_hash, rol) VALUES (%s,%s,%s,%s)", (u, n, h, r))
                        st.success(f"Usuario {u} creado.")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Faltan datos")
            
    st.dataframe(pd.DataFrame(run_query("SELECT username, nombre_completo, rol FROM usuarios")))