# app.py
import streamlit as st

# 1. Configuración de la Página
st.set_page_config(
    page_title="💎 CORE - Sistema Minero", 
    page_icon="⛰️", 
    layout="wide"
)

# Importamos los módulos
from modules.auth import show_login_screen, check_admin_exists, show_users_manager
from modules.dashboard import show_dashboard
# Importamos registro para que el Admin pueda usarlo también
from modules.registro import show_registro 

try:
    from modules.maestros import show_maestros
except ImportError:
    pass

def main():
    check_admin_exists()
    
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
        
    # --- LOGICA DE NAVEGACIÓN ---
    
    if not st.session_state['authenticated']:
        show_login_screen()
        
    else:
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/1048/1048950.png", width=100)
            
            # AQUI CAMBIAMOS PARA QUE DIGA TU NOMBRE REAL (Ej: Alexander)
            nombre_mostrar = st.session_state.get('nombre', st.session_state.get('usuario'))
            st.title(f"Hola, {nombre_mostrar}")
            
            st.write(f"Rol: **{st.session_state.get('rol', 'N/A').upper()}**")
            st.divider()
            
            # DEFINICIÓN DEL MENÚ SEGÚN EL ROL
            rol = st.session_state['rol']
            
            if rol == 'admin':
                # EL ADMIN AHORA TIENE ACCESO A TODO
                opciones = ["📊 Dashboard", "📝 Registros", "⚙️ Maestros", "👤 Usuarios"]
            elif rol == 'digitador':
                opciones = ["📝 Registros", "📊 Dashboard"]
            else:
                opciones = ["📊 Dashboard"]
                
            menu = st.radio("Navegación", opciones)
            
            st.divider()
            if st.button("🔴 Cerrar Sesión"):
                st.session_state['authenticated'] = False
                st.rerun()

        # --- MOSTRAR PANTALLAS ---
        if menu == "📊 Dashboard":
            show_dashboard()
            
        elif menu == "📝 Registros":
            show_registro()
            
        elif menu == "⚙️ Parámetros":
            show_maestros()
            
        elif menu == "👤 Usuarios":
            show_users_manager()

if __name__ == "__main__":
    main()