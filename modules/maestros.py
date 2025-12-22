# modules/maestros.py
import streamlit as st
import pandas as pd
import time
import yfinance as yf  # <--- IMPORTANTE: La nueva librería
from database import run_query

def obtener_datos_yahoo():
    """Conecta con Yahoo Finance para traer Dólar y Oro"""
    try:
        # 1. Traer Dólar (PEN=X)
        dolar_ticker = yf.Ticker("PEN=X")
        dolar_data = dolar_ticker.history(period="1d")
        if dolar_data.empty: return None, None
        precio_dolar = float(dolar_data['Close'].iloc[-1])

        # 2. Traer Oro (GC=F -> Futuros de Oro en USD/Onza)
        oro_ticker = yf.Ticker("GC=F")
        oro_data = oro_ticker.history(period="1d")
        if oro_data.empty: return None, None
        precio_oro_usd_oz = float(oro_data['Close'].iloc[-1])

        # 3. Conversión: De USD/Onza a PEN/Gramo
        # 1 Onza Troy = 31.1035 gramos
        precio_oro_pen_oz = precio_oro_usd_oz * precio_dolar
        precio_oro_pen_gramo = precio_oro_pen_oz / 31.1035

        return round(precio_dolar, 3), round(precio_oro_pen_gramo, 2)

    except Exception as e:
        st.error(f"Error conectando a Yahoo Finance: {e}")
        return None, None

