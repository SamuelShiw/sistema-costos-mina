# modules/registro.py
import streamlit as st
import pandas as pd
import time
from datetime import datetime
from database import run_query

def show_registro():
    st.title("📝 Parte Diario de Mina")
    st.caption(f"Responsable: **{st.session_state['nombre']}**")
    
    # Cargar Datos Maestros
    frentes_data = run_query("SELECT id, codigo FROM frentes WHERE estado='ACTIVO'")
    if not frentes_data:
        st.warning("⚠️ No hay labores activas. Ve al Panel Maestro para crearlas.")
        return

    frentes_codigos = [f['codigo'] for f in frentes_data]
    insumos_db = run_query("SELECT * FROM insumos WHERE activo=1 ORDER BY categoria, nombre")
    
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
                    # Obtener IDs
                    fid = run_query("SELECT id FROM frentes WHERE codigo=%s", (labor,))[0]['id']
                    uid = run_query("SELECT id FROM usuarios WHERE username=%s", (st.session_state['usuario'],))[0]['id']
                    
                    saved_count = 0
                    # 1. Guardar Insumos
                    for iid, qty in consumos.items():
                        if qty > 0:
                            # Solo guardamos Avance/TM en la primera fila del lote para no duplicar en sumas simples
                            av_val = avance if saved_count == 0 else 0
                            tm_val = tm if saved_count == 0 else 0
                            
                            run_query("""
                                INSERT INTO consumo_diario 
                                (fecha, guardia, frente_id, insumo_id, cantidad, avance_metros, tonelaje, usuario_id)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (fecha, guardia, fid, iid, qty, av_val, tm_val, uid))
                            saved_count += 1
                    
                    # 2. Si solo hubo avance/mineral sin consumo
                    if saved_count == 0 and (avance > 0 or tm > 0):
                        run_query("""
                            INSERT INTO consumo_diario 
                            (fecha, guardia, frente_id, insumo_id, cantidad, avance_metros, tonelaje, usuario_id)
                            VALUES (%s, %s, %s, NULL, 0, %s, %s, %s)
                        """, (fecha, guardia, fid, avance, tm, uid))
                        saved_count += 1
                        
                    if saved_count > 0:
                        st.success("✅ Guardado exitosamente.")
                        time.sleep(1); st.rerun()
                    else:
                        st.warning("⚠️ El registro está vacío.")
                        
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

    # --- PESTAÑA 2: HISTORIAL ---
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
                    run_query("DELETE FROM consumo_diario WHERE id=%s", (row['id'],))
                    st.warning("Eliminado."); time.sleep(0.5); st.rerun()
                st.divider()
        else:
            st.info("No hay registros recientes.")