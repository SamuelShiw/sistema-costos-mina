# app.py
import streamlit as st
from auth import login_user, check_admin_exists, show_users_manager
from modules.registro import show_registro
from modules.dashboard import show_dashboard
from modules.maestros import show_maestros

# Configuración Inicial
st.set_page_config(page_title="MineCost v10.1", page_icon="⛏️", layout="wide")

# Inicializar Sesión
if 'usuario' not in st.session_state: st.session_state.update({'usuario': None, 'rol': None, 'nombre': None})

# Verificar Admin al inicio
try: check_admin_exists()
except: pass

def logout():
    st.session_state.update({'usuario': None, 'rol': None, 'nombre': None})
    st.rerun()

# --- LÓGICA DE NAVEGACIÓN ---
if st.session_state['usuario'] is None:
    # PANTALLA DE LOGIN
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<h1 style='text-align:center;'>⛏️ MineCost v10.1</h1>", unsafe_allow_html=True)
        st.info("Sistema Modular Cloud")
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("INGRESAR", type="primary"):
                user = login_user(u, p)
                if user:
                    st.session_state['usuario'] = user['username']
                    st.session_state['rol'] = user['rol']
                    st.session_state['nombre'] = user['nombre_completo']
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
else:
    # SISTEMA DENTRO
    with st.sidebar:
        st.title(f"Hola, {st.session_state['nombre'].split()[0]}")
        rol = st.session_state['rol']
        
        if rol == 'admin': st.success("🔑 ADMIN")
        elif rol == 'digitador': st.info("✏️ DIGITADOR")
        else: st.warning("👁️ LECTOR")
        
        st.divider()
        menu_opts = []
        if rol in ['admin', 'digitador']: menu_opts.append("📝 Registro")
        if rol in ['admin', 'lector', 'digitador']: menu_opts.append("📊 Dashboard")
        if rol == 'admin': 
            menu_opts.append("⚙️ Maestros")
            menu_opts.append("👥 Usuarios")
            
        selection = st.radio("Menú", menu_opts)
        st.divider()
        if st.button("Cerrar Sesión"): logout()

    # ENRUTADOR DE MÓDULOS
    if selection == "📝 Registro":
        show_registro()
    elif selection == "📊 Dashboard":
        show_dashboard()
    elif selection == "⚙️ Maestros":
        show_maestros()
    elif selection == "👥 Usuarios":
        show_users_manager()