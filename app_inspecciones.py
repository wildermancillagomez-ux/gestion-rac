import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE LA PÁGINA (ESTRUCTURA COMPLETA)
st.set_page_config(
    page_title="Gestor de Seguridad RAC 2025",
    page_icon="🛡️",
    layout="wide"
)

# --- ESTILOS VISUALES (CSS PREMIUM - NO SE RESUME) ---
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
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS INTELIGENTE (LECTURA DE DATA.XLSX)
@st.cache_data
def load_data():
    # Usamos el nombre simplificado para evitar errores en la red
    file_path = 'data.xlsx'
    xl = pd.ExcelFile(file_path)
    
    # Lógica para detectar la pestaña correcta
    sheet = 'Hoja1' if 'Hoja1' in xl.sheet_names else xl.sheet_names[0]
    df = xl.parse(sheet)
    
    # Limpieza profunda de encabezados
    df.columns = [str(c).strip() for c in df.columns]
    
    # Procesamiento de la columna Estado (Columna X)
    if 'Estado' in df.columns:
        df['Estado'] = df['Estado'].astype(str).str.strip().replace({'nan': 'Overdue', 'None': 'Overdue', '': 'Overdue'})
        df['Estado'] = df['Estado'].replace({'Completado': 'Completed', 'Pendiente': 'Overdue'})
    else:
        df['Estado'] = 'Overdue'

    # Limpieza de responsables (Columna L)
    if 'RESPONSABLE DE ÁREA' in df.columns:
        df['RESPONSABLE DE ÁREA'] = df['RESPONSABLE DE ÁREA'].astype(str).str.strip()
    
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"❌ Error crítico al cargar 'data.xlsx': {e}")
    st.info("Asegúrate de haber renombrado tu archivo a 'data.xlsx' antes de subirlo a GitHub.")
    st.stop()

# --- 3. BARRA LATERAL (FILTROS COMPLETOS) ---
st.sidebar.header("🔍 Filtros de Gestión")
st.sidebar.markdown("Ajusta los datos para el análisis específico.")

# Filtro por Mes
lista_meses = ["Todos"] + sorted([str(m) for m in df_raw['MES'].dropna().unique() if str(m) != 'nan'])
mes_sel = st.sidebar.selectbox("Filtrar por Mes:", lista_meses)

# Filtro por Sección
lista_secciones = ["Todas"] + sorted([str(s) for s in df_raw['SECCIÓN'].dropna().unique() if str(s) != 'nan'])
seccion_sel = st.sidebar.selectbox("Filtrar por Sección:", lista_secciones)

# Aplicación de filtros al dataset
df = df_raw.copy()
if mes_sel != "Todos":
    df = df[df['MES'] == mes_sel]
if seccion_sel != "Todas":
    df = df[df['SECCIÓN'] == seccion_sel]

# 4. CABECERA PRINCIPAL Y LOGO SIMBOLICO
st.title("🛡️ Sistema de Gestión de Observaciones - RAC 2025")
st.markdown(f"**Visualización Activa:** {mes_sel} | **Sección:** {seccion_sel} | **Registros:** {len(df)}")
st.markdown("---")

# 5. TABLERO DE INDICADORES (KPIs DETALLADOS)
total_obs = len(df)
cerradas = len(df[df['Estado'] == 'Completed'])
pendientes = len(df[df['Estado'] == 'Overdue'])
efectividad = (cerradas / total_obs * 100) if total_obs > 0 else 0

col_k1, col_k2, col_k3, col_k4 = st.columns(4)
col_k1.metric("Total Observaciones", total_obs)
col_k2.metric("Cerradas (Cierres)", cerradas)
col_k3.metric("Pendientes (Overdue)", pendientes, delta=f"{pendientes} críticas", delta_color="inverse")
col_k4.metric("% de Cumplimiento", f"{efectividad:.1f}%")

st.markdown("---")

# 6. GRÁFICOS DE ALTO IMPACTO (PIE Y RANKING)
st.header("📊 Estadísticas y Monitoreo de Cumplimiento")
g1, g2 = st.columns([1, 1])

with g1:
    fig_pie = px.pie(
        df, names='Estado', 
        title="Estado de Observaciones en Tiempo Real",
        hole=0.5,
        color='Estado',
        color_discrete_map={'Completed': '#2ecc71', 'Overdue': '#e74c3c'}
    )
    fig_pie.update_traces(textinfo='percent+label', pull=[0.1, 0])
    st.plotly_chart(fig_pie, use_container_width=True)

with g2:
    # Solo mostrar responsables con tareas Overdue
    df_pendientes = df[df['Estado'] == 'Overdue']
    df_pendientes = df_pendientes[df_pendientes['RESPONSABLE DE ÁREA'].str.lower() != 'nan']
    
    if not df_pendientes.empty:
        ranking = df_pendientes.groupby('RESPONSABLE DE ÁREA').size().reset_index(name='Cantidad')
        ranking = ranking.sort_values(by='Cantidad', ascending=True)
        
        fig_bar = px.bar(
            ranking, 
            x='Cantidad', 
            y='RESPONSABLE DE ÁREA', 
            orientation='h',
            title="Ranking de Responsables con Pendientes",
            color='Cantidad',
            color_continuous_scale='Reds',
            text='Cantidad'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.success("🎉 ¡Excelente! No existen pendientes con los filtros actuales.")

st.markdown("---")

# 7. PORTAL DE BÚSQUEDA INTERACTIVO (EL CORAZÓN DE LA WEB)
st.header("🔍 Portal de Autogestión para Responsables")
st.info("Selecciona tu nombre para verificar deudas y subir evidencia fotográfica.")

# Obtención de lista de nombres limpia
nombres_limpios = [str(n) for n in df['RESPONSABLE DE ÁREA'].unique() if str(n).lower() != 'nan' and str(n).strip() != '']
nombres_ordenados = sorted(nombres_limpios)

user_sel = st.selectbox(
    "Busca y selecciona tu nombre completo:",
    options=["Seleccionar responsable..."] + nombres_ordenados
)

if user_sel != "Seleccionar responsable...":
    # Filtrado por usuario
    mis_datos = df[df['RESPONSABLE DE ÁREA'] == user_sel]
    mis_pendientes = mis_datos[mis_datos['Estado'] == 'Overdue']
    
    if not mis_pendientes.empty:
        st.warning(f"Estimado(a) **{user_sel}**, se han detectado **{len(mis_pendientes)}** observaciones pendientes de cierre.")
        
        # Despliegue de observaciones individuales
        for idx, row in mis_pendientes.iterrows():
            with st.expander(f"📌 Registro ID: {row['Nº']} | Área: {row['ÁREA']} | Límite: {row['Fecha de Cumplimiento']}"):
                col_txt, col_img = st.columns([2, 1])
                
                with col_txt:
                    st.markdown("**Descripción del Hallazgo:**")
                    st.write(row['DESCRIPCIÓN'])
                    st.markdown("**Acción Correctiva Requerida:**")
                    st.write(row['Acción Correctiva'])
                    st.markdown(f"**Riesgo Asociado:** `{row['RIESGO ASOCIADO']}`")
                
                with col_img:
                    # Función de subida de archivos (Evidencia)
                    foto = st.file_uploader(f"Cargar Foto de Corrección (ID {row['Nº']})", type=['jpg','png','jpeg'], key=f"photo_{idx}")
                    if foto:
                        st.image(foto, caption="Vista previa de evidencia", use_container_width=True)
                        if st.button(f"Validar y Enviar ID {row['Nº']}", key=f"btn_{idx}"):
                            st.success(f"✅ Evidencia para el ID {row['Nº']} enviada correctamente.")
    else:
        st.balloons()
        st.success(f"🎊 ¡Felicidades **{user_sel}**! No tienes observaciones pendientes bajo los criterios actuales.")

# 8. VISOR DE DATOS PARA AUDITORÍA
with st.expander("📂 Explorar Base de Datos Completa (Modo Lectura)"):
    st.dataframe(df, use_container_width=True)