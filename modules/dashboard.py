# modules/dashboard.py
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, time  # <-- 'time' es vital para el cierre del día
from database import run_query
# Importamos el módulo de reportes
from modules.reportes import generar_excel_corporativo

def show_dashboard():
    # --- CABECERA Y BOTÓN DE ACTUALIZACIÓN ---
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
        
        # --- CORRECCIÓN DE FILTRO DE LABOR ---
        # Antes buscabas en 'labores' (nombres), ahora buscamos en 'frentes' (códigos)
        # para que coincida con lo que guarda el registro.py
        try:
            # A) Traemos los frentes activos
            labs_data = run_query("SELECT codigo FROM frentes WHERE estado='ACTIVO' ORDER BY codigo")
            labs = [x['codigo'] for x in labs_data] if labs_data else []
            
            # B) TRUCO: Traemos también cualquier labor que ya tenga costos registrados
            # (Esto sirve por si hay datos viejos o frentes desactivados que tienen historia)
            labs_existentes = run_query("SELECT DISTINCT labor FROM costos")
            if labs_existentes:
                lista_existentes = [x['labor'] for x in labs_existentes if x['labor']]
                # Unimos las dos listas y quitamos duplicados
                labs = sorted(list(set(labs + lista_existentes)))
        except:
            labs = []
        # -------------------------------------
            
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
    
    # Ajuste de fecha final para incluir todo el día (hasta las 23:59:59)
    ff_full = datetime.combine(ff, time(23, 59, 59))
    
    params = [fi, ff_full]
    
    if f_lab != "TODOS":
        query += " AND c.labor = %s"
        params.append(f_lab)
    if f_gua != "TODOS":
        query += " AND c.guardia = %s"
        params.append(f_gua)
        
    data = run_query(query, params)
    df = pd.DataFrame(data)
    
    if df.empty:
        st.warning("📭 No hay datos registrados en este rango de fechas y filtros.")
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
    
    # 4. KPIs y Gráficos
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

    # 5. SECCIÓN DE EXPORTACIÓN
    st.divider()
    st.subheader("📥 Exportación de Reportes")
    
    col_btn_csv, col_btn_xls = st.columns(2)
    
    # --- BOTÓN 1: CSV BÁSICO ---
    with col_btn_csv:
        st.info("📊 **Formato Básico (CSV)**")
        st.caption("Texto plano separado por comas.")
        
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Descargar CSV",
            data=csv_data,
            file_name="data_raw.csv",
            mime="text/csv",
            key="btn_csv_down"
        )

    # --- BOTÓN 2: EXCEL PREMIUM ---
    with col_btn_xls:
        st.success("📈 **Formato Gerencial (Excel)**")
        st.caption("Incluye formatos, colores y tablas dinámicas.")
        
        try:
            usuario = st.session_state.get('usuario', 'Admin')
            rol = st.session_state.get('rol', 'Lector')
            
            excel_data = generar_excel_corporativo(df, df_agrupado, usuario, rol)
            
            st.download_button(
                label="📊 Descargar Excel Pro",
                data=excel_data,
                file_name=f"Reporte_CORE_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_xls_down",
                type="primary"
            )
        except Exception as e:
            st.error(f"⚠️ Error generando Excel: {e}")
            st.warning("Verifica que hayas subido el archivo modules/reportes.py")