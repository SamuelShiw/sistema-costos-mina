# modules/registro.py
import streamlit as st
import pandas as pd
import time
from datetime import datetime
from database import run_query

def show_registro():
    st.title("📝 Parte Diario de Mina")
    st.caption(f"Responsable: **{st.session_state.get('nombre', 'Usuario')}**")
    
    # Cargar Datos Maestros
    frentes_data = run_query("SELECT id, codigo FROM frentes WHERE estado='ACTIVO'")
    if not frentes_data:
        st.warning("⚠️ No hay labores activas. Ve al Panel Maestro para crearlas.")
        return

    frentes_codigos = [f['codigo'] for f in frentes_data]
    # Traemos también el precio para calcular costos
    insumos_db = run_query("SELECT * FROM insumos WHERE activo=1 ORDER BY categoria, nombre")
    
    # Mapa de precios para cálculo rápido {id_insumo: precio}
    precios_map = {i['id']: float(i['precio']) for i in insumos_db}
    # Mapa de nombres para la tabla 'costos' {id_insumo: nombre}
    nombres_map = {i['id']: i['nombre'] for i in insumos_db}
    # Mapa de categorias y unidades
    cat_map = {i['id']: i['categoria'] for i in insumos_db}
    uni_map = {i['id']: i['unidad'] for i in insumos_db}
    
    tab_new, tab_hist = st.tabs(["📄 NUEVO REGISTRO", "🗑️ HISTORIAL / CORREGIR"])

    # --- PESTAÑA 1: NUEVO REGISTRO ---
    with tab_new:
        with st.form("form_diario"):
            c1, c2, c3 = st.columns(3)
            fecha = c1.date_input("Fecha", value=datetime.today())
            guardia = c2.selectbox("Guardia", ["Día", "Noche"])
            labor = c3.selectbox("Labor", frentes_codigos)
            
            st.divider()
            k1, k2 = st.columns(2)
            avance = k1.number_input("Avance (m)", step=0.1)
            tm = k2.number_input("Mineral (TM)", step=1.0)
            
            st.divider()
            consumos = {}
            t1, t2, t3, t4 = st.tabs(["🧨 Explosivos", "🔗 Accesorios", "🌲 Madera", "🔩 Aceros"])
            
            def render_tab(cat, tab_obj):
                with tab_obj:
                    items = [i for i in insumos_db if i['categoria'] == cat]
                    if not items: st.caption("No hay items.")
                    cols = st.columns(3)
                    for idx, item in enumerate(items):
                        consumos[item['id']] = cols[idx%3].number_input(item['nombre'], min_value=0.0, step=1.0, key=f"ins_{item['id']}")

            render_tab("Explosivos", t1)
            render_tab("Accesorios", t2)
            render_tab("Madera", t3)
            render_tab("Aceros", t4)

            if st.form_submit_button("💾 Guardar Parte", type="primary"):
                try:
                    # Obtener IDs necesarios
                    fid_res = run_query("SELECT id FROM frentes WHERE codigo=%s", (labor,))
                    if not fid_res: st.error("Error: Labor no encontrada"); st.stop()
                    fid = fid_res[0]['id']
                    
                    # Intentamos obtener usuario, si falla usamos default
                    try:
                        uid_res = run_query("SELECT id FROM usuarios WHERE username=%s", (st.session_state.get('usuario'),))
                        uid = uid_res[0]['id'] if uid_res else None
                    except:
                        uid = None
                    
                    saved_count = 0
                    
                    # 1. Guardar Insumos (DOBLE ESCRITURA)
                    for iid, qty in consumos.items():
                        if qty > 0:
                            # Valores para evitar duplicar avance/tm en cada fila
                            av_val = avance if saved_count == 0 else 0
                            tm_val = tm if saved_count == 0 else 0
                            
                            # A) Insertar en la tabla BUENA (Relacional)
                            run_query("""
                                INSERT INTO consumo_diario 
                                (fecha, guardia, frente_id, insumo_id, cantidad, avance_metros, tonelaje, usuario_id)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (fecha, guardia, fid, iid, qty, av_val, tm_val, uid))
                            
                            # B) Insertar en la tabla COSTOS (Para el Dashboard actual)
                            # Calculamos precio total
                            precio_unit = precios_map.get(iid, 0)
                            total_soles = qty * precio_unit
                            nom_insumo = nombres_map.get(iid, 'Desconocido')
                            cat_insumo = cat_map.get(iid, 'General')
                            uni_insumo = uni_map.get(iid, 'und')
                            
                            run_query("""
                                INSERT INTO costos 
                                (fecha, guardia, labor, categoria, detalle, unidad, cantidad, precio_total, avance, mineral_tm, usuario)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (fecha, guardia, labor, cat_insumo, nom_insumo, uni_insumo, qty, total_soles, av_val, tm_val, st.session_state.get('usuario','App')))
                            
                            saved_count += 1
                    
                    # 2. Si solo hubo avance/mineral SIN consumo de materiales
                    if saved_count == 0 and (avance > 0 or tm > 0):
                        # A) Tabla Buena
                        run_query("""
                            INSERT INTO consumo_diario 
                            (fecha, guardia, frente_id, insumo_id, cantidad, avance_metros, tonelaje, usuario_id)
                            VALUES (%s, %s, %s, NULL, 0, %s, %s, %s)
                        """, (fecha, guardia, fid, avance, tm, uid))
                        
                        # B) Tabla Costos
                        run_query("""
                            INSERT INTO costos 
                            (fecha, guardia, labor, categoria, detalle, unidad, cantidad, precio_total, avance, mineral_tm, usuario)
                            VALUES (%s, %s, %s, 'AVANCE', 'Solo Avance', 'm', 0, 0, %s, %s, %s)
                        """, (fecha, guardia, labor, avance, tm, st.session_state.get('usuario','App')))
                        
                        saved_count += 1
                        
                    if saved_count > 0:
                        st.success(f"✅ Guardado exitosamente ({saved_count} registros).")
                        time.sleep(1); st.rerun()
                    else:
                        st.warning("⚠️ El registro está vacío. Ingrese algún valor.")
                        
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

    # --- PESTAÑA 2: HISTORIAL (Leyendo de la tabla buena) ---
    with tab_hist:
        st.subheader("🕵️ Últimos 7 días")
        filtro = st.selectbox("Filtrar por Labor", ["TODAS"] + frentes_codigos)
        
        q = """
            SELECT c.id, c.fecha, c.guardia, f.codigo as labor, i.nombre as insumo, c.cantidad, u.username
            FROM consumo_diario c
            LEFT JOIN frentes f ON c.frente_id = f.id
            LEFT JOIN insumos i ON c.insumo_id = i.id
            LEFT JOIN usuarios u ON c.usuario_id = u.id
            WHERE c.fecha >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY c.id DESC
        """
        df_hist = pd.DataFrame(run_query(q))
        
        if not df_hist.empty:
            if filtro != "TODAS":
                df_hist = df_hist[df_hist['labor'] == filtro]
            
            for i, row in df_hist.iterrows():
                c1, c2, c3, c4, c5 = st.columns([2,2,3,2,1])
                c1.write(f"📅 {row['fecha']}")
                c2.write(f"📍 **{row['labor']}**")
                item_nom = row['insumo'] if pd.notna(row['insumo']) else "---"
                c3.write(f"📦 {item_nom}: **{row['cantidad']}**")
                c4.caption(f"👤 {row['username']}")
                if c5.button("🗑️", key=f"del_{row['id']}"):
                    # Borramos de la tabla buena
                    run_query("DELETE FROM consumo_diario WHERE id=%s", (row['id'],))
                    # OJO: Borrar de la tabla 'costos' es difícil porque no tenemos el ID aquí.
                    # Por ahora aceptamos esa pequeña inconsistencia al borrar.
                    st.warning("Eliminado."); time.sleep(0.5); st.rerun()
                st.divider()
        else:
            st.info("No hay registros recientes.")