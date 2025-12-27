# modules/dashboard.py
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, time
from database import run_query
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
    
    # 1. Configuración General
    res = run_query("SELECT valor FROM configuracion WHERE clave='DOLAR_CAMBIO'")
    dolar = float(res[0]['valor']) if res else 3.75
    
    with st.expander("🔍 Filtros de Búsqueda", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        fi = c1.date_input("Desde", value=datetime.today().replace(day=1))
        ff = c2.date_input("Hasta", value=datetime.today())
        
        # ---------------------------------------------------------
        # 🚀 LA LÓGICA DEL FILTRO "A PRUEBA DE BALAS"
        # ---------------------------------------------------------
        # En lugar de adivinar qué labores existen, primero traemos TODA la data
        # del rango de fechas. Así el filtro se llena con lo que REALMENTE hay.
        
        # Paso 1: Consultar BD sin filtrar por labor/guardia aún
        base_query = """
            SELECT 
                c.fecha, c.guardia, c.labor, c.categoria, c.detalle, c.unidad,
                c.cantidad, c.precio_total, c.avance, c.mineral_tm
            FROM costos c
            WHERE c.fecha BETWEEN %s AND %s
        """
        ff_full = datetime.combine(ff, time(23, 59, 59))
        base_params = [fi, ff_full]
        
        raw_data = run_query(base_query, base_params)
        df_base = pd.DataFrame(raw_data)
        
        # Paso 2: Extraer listas únicas para los selectbox
        if not df_base.empty:
            # Normalizamos nombres de columnas por si acaso
            df_base.columns = [c.lower() for c in df_base.columns]
            
            # Sacamos lista única de labores y guardias presentes en la data
            labs_reales = sorted(df_base['labor'].unique().tolist()) if 'labor' in df_base.columns else []
            gua_reales = sorted(df_base['guardia'].unique().tolist()) if 'guardia' in df_base.columns else []
        else:
            labs_reales = []
            gua_reales = []
            
        # Paso 3: Crear los filtros con esas listas reales
        f_lab = c3.selectbox("Labor", ["TODOS"] + labs_reales)
        f_gua = c4.selectbox("Guardia", ["TODOS"] + gua_reales)
        
    # ---------------------------------------------------------
    # 2. Aplicar Filtros en Memoria (Pandas)
    # ---------------------------------------------------------
    # Usamos df_base que ya tiene los datos, solo filtramos el DataFrame
    df = df_base.copy()
    
    if df.empty:
        st.warning("📭 No hay datos registrados en este rango de fechas.")
        return 

    # Filtro de Labor
    if f_lab != "TODOS":
        df = df[df['labor'] == f_lab]
        
    # Filtro de Guardia
    if f_gua != "TODOS":
        df = df[df['guardia'] == f_gua]
        
    if df.empty:
        st.warning("📭 No hay datos con los filtros seleccionados.")
        return

    # 3. Procesamiento de Datos (Limpieza y Tipos)
    cols_num = ['precio_total', 'avance', 'mineral_tm', 'cantidad']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    total_pen = df['precio_total'].sum()
    
    # Dataframe Agrupado para gráfico
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
    
    # --- BOTÓN 1: CSV ---
    with col_btn_csv:
        st.info("📊 **Formato Básico (CSV)**")
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button("📄 Descargar CSV", csv_data, "data_raw.csv", "text/csv", key="btn_csv_down")

    # --- BOTÓN 2: EXCEL PREMIUM ---
    with col_btn_xls:
        st.success("📈 **Formato Gerencial (Excel)**")
        try:
            usuario = st.session_state.get('usuario', 'Admin')
            rol = st.session_state.get('rol', 'Lector')
            excel_data = generar_excel_corporativo(df, df_agrupado, usuario, rol)
            
            st.download_button(
                "📊 Descargar Excel Pro", 
                excel_data, 
                f"Reporte_CORE_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_xls_down",
                type="primary"
            )
        except Exception as e:
            st.error(f"⚠️ Error: {e}")