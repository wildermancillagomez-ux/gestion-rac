import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Gestor de Seguridad RAC 2025",
    page_icon="🛡️",
    layout="wide"
)

# --- ESTILOS VISUALES (CSS COMPLETO - NO SE TOCA) ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        border-left: 5px solid #007bff;
    }
    div.stButton > button:first-child {
        background-color: #007bff;
        color: white;
        border-radius: 10px;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS INTELIGENTE Y LIMPIEZA PROFUNDA
@st.cache_data
def load_data():
    file_path = 'Base de datos Inspecciones mas RAC 2025.xlsx'
    xl = pd.ExcelFile(file_path)
    sheet = 'Hoja1' if 'Hoja1' in xl.sheet_names else xl.sheet_names[0]
    df = xl.parse(sheet)
    
    # Limpieza de nombres de columnas
    df.columns = [str(c).strip() for c in df.columns]
    
    # Homologación de Estado
    if 'Estado' in df.columns:
        df['Estado'] = df['Estado'].astype(str).str.strip().replace({'nan': 'Overdue', 'None': 'Overdue', '': 'Overdue'})
        df['Estado'] = df['Estado'].replace({'Completado': 'Completed', 'Pendiente': 'Overdue'})
    else:
        df['Estado'] = 'Overdue'

    # Limpieza de responsables
    if 'RESPONSABLE DE ÁREA' in df.columns:
        df['RESPONSABLE DE ÁREA'] = df['RESPONSABLE DE ÁREA'].astype(str).str.strip()
    
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"❌ Error crítico al cargar el archivo: {e}")
    st.stop()

# --- 3. BARRA LATERAL (FILTROS) ---
st.sidebar.header("🔍 Filtros Globales")
st.sidebar.markdown("Usa estos filtros para ajustar el Dashboard completo.")

# Filtro de Mes
meses = ["Todos"] + sorted(df_raw['MES'].dropna().unique().tolist())
mes_sel = st.sidebar.selectbox("Seleccionar Mes:", meses)

# Filtro de Sección
secciones = ["Todas"] + sorted(df_raw['SECCIÓN'].dropna().unique().tolist())
seccion_sel = st.sidebar.selectbox("Seleccionar Sección:", secciones)

# Aplicar Filtros al DataFrame principal
df = df_raw.copy()
if mes_sel != "Todos":
    df = df[df['MES'] == mes_sel]
if seccion_sel != "Todas":
    df = df[df['SECCIÓN'] == seccion_sel]

# 4. CABECERA PRINCIPAL
st.title("🛡️ Sistema de Gestión de Observaciones - RAC 2025")
st.markdown(f"**Visualizando:** {mes_sel} | {seccion_sel} | **Registros:** {len(df)}")
st.markdown("---")

# 5. TABLERO DE INDICADORES (KPIs)
total_obs = len(df)
cerradas = len(df[df['Estado'] == 'Completed'])
pendientes = len(df[df['Estado'] == 'Overdue'])
efectividad = (cerradas / total_obs * 100) if total_obs > 0 else 0

col_k1, col_k2, col_k3, col_k4 = st.columns(4)
col_k1.metric("Total Observaciones", total_obs)
col_k2.metric("Cerradas ✅", cerradas)
col_k3.metric("Pendientes ⚠️", pendientes, delta=f"{pendientes} críticas", delta_color="inverse")
col_k4.metric("% de Cumplimiento", f"{efectividad:.1f}%")

st.markdown("---")

# 6. GRÁFICOS DE ALTO IMPACTO
st.header("📊 Estadísticas y Rankings")
g1, g2 = st.columns([1, 1])

with g1:
    fig_pie = px.pie(
        df, names='Estado', 
        title="Estado General de la Gestión",
        hole=0.5,
        color='Estado',
        color_discrete_map={'Completed': '#2ecc71', 'Overdue': '#e74c3c'}
    )
    fig_pie.update_traces(textinfo='percent+label', pull=[0.1, 0])
    st.plotly_chart(fig_pie, use_container_width=True)

with g2:
    df_pendientes = df[df['Estado'] == 'Overdue']
    df_pendientes = df_pendientes[df_pendientes['RESPONSABLE DE ÁREA'] != 'nan']
    
    if not df_pendientes.empty:
        ranking = df_pendientes.groupby('RESPONSABLE DE ÁREA').size().reset_index(name='Cantidad')
        ranking = ranking.sort_values(by='Cantidad', ascending=True)
        
        fig_bar = px.bar(
            ranking, 
            x='Cantidad', 
            y='RESPONSABLE DE ÁREA', 
            orientation='h',
            title="Ranking: Responsables con más Pendientes",
            color='Cantidad',
            color_continuous_scale='Reds',
            text='Cantidad'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.success("🎉 ¡Sin pendientes con los filtros aplicados!")

st.markdown("---")

# 7. PORTAL DE BÚSQUEDA DEL RESPONSABLE
st.header("🔍 Mi Portal de Trabajo Personal")
st.info("Nota: Los filtros de la izquierda también afectan tu búsqueda personal.")

nombres_limpios = [str(n) for n in df['RESPONSABLE DE ÁREA'].unique().tolist() if str(n).lower() != 'nan' and str(n).strip() != '']
nombres_ordenados = sorted(nombres_limpios)

user_sel = st.selectbox(
    "Escribe o selecciona tu nombre:",
    options=["Seleccionar..."] + nombres_ordenados
)

if user_sel != "Seleccionar...":
    mis_datos = df[df['RESPONSABLE DE ÁREA'] == user_sel]
    mis_pendientes = mis_datos[mis_datos['Estado'] == 'Overdue']
    
    if not mis_pendientes.empty:
        st.warning(f"Hola **{user_sel}**, tienes **{len(mis_pendientes)}** pendientes en esta selección.")
        
        for idx, row in mis_pendientes.iterrows():
            with st.expander(f"📌 ID: {row['Nº']} - {row['ÁREA']} (Límite: {row['Fecha de Cumplimiento']})"):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"**Hallazgo:** {row['DESCRIPCIÓN']}")
                    st.markdown(f"**Acción:** {row['Acción Correctiva']}")
                    st.info(f"**Riesgo:** {row['RIESGO ASOCIADO']}")
                with c2:
                    foto = st.file_uploader(f"Subir foto ID {row['Nº']}", type=['jpg','png','jpeg'], key=f"photo_{idx}")
                    if foto:
                        st.image(foto, width=250)
                        st.button(f"Enviar Registro ID {row['Nº']}", key=f"btn_{idx}")
    else:
        st.balloons()
        st.success(f"🎊 ¡Felicidades **{user_sel}**! No tienes deudas con los filtros actuales.")

# 8. VISTA GENERAL
with st.expander("📂 Ver tabla de datos filtrada"):
    st.dataframe(df, use_container_width=True)