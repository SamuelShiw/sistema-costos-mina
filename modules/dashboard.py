# modules/dashboard.py
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, time  # <-- AGREGADO: 'time' para manejar la hora final
from database import run_query
# Importamos el módulo de reportes que creaste
from modules.reportes import generar_excel_corporativo

def show_dashboard():
    # --- CAMBIO 1: Botón de actualización manual ---
    col_head, col_btn = st.columns([8,2])
    with col_head:
        st.title("💎 CORE - Control de Costos")
    with col_btn:
        if st.button("🔄 Actualizar Data"):
            st.cache_data.clear()
            st.rerun()
    # ---------------------------------------------
    
    # 1. Configuración y Filtros
    res = run_query("SELECT valor FROM configuracion WHERE clave='DOLAR_CAMBIO'")
    dolar = float(res[0]['valor']) if res else 3.75
    
    with st.expander("🔍 Filtros de Búsqueda", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        fi = c1.date_input("Desde", value=datetime.today().replace(day=1))
        ff = c2.date_input("Hasta", value=datetime.today())
        
        # Intentamos cargar lista de labores, si falla, lista vacía
        try:
            labs_data = run_query("SELECT nombre FROM labores WHERE estado=true")
            labs = [x['nombre'] for x in labs_data] if labs_data else []
        except:
            labs = []
            
        f_lab = c3.selectbox("Labor", ["TODOS"] + labs)
        f_gua = c4.selectbox("Guardia", ["TODOS", "Día", "Noche"])
        
    # 2. Consulta de Datos
    query = """
        SELECT 
            c.fecha, c.guardia, c.labor, c.categoria, c.detalle, c.unidad,
            c.cantidad, c.precio_total, c.avance, c.mineral_tm
        FROM costos c
        WHERE c.fecha BETWEEN %s AND %s
    """
    
    # --- CAMBIO 2: Ajuste de fecha final para incluir todo el día ---
    # Combinamos la fecha seleccionada con la hora 23:59:59
    ff_full = datetime.combine(ff, time(23, 59, 59))
    
    params = [fi, ff_full] # Usamos ff_full en lugar de ff
    # -------------------------------------------------------------
    
    if f_lab != "TODOS":
        query += " AND c.labor = %s"
        params.append(f_lab)
    if f_gua != "TODOS":
        query += " AND c.guardia = %s"
        params.append(f_gua)
        
    data = run_query(query, params)
    df = pd.DataFrame(data)
    
    if df.empty:
        st.warning("📭 No hay datos registrados en este rango de fechas.")
        return # Se detiene aquí si no hay datos

    # 3. Procesamiento de Datos (Limpieza)
    df.columns = [c.lower() for c in df.columns] # Todo a minúsculas
    cols_num = ['precio_total', 'avance', 'mineral_tm', 'cantidad']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    total_pen = df['precio_total'].sum()
    
    # Dataframe Agrupado
    df_agrupado = df.groupby(['labor']).agg({
        'avance': 'sum', 
        'mineral_tm': 'sum', 
        'precio_total': 'sum'
    }).reset_index()
    
    # 4. KPIs y Gráficos (Tu código visual)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Gasto Total (S/)", f"S/ {total_pen:,.0f}")
    k2.metric("Equiv. Dólares ($)", f"$ {total_pen/dolar:,.0f}")
    k3.metric("Avance Total", f"{df['avance'].sum():.1f} m")
    k4.metric("Mineral (TM)", f"{df['mineral_tm'].sum():.0f} t")
    
    st.divider()
    
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("##### 📦 Gasto por Categoría")
        if 'categoria' in df.columns:
            d_c = df.groupby('categoria')['precio_total'].sum().reset_index()
            st.altair_chart(alt.Chart(d_c).mark_bar().encode(
                x=alt.X('categoria', sort='-y'), y='precio_total',
                tooltip=['categoria', 'precio_total']
            ), use_container_width=True)
            
    with g2:
        st.markdown("##### 📉 Costo por Labor")
        st.altair_chart(alt.Chart(df_agrupado).mark_bar(color='#FFA500').encode(
            x=alt.X('labor', sort='-y'), y='precio_total',
            tooltip=['labor', 'precio_total']
        ), use_container_width=True)

    # 5. SECCIÓN DE EXPORTACIÓN (Aquí están los 2 Botones)
    st.divider()
    st.subheader("📥 Exportación de Reportes")
    
    col_btn_csv, col_btn_xls = st.columns(2)
    
    # --- BOTÓN 1: CSV BÁSICO (Siempre funciona) ---
    with col_btn_csv:
        st.info("📊 **Formato Básico (CSV)**")
        st.caption("Texto plano separado por comas. Ideal para importar rápido a otros sistemas.")
        
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Descargar CSV",
            data=csv_data,
            file_name="data_raw.csv",
            mime="text/csv",
            key="btn_csv_down"
        )

    # --- BOTÓN 2: EXCEL PREMIUM (Tu nuevo código) ---
    with col_btn_xls:
        st.success("📈 **Formato Gerencial (Excel)**")
        st.caption("Incluye formatos, colores, tablas dinámicas y gráficos. Listo para imprimir.")
        
        # Generamos el Excel en memoria
        try:
            usuario = st.session_state.get('usuario', 'Admin')
            rol = st.session_state.get('rol', 'Lector')
            
            # Llamamos a tu función de modules/reportes.py
            excel_data = generar_excel_corporativo(df, df_agrupado, usuario, rol)
            
            st.download_button(
                label="📊 Descargar Excel Pro",
                data=excel_data,
                file_name=f"Reporte_CORE_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_xls_down",
                type="primary" # Botón resaltado
            )
        except Exception as e:
            st.error(f"⚠️ Error generando Excel: {e}")
            st.warning("Verifica que hayas subido el archivo modules/reportes.py")