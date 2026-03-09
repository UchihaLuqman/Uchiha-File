import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from pyproj import Transformer

# --- CONFIG ---
st.set_page_config(page_title="Sistem Plot Lot Luqman", layout="wide")

# Fungsi Tukar Koordinat (Contoh: RSO ke WGS84)
# Ganti 'EPSG:3168' dengan kod sistem koordinat anda (3168 adalah RSO Malaya)
def convert_to_latlon(e_list, n_list):
 transformer = Transformer.from_crs("EPSG:3168", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(e_list, n_list)
    return lat, lon

st.title("🗺️ Sistem Visualisasi Lot Tanah (Google Satellite)")

uploaded_file = st.file_uploader("Pilih fail CSV koordinat", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df = df.dropna(subset=['E', 'N'])
        
        e = df['E'].tolist()
        n = df['N'].tolist()
        stn = df['STN'].tolist()

        # 1. Tukar Koordinat untuk Peta
        lats, lons = convert_to_latlon(e, n)
        points = list(zip(lats, lons))
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)

        # 2. Bina Peta Folium
        # Layer Google Satellite menggunakan custom tile
        m = folium.Map(location=[center_lat, center_lon], zoom_start=18, tiles=None)
        
        google_satellite = folium.TileLayer(
            tiles = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr = 'Google',
            name = 'Google Satellite',
            overlay = False,
            control = True
        ).add_to(m)

        # 3. Lukis Poligon Lot
        folium.Polygon(
            locations=points,
            color="yellow",
            weight=3,
            fill=True,
            fill_color="green",
            fill_opacity=0.2,
            tooltip="Kawasan Lot"
        ).add_to(m)

        # 4. Tambah Marker Stesen
        for i, (lat, lon) in enumerate(points):
            folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                color="red",
                fill=True,
                tooltip=f"STN {int(stn[i])}"
            ).add_to(m)

        # 5. Paparkan Peta di Streamlit
        st.subheader("Peta Satelit Lot Tanah")
        st_folium(m, width="100%", height=600)

        # 6. Kira Luas (Guna formula Shoelace anda)
        def calculate_area(x, y):
            return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        
        luas = calculate_area(np.array(e), np.array(n))
        st.info(f"📐 Estimasi Luas Lot: {luas:.3f} unit persegi")

    except Exception as err:
        st.error(f"Ralat: {err}")

