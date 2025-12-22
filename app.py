# app.py
import streamlit as st

# 1. Configuración de la Página
st.set_page_config(
    page_title="Pukamani - Sistema Minero", 
    page_icon="⛰️", 
    layout="wide"
)

# Importamos los módulos
# NOTA: Esto fallará si auth.py no tiene la función show_login_screen
from modules.auth import show_login_screen, check_admin_exists, show_users_manager
from modules.dashboard import show_dashboard

try:
    from modules.maestros import show_maestros
except ImportError:
    pass

def main():
    # Asegurar que existe el admin
    check_admin_exists()
    
    # Inicializar estado de sesión
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
        
    # --- LOGICA DE NAVEGACIÓN ---
    if not st.session_state['authenticated']:
        # CASO A: NO ESTÁ LOGUEADO -> Muestra Login
        show_login_screen()
        
    else:
        # CASO B: YA ENTRÓ AL SISTEMA -> Muestra Menú Lateral
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/1048/1048950.png", width=100)
            st.title(f"Hola, {st.session_state.get('usuario', 'Minero')}")
            st.write(f"Rol: **{st.session_state.get('rol', 'N/A')}**")
            st.divider()
            
            menu = st.radio("Navegación", ["📊 Dashboard", "⚙️ Maestros", "👤 Usuarios"])
            
            st.divider()
            if st.button("🔴 Cerrar Sesión"):
                st.session_state['authenticated'] = False
                st.rerun()

        # Muestra la pantalla seleccionada
        if menu == "📊 Dashboard":
            show_dashboard()
        elif menu == "⚙️ Maestros":
            if st.session_state['rol'] == 'admin':
                try:
                    show_maestros()
                except:
                    st.warning("Módulo Maestros no cargado.")
            else:
                st.warning("⚠️ Acceso restringido a Administradores")
        elif menu == "👤 Usuarios":
            if st.session_state['rol'] == 'admin':
                show_users_manager()
            else:
                st.warning("⚠️ Acceso restringido a Administradores")

if __name__ == "__main__":
    main()