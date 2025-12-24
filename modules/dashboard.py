# modules/dashboard.py
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from database import run_query
# Asegúrate de tener el archivo modules/reportes.py creado con el código anterior
from modules.reportes import generar_excel_corporativo 

def show_dashboard():
    st.title("🏔️ Pukamani - Control de Costos")
    
    # 1. Obtener Configuración (Dólar)
    res = run_query("SELECT valor FROM configuracion WHERE clave='DOLAR_CAMBIO'")
    dolar = float(res[0]['valor']) if res else 3.75
    
    # 2. Filtros Superiores
    with st.expander("🔍 Filtros de Búsqueda", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        fi = c1.date_input("Desde", value=datetime.today().replace(day=1))
        ff = c2.date_input("Hasta", value=datetime.today())
        
        # Filtros Dinámicos desde BD
        # Ajusta 'frentes' o 'labores' según como se llame tu tabla real
        try:
            labs = [f['nombre'] for f in run_query("SELECT nombre FROM labores WHERE estado=true")]
        except:
            labs = [] # Fallback si no hay tabla labores aún
            
        f_lab = c3.selectbox("Labor", ["TODOS"] + labs)
        f_gua = c4.selectbox("Guardia", ["TODOS", "Día", "Noche"])
        
    # 3. Consulta Maestra (JOINs para traer nombres reales)
    # Nota: Ajusta los nombres de tablas (frentes vs labores) según tu BD real
    query = """
        SELECT 
            c.fecha, 
            c.guardia,
            c.labor,         -- Usamos el campo texto directo si fase 1, o join si fase 2
            c.categoria, 
            c.detalle,       -- Antes 'insumo'
            c.unidad,
            c.cantidad, 
            c.precio_total,  -- La columna clave de dinero
            c.avance, 
            c.mineral_tm
        FROM costos c
        WHERE c.fecha BETWEEN %s AND %s
    """
    params = [fi, ff]
    
    if f_lab != "TODOS":
        query += " AND c.labor = %s"
        params.append(f_lab)
    if f_gua != "TODOS":
        query += " AND c.guardia = %s"
        params.append(f_gua)
        
    data = run_query(query, params)
    df = pd.DataFrame(data)
    
    # 4. Validación de Datos Vacíos
    if df.empty:
        st.info("📭 No se encontraron registros en este período.")
        return

    # --- CORRECCIÓN CRÍTICA: Estandarizar columnas ---
    # Convertimos todo a minúsculas para evitar errores de Key (Costo_PEN vs costo_pen)
    df.columns = [c.lower() for c in df.columns]

    # Aseguramos tipos numéricos
    cols_num = ['precio_total', 'avance', 'mineral_tm', 'cantidad']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Variables calculadas
    total_pen = df['precio_total'].sum()
    
    # Dataframe Agrupado para KPIs y Gráficos
    df_agrupado = df.groupby(['labor']).agg({
        'avance': 'sum', 
        'mineral_tm': 'sum', 
        'precio_total': 'sum'
    }).reset_index()
    
    # 5. Visualización de KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Gasto Total (S/)", f"S/ {total_pen:,.0f}")
    k2.metric("Equiv. Dólares ($)", f"$ {total_pen/dolar:,.0f}")
    k3.metric("Avance Total", f"{df['avance'].sum():.1f} m")
    k4.metric("Mineral (TM)", f"{df['mineral_tm'].sum():.0f} t")
    
    st.divider()
    
    # 6. Gráficos Interactivos
    g1, g2, g3 = st.columns([1, 1, 1.5])
    
    with g1:
        st.markdown("##### 🌓 Por Guardia")
        if 'guardia' in df.columns:
            d_g = df.groupby('guardia')['precio_total'].sum().reset_index()
            chart_g = alt.Chart(d_g).mark_arc(innerRadius=40).encode(
                theta='precio_total', 
                color='guardia', 
                tooltip=['guardia', alt.Tooltip('precio_total', format=',.2f')]
            )
            st.altair_chart(chart_g, use_container_width=True)
        
    with g2:
        st.markdown("##### 📦 Por Categoría")
        if 'categoria' in df.columns:
            d_c = df.groupby('categoria')['precio_total'].sum().reset_index()
            chart_c = alt.Chart(d_c).mark_bar().encode(
                x=alt.X('categoria', sort='-y'), 
                y='precio_total', 
                tooltip=['categoria', alt.Tooltip('precio_total', format=',.2f')]
            )
            st.altair_chart(chart_c, use_container_width=True)

    with g3:
        st.markdown("##### 📉 Costo por Labor (Pareto)")
        chart_l = alt.Chart(df_agrupado).mark_bar(color='#FFA500').encode(
            x=alt.X('labor', sort='-y'), 
            y='precio_total', 
            tooltip=['labor', alt.Tooltip('precio_total', format=',.2f')]
        )
        st.altair_chart(chart_l, use_container_width=True)

    # 7. EXPORTACIÓN DE REPORTES (Excel Pro)
    st.divider()
    st.subheader("📥 Exportar Datos")
    
    col_exp_info, col_exp_btn = st.columns([3,1])
    
    with col_exp_info:
        st.caption("Descargue el reporte detallado con tablas dinámicas y gráficos incrustados.")
        
    with col_exp_btn:
        try:
            # Recuperamos usuario de la sesión (o ponemos default)
            usuario_actual = st.session_state.get('usuario', 'Invitado')
            rol_actual = st.session_state.get('rol', 'Lector')
            
            # Generamos el Excel en memoria
            xls_data = generar_excel_corporativo(df, df_agrupado, usuario_actual, rol_actual)
            
            # Nombre del archivo con fecha y hora
            nombre_archivo = f"Reporte_Pukamani_{datetime.now().strftime('%Y-%m-%d_%H%M')}.xlsx"
            
            st.download_button(
                label="📊 Descargar Excel",
                data=xls_data,
                file_name=nombre_archivo,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        except Exception as e:
            st.error(f"⚠️ Error al generar Excel: {e}")
            # Fallback a CSV simple si falla el Excel complejo
            st.download_button(
                label="📄 Descargar CSV Simple (Respaldo)",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name="data_backup.csv",
                mime="text/csv"
            )