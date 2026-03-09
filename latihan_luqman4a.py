import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from pyproj import Transformer

# --- 1. CONFIG ---
st.set_page_config(page_title="Sistem Plot Lot RSO Malaya", layout="wide")

# --- 2. FUNGSI TUKAR KOORDINAT (RSO MALAYA -> WGS84) ---
def convert_rso_to_wgs84(e_list, n_list):
    # EPSG:3168 = Kertau (RSO) / RSO Malaya
    # EPSG:4326 = WGS84 (Lat/Lon)
    transformer = Transformer.from_crs("EPSG:3168", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(e_list, n_list)
    return lat, lon

st.title("🗺️ Sistem Visualisasi Lot Tanah (RSO Malaya)")
st.write("Sistem ini menggunakan unjuran RSO Malaya (Kertau) untuk pemetaan satelit.")

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
        lats, lons = convert_rso_to_wgs84(e, n)
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
            fill_color="orange", # Warna dalam lot (RSO guna orange untuk beza dengan GDM)
            fill_opacity=0.3,
            tooltip="Kawasan Lot RSO Malaya"
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
        st.error(f"Ralat: {err}. Sila pastikan koordinat adalah dalam format RSO Malaya.")
else:
    st.info("Sila muat naik fail CSV untuk melihat plot lot RSO anda.")

# --- 6. SIDEBAR ---
with st.sidebar:
    st.header("Info Sistem")
    st.info("Sistem: RSO Malaya (Kertau)")
    st.write("Kod EPSG: **3168**")
    st.divider()
    st.write("Nota: Sistem ini sesuai untuk koordinat Easting/Northing dalam ratusan ribu (E: ~400,000, N: ~500,000).")
