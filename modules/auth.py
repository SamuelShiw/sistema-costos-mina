# modules/auth.py
import streamlit as st
import bcrypt
import pandas as pd
import time
from database import run_query

def check_admin_exists():
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

# --- ESTA ES LA FUNCIÓN QUE FALTABA Y CAUSABA EL ERROR ---
def show_login_screen():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>⛰️ Pukamani</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Sistema de Control de Costos</p>", unsafe_allow_html=True)
        st.divider()
        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", type="primary"):
                user_data = login_user(u, p)
                if user_data:
                    st.session_state['authenticated'] = True
                    st.session_state['usuario'] = user_data['username']
                    # --- AGREGA ESTA LÍNEA NUEVA AQUÍ ABAJO: ---
                    st.session_state['nombre'] = user_data['nombre_completo'] 
                    # -------------------------------------------
                    st.session_state['rol'] = user_data['rol']
                    st.session_state['user_id'] = user_data['id']
                    
                    st.success(f"¡Bienvenido, {user_data['nombre_completo']}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

def show_users_manager():
    st.subheader("Gestión de Usuarios")
    with st.form("new_u"):
        u = st.text_input("Usuario")
        n = st.text_input("Nombre")
        p = st.text_input("Clave", type="password")
        r = st.selectbox("Rol", ["digitador", "lector", "admin"])
        if st.form_submit_button("Crear"):
            h = bcrypt.hashpw(p.encode(), bcrypt.gensalt())
            run_query("INSERT INTO usuarios (username, nombre_completo, password_hash, rol) VALUES (%s,%s,%s,%s)", (u, n, h, r))
            st.success("Usuario creado")
            st.rerun()
    st.dataframe(pd.DataFrame(run_query("SELECT username, rol FROM usuarios")))