def show_maestros():
    st.title("⚙️ Maestro de Configuración")

    # --- NOTIFICACIONES (TOAST) ---
    if 'mensaje_exito' in st.session_state:
        st.toast(st.session_state['mensaje_exito'], icon="✅")
        st.success(st.session_state['mensaje_exito'])
        del st.session_state['mensaje_exito']

    # --- VARIABLES ECONÓMICAS ---
    # 1. Obtenemos valores actuales de la Base de Datos
    res_dol = run_query("SELECT valor FROM configuracion WHERE clave='DOLAR_CAMBIO'")
    val_dol = float(res_dol[0]['valor']) if res_dol else 3.75
    res_oro = run_query("SELECT valor FROM configuracion WHERE clave='PRECIO_ORO_GRAMO'")
    val_oro = float(res_oro[0]['valor']) if res_oro else 260.00
    
    with st.expander("💰 Variables Económicas (Dólar y Oro)", expanded=False):
        st.caption("Puedes escribir manualmente o descargar de internet.")
        
        # --- BOTÓN MÁGICO DE INTERNET ---
        col_btn, col_info = st.columns([1, 2])
        with col_btn:
            if st.button("🔄 Actualizar desde Internet", type="secondary"):
                with st.spinner("Conectando con Bolsa de Valores..."):
                    nuevo_dolar, nuevo_oro = obtener_datos_yahoo()
                    if nuevo_dolar and nuevo_oro:
                        # Guardamos en BD automáticamente
                        run_query("INSERT INTO configuracion (clave, valor) VALUES ('DOLAR_CAMBIO', %s) ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor", (nuevo_dolar,))
                        run_query("INSERT INTO configuracion (clave, valor) VALUES ('PRECIO_ORO_GRAMO', %s) ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor", (nuevo_oro,))
                        st.session_state['mensaje_exito'] = f"✅ Actualizado: Dólar S/{nuevo_dolar} | Oro S/{nuevo_oro}/gr"
                        st.rerun()
                    else:
                        st.error("No se pudo obtener datos de internet. Revisa tu conexión.")

        # FORMULARIO MANUAL (Por si no hay internet o quieren ajustar)
        with st.form("vars"):
            c1, c2 = st.columns(2)
            nd = c1.number_input("Dólar (S/)", value=val_dol, step=0.001, format="%.3f")
            no = c2.number_input("Oro (S/ gramo)", value=val_oro, step=0.1, format="%.2f")
            
            if st.form_submit_button("💾 Guardar Manualmente"):
                run_query("INSERT INTO configuracion (clave, valor) VALUES ('DOLAR_CAMBIO', %s) ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor", (nd,))
                run_query("INSERT INTO configuracion (clave, valor) VALUES ('PRECIO_ORO_GRAMO', %s) ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor", (no,))
                st.session_state['mensaje_exito'] = "Variables guardadas manualmente."
                st.rerun()

    st.divider()

    # --- GESTIÓN DE INSUMOS ---
    st.subheader("1. Maestro de Insumos")
    
    data = run_query("SELECT id, nombre, unidad, precio, categoria, activo FROM insumos ORDER BY categoria, nombre")
    df_ins = pd.DataFrame(data) if data else pd.DataFrame(columns=['id', 'nombre', 'unidad', 'precio', 'categoria', 'activo'])

    if not df_ins.empty:
        df_ins['precio'] = df_ins['precio'].astype(float)
        df_ins['activo'] = df_ins['activo'].astype(bool)
        df_ins['id'] = df_ins['id'].astype(float)

    edited_ins = st.data_editor(
        df_ins, 
        key="editor_insumos", 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "id": st.column_config.NumberColumn(disabled=True),
            "precio": st.column_config.NumberColumn(format="S/ %.2f"),
            "categoria": st.column_config.SelectboxColumn(
                "Categoría",
                width="medium",
                options=["Explosivos", "Accesorios", "Madera", "Aceros", "Otros"],
                required=True
            )
        }
    )
    
    if st.button("💾 Guardar Cambios en Insumos", type="primary"):
        try:
            cambios = 0
            nuevos_nombres = [] 
            for index, row in edited_ins.iterrows():
                es_nuevo = pd.isna(row['id']) or row['id'] == 0
                nombre = row['nombre']; unidad = row['unidad']; precio = row['precio']; cat = row['categoria']; activo = 1 if row['activo'] else 0
                
                if nombre and cat: 
                    if es_nuevo:
                        run_query("INSERT INTO insumos (nombre, unidad, precio, categoria, activo) VALUES (%s,%s,%s,%s,%s)", (nombre, unidad, precio, cat, activo))
                        nuevos_nombres.append(nombre)
                        cambios += 1
                    else:
                        run_query("UPDATE insumos SET nombre=%s, unidad=%s, precio=%s, categoria=%s, activo=%s WHERE id=%s", (nombre, unidad, precio, cat, activo, row['id']))
                        cambios += 1
            
            if cambios > 0:
                if nuevos_nombres: st.session_state['mensaje_exito'] = f"✨ Se agregaron: {', '.join(nuevos_nombres)}"
                else: st.session_state['mensaje_exito'] = "✅ Datos guardados."
                st.rerun()
            else: st.info("Sin cambios.")
        except Exception as e: st.error(f"Error: {e}")

    st.divider()

    # --- GESTIÓN DE LABORES ---
    st.subheader("2. Maestro de Labores")
    col_tab, col_form = st.columns([1, 1])
    with col_tab:
        df_frentes = pd.DataFrame(run_query("SELECT codigo, tipo, estado, zona FROM frentes ORDER BY codigo"))
        st.dataframe(df_frentes, use_container_width=True, height=300)
    with col_form:
        opcion = st.radio("Acción", ["Crear Nueva", "Editar Existente"], horizontal=True)
        tipos = ["Tajeo", "Subnivel", "Galería", "Chimenea", "Rampa", "Pique", "Crucero", "ByPass", "Cámara"]
        if opcion == "Crear Nueva":
            with st.form("add_labor"):
                nc = st.text_input("Código"); nt = st.selectbox("Tipo", tipos); nz = st.text_input("Zona/Nivel")
                if st.form_submit_button("Crear"):
                    if run_query("INSERT INTO frentes (codigo, tipo, zona, estado) VALUES (%s,%s,%s,'ACTIVO')", (nc,nt,nz)):
                        st.session_state['mensaje_exito'] = f"✅ Labor {nc} creada."
                        st.rerun()
        else:
            ls = [f['codigo'] for f in run_query("SELECT codigo FROM frentes")]
            sel = st.selectbox("Seleccionar Labor", ls)
            if sel:
                curr = run_query("SELECT * FROM frentes WHERE codigo=%s", (sel,))[0]
                with st.form("edit_labor"):
                    et = st.selectbox("Tipo", tipos, index=tipos.index(curr['tipo']) if curr['tipo'] in tipos else 0)
                    es = st.selectbox("Estado", ["ACTIVO", "STANDBY", "CERRADO"], index=["ACTIVO", "STANDBY", "CERRADO"].index(curr['estado']))
                    ez = st.text_input("Zona", value=curr['zona'] if curr['zona'] else "")
                    if st.form_submit_button("Actualizar"):
                        run_query("UPDATE frentes SET tipo=%s, estado=%s, zona=%s WHERE codigo=%s", (et,es,ez,sel))
                        st.session_state['mensaje_exito'] = f"✅ Labor {sel} actualizada."
                        st.rerun()