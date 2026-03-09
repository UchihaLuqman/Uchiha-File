import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from pyproj import Transformer

# --- 1. CONFIG ---
st.set_page_config(page_title="Sistem Plot Lot GDM2000 MRSO", layout="wide")

# --- 2. FUNGSI TUKAR KOORDINAT (GDM2000 MRSO -> WGS84) ---
def convert_gdm2000_to_wgs84(e_list, n_list):
    # EPSG:3375 = GDM2000 / Malaysia Rectified Skew Orthomorphic (MRSO)
    # EPSG:4326 = WGS84 (Lat/Lon)
    transformer = Transformer.from_crs("EPSG:3375", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(e_list, n_list)
    return lat, lon

st.title("🗺️ Sistem Visualisasi Lot Tanah (GDM2000 MRSO)")
st.write("Sistem ini menggunakan unjuran GDM2000 MRSO untuk pemetaan satelit.")

# --- 3. UPLOAD FAIL ---
uploaded_file = st.file_uploader("Muat naik fail CSV (Format: STN, E, N)", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df = df.dropna(subset=['E', 'N'])
        
        e = df['E'].tolist()
        n = df['N'].tolist()
        stn = df['STN'].tolist()

        # A. Tukar Koordinat
        lats, lons = convert_gdm2000_to_wgs84(e, n)
        points = list(zip(lats, lons))
        
        # B. Setting Peta (Zoom ke kawasan lot)
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)
        m = folium.Map(location=[center_lat, center_lon], zoom_start=19, tiles=None)
        
        # Google Satellite Layer
        folium.TileLayer(
            tiles = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr = 'Google',
            name = 'Google Satellite',
            overlay = False,
            control = True
        ).add_to(m)

        # C. Lukis Poligon Lot
        folium.Polygon(
            locations=points,
            color="yellow",      # Warna garisan
            weight=3,
            fill=True,
            fill_color="cyan",   # Warna dalam lot
            fill_opacity=0.3,
            tooltip="Kawasan Lot GDM2000"
        ).add_to(m)

        # D. Letak Marker Stesen
        for i in range(len(points)):
            folium.CircleMarker(
                location=points[i],
                radius=5,
                color="red",
                fill=True,
                fill_color="white",
                fill_opacity=1,
                popup=f"STN {stn[i]}"
            ).add_to(m)

        # --- 4. PAPAR PETA ---
        st_folium(m, width="100%", height=600)

        # --- 5. ANALISIS LUAS ---
        def calculate_area(x, y):
            return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        
        luas_m2 = calculate_area(np.array(e), np.array(n))
        
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Bilangan Stesen", len(stn))
        c2.metric("Luas (m²)", f"{luas_m2:.2f}")
        c3.metric("Luas (Ekar)", f"{(luas_m2 / 4046.86):.4f}")

    except Exception as err:
        st.error(f"Ralat: {err}. Pastikan fail CSV mempunyai kolum E dan N yang betul.")
else:
    st.info("Sila muat naik fail CSV untuk melihat plot lot anda.")

# --- 6. SIDEBAR ---
with st.sidebar:
    st.header("Info Sistem")
    st.info("Sistem: GDM2000 / MRSO")
    st.write("Kod EPSG: **3375**")
    st.divider()
    st.write("Contoh Data:")
    st.code("STN,E,N\n1,424560,512340\n2,424580,512360")
