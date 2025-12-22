# modules/dashboard.py
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from database import run_query
from exportacion import generar_excel_corporativo

def show_dashboard():
    st.title("🏔️ Pukamani - Control de Costos")
    
    # Obtener Dolar
    res = run_query("SELECT valor FROM configuracion WHERE clave='DOLAR_CAMBIO'")
    dolar = float(res[0]['valor']) if res else 3.75
    
    with st.expander("🔍 Filtros", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        fi = c1.date_input("Desde", value=datetime.today().replace(day=1))
        ff = c2.date_input("Hasta", value=datetime.today())
        
        # Filtros Dinámicos
        labs = [f['codigo'] for f in run_query("SELECT codigo FROM frentes")]
        f_lab = c3.selectbox("Labor", ["TODOS"] + labs)
        f_gua = c4.selectbox("Guardia", ["TODOS", "Día", "Noche"])
        
    # Consulta Maestra
    query = """
        SELECT 
            c.fecha, c.guardia as Guardia,
            f.codigo as Labor, f.tipo as Tipo_Labor,
            i.categoria as Categoria, i.nombre as Insumo, i.unidad as Unidad,
            c.cantidad as Cantidad, COALESCE(i.precio, 0) as Precio_Unit,
            c.avance_metros as Avance, c.tonelaje as TM,
            (c.cantidad * COALESCE(i.precio, 0)) as Costo_PEN,
            u.username as Usuario_Registro
        FROM consumo_diario c
        LEFT JOIN frentes f ON c.frente_id = f.id
        LEFT JOIN insumos i ON c.insumo_id = i.id
        LEFT JOIN usuarios u ON c.usuario_id = u.id
        WHERE c.fecha BETWEEN %s AND %s
    """
    params = [fi, ff]
    if f_lab != "TODOS":
        query += " AND f.codigo = %s"
        params.append(f_lab)
    if f_gua != "TODOS":
        query += " AND c.guardia = %s"
        params.append(f_gua)
        
    data = run_query(query, params)
    df = pd.DataFrame(data)
    
    if df.empty:
        st.info("📭 Sin datos en este período para generar gráficos.")
        return

    # --- CORRECCIÓN CRÍTICA: Estandarizar nombres de columnas a minúsculas ---
    # Esto soluciona el error KeyError 'Costo_PEN' vs 'costo_pen'
    df.columns = [c.lower() for c in df.columns]

    # Ahora usamos las columnas en minúscula (costo_pen, avance, tm, etc.)
    df['costo_pen'] = df['costo_pen'].astype(float)
    df['avance'] = df['avance'].astype(float)
    df['tm'] = df['tm'].astype(float)
    
    total_pen = df['costo_pen'].sum()
    
    # Agrupamos usando nombres en minúscula
    df_agrupado = df.groupby(['labor', 'tipo_labor']).agg({
        'avance':'sum', 
        'tm':'sum', 
        'costo_pen':'sum'
    }).reset_index()
    
    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Gasto Total (S/)", f"S/ {total_pen:,.0f}")
    k2.metric("Equiv. Dólares ($)", f"$ {total_pen/dolar:,.0f}")
    k3.metric("Avance Total", f"{df_agrupado['avance'].sum():.1f} m")
    k4.metric("Mineral (TM)", f"{df_agrupado['tm'].sum():.0f} t")
    st.divider()
    
    # Gráficos (Todo actualizado a minúsculas)
    g1, g2, g3 = st.columns([1,1,1.5])
    
    with g1:
        st.markdown("##### 🌓 Por Guardia")
        d_g = df.groupby('guardia')['costo_pen'].sum().reset_index()
        st.altair_chart(
            alt.Chart(d_g).mark_arc(innerRadius=40).encode(
                theta='costo_pen', 
                color='guardia', 
                tooltip=['guardia', alt.Tooltip('costo_pen', format=',.2f')]
            ), use_container_width=True)
        
    with g2:
        st.markdown("##### 📦 Por Categoría")
        d_c = df.groupby('categoria')['costo_pen'].sum().reset_index()
        st.altair_chart(
            alt.Chart(d_c).mark_bar().encode(
                x=alt.X('categoria', sort='-y'), 
                y='costo_pen', 
                tooltip=['categoria', alt.Tooltip('costo_pen', format=',.2f')]
            ), use_container_width=True)

    with g3:
        st.markdown("##### 📉 Costo Unitario (S/m)")
        # Calculamos unitario
        df_agrupado['unit_s'] = df_agrupado.apply(lambda x: x['costo_pen']/x['avance'] if x['avance']>0 else 0, axis=1)
        
        st.altair_chart(
            alt.Chart(df_agrupado).mark_bar(color='#FFA500').encode(
                x=alt.X('labor', sort='-y'), 
                y='unit_s', 
                tooltip=['labor', alt.Tooltip('unit_s', format=',.2f')]
            ), use_container_width=True)

    # --- BLOQUE DE EXPORTACIÓN CORREGIDO ---
    try:
        # Generamos el archivo Excel
        xls = generar_excel_corporativo(df, df_agrupado, st.session_state['usuario'], st.session_state['rol'])
        
        # OJO AQUÍ: Agregamos _%H%M%S para que sea único cada segundo
        # Ejemplo del nombre que saldrá: "Reporte_Costos_2025-12-22_143005.xlsx"
        nombre_archivo = f"Reporte_Costos_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.xlsx"
        
        st.download_button(
            label="📥 Descargar Reporte Excel",
            data=xls,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    except Exception as e:
        st.error(f"⚠️ Error en Exportación: {e}")