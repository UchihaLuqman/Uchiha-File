import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from pyproj import Transformer

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Plot Lot Cassini Perak", layout="wide")

# --- 2. FUNGSI PENUKARAN KOORDINAT (CASSINI PERAK -> WGS84) ---
def convert_cassini_to_wgs84(e_list, n_list):
    # EPSG:3381 = Cassini-Soldner (Perak)
    transformer = Transformer.from_crs("EPSG:3381", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(e_list, n_list)
    return lat, lon

st.title("🗺️ Sistem Visualisasi Lot Tanah (Cassini Perak)")
st.write("Muat naik fail CSV untuk melihat lot di atas Google Satellite.")

# --- 3. MUAT NAIK FAIL ---
uploaded_file = st.file_uploader("Pilih fail CSV (Kolum: STN, E, N)", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df = df.dropna(subset=['E', 'N'])
        
        e = df['E'].tolist()
        n = df['N'].tolist()
        stn = df['STN'].tolist()

        # A. Proses penukaran koordinat
        lats, lons = convert_cassini_to_wgs84(e, n)
        points = list(zip(lats, lons))
        
        # B. Titik tengah peta
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)
        
        # C. Bina Peta Folium
        m = folium.Map(location=[center_lat, center_lon], zoom_start=19, tiles=None)
        
        folium.TileLayer(
            tiles = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr = 'Google',
            name = 'Google Satellite',
            overlay = False,
            control = True
        ).add_to(m)

        # D. Lukis Poligon
        folium.Polygon(
            locations=points,
            color="cyan",
            weight=3,
            fill=True,
            fill_color="yellow",
            fill_opacity=0.2,
            tooltip="Kawasan Lot"
        ).add_to(m)

        # E. Tambah Marker
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

        # --- 4. PAPARAN PETA ---
        st_folium(m, width="100%", height=600)

        # --- 5. ANALISIS LUAS ---
        def calculate_area(x, y):
            return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        
        luas_m2 = calculate_area(np.array(e), np.array(n))
        
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Bilangan Stesen", len(stn))
        c2.metric("Luas (Meter Persegi)", f"{luas_m2:.2f} m²")
        c3.metric("Luas (Ekar)", f"{(luas_m2 / 4046.86):.4f} ekar")

    except Exception as err:
        st.error(f"Ralat: {err}")
else:
    st.info("Sila muat naik fail CSV
