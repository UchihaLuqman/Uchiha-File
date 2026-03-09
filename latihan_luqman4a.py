import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from pyproj import Transformer

# --- 1. CONFIG ---
st.set_page_config(page_title="Fix: Sistem RSO Malaya", layout="wide")

# --- 2. FUNGSI TUKAR KOORDINAT (DENGAN FIX TERBALIK) ---
def convert_rso_to_wgs84(e_list, n_list, swap=False):
    # EPSG:3168 (RSO) -> EPSG:4326 (WGS84)
    # always_xy=True memastikan E=X, N=Y
    transformer = Transformer.from_crs("EPSG:3168", "EPSG:4326", always_xy=True)
    
    if swap:
        # Jika user pilih untuk tukar posisi
        lon, lat = transformer.transform(n_list, e_list)
    else:
        lon, lat = transformer.transform(e_list, n_list)
        
    return lat, lon

st.title("🗺️ Sistem Visualisasi Lot Tanah (RSO Malaya)")
st.warning("Jika lot muncul di laut, sila gunakan butang 'Tukar Posisi E/N' di sidebar.")

# --- 3. SIDEBAR SETTING ---
st.sidebar.header("Kawalan Koordinat")
swap_coords = st.sidebar.checkbox("Tukar Posisi (E <-> N)", value=False)

# --- 4. UPLOAD FAIL ---
uploaded_file = st.file_uploader("Muat naik fail CSV (STN, E, N)", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df = df.dropna(subset=['E', 'N'])
        
        e_raw = df['E'].tolist()
        n_raw = df['N'].tolist()
        stn = df['STN'].tolist()

        # A. Tukar Koordinat dengan fungsi Fix
        lats, lons = convert_rso_to_wgs84(e_raw, n_raw, swap=swap_coords)
        points = list(zip(lats, lons))
        
        # B. Cek jika koordinat masuk akal (Bukan 0,0)
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)
        
        # C. Bina Peta
        m = folium.Map(location=[center_lat, center_lon], zoom_start=18, tiles=None)
        
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
            color="yellow",
            weight=3,
            fill=True,
            fill_color="orange",
            fill_opacity=0.3
        ).add_to(m)

        # E. Marker
        for i in range(len(points)):
            folium.CircleMarker(
                location=points[i],
                radius=5,
                color="red",
                fill=True,
                fill_color="white",
                popup=f"STN {stn[i]}"
            ).add_to(m)

        # --- 5. PAPAR PETA ---
        st_folium(m, width="100%", height=600)

        # --- 6. ANALISIS ---
        area = 0.5 * np.abs(np.dot(e_raw, np.roll(n_raw, 1)) - np.dot(n_raw, np.roll(e_raw, 1)))
        st.info(f"📐 Luas: {area:.2f} m² | Koordinat Pusat: {center_lat:.6f}, {center_lon:.6f}")

    except Exception as err:
        st.error(f"Ralat: {err}")
else:
    st.info("Sila muat naik fail CSV.")
