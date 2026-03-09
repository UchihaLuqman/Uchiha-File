import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from pyproj import Transformer

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Sistem Plot Lot Luqman", layout="wide")

# 2. Fungsi Tukar Koordinat dengan Pilihan EPSG
def convert_to_latlon(e_list, n_list, epsg_input):
    # Pastikan jarak di sini konsisten (4 spaces)
    transformer = Transformer.from_crs(epsg_input, "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(e_list, n_list)
    return lat, lon

st.title("🗺️ Sistem Visualisasi Lot Tanah (Google Satellite)")

# 3. Sidebar untuk Pilihan Kod EPSG
st.sidebar.header("Tetapan Koordinat")
opsi_epsg = {
    "RSO Malaya (EPSG:3168)": "EPSG:3168",
    "GDM2000 / MRSO (EPSG:3375)": "EPSG:3375",
    "Cassini Perak (EPSG:3381)": "EPSG:3381"
}
pilihan = st.sidebar.selectbox("Pilih Sistem Koordinat Asal:", list(opsi_epsg.keys()))
kod_terpilih = opsi_epsg[pilihan]

uploaded_file = st.file_uploader("Pilih fail CSV koordinat", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df = df.dropna(subset=['E', 'N'])
        
        e = df['E'].tolist()
        n = df['N'].tolist()
        stn = df['STN'].tolist()

        # Tukar Koordinat menggunakan kod yang dipilih
        lats, lons = convert_to_latlon(e, n, kod_terpilih)
        points = list(zip(lats, lons))
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)

        # Bina Peta Folium
        m = folium.Map(location=[center_lat, center_lon], zoom_start=18, tiles=None)
        
        # Add Google Satellite Layer
        folium.TileLayer(
            tiles = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr = 'Google',
            name = 'Google Satellite',
            overlay = False,
            control = True
        ).add_to(m)

        # Lukis Poligon Lot
        folium.Polygon(
            locations=points,
            color="yellow",
            weight=3,
            fill=True,
            fill_color="green",
            fill_opacity=0.3,
            tooltip="Kawasan Lot"
        ).add_to(m)

        # Tambah Marker Stesen
        for i, (lat, lon) in enumerate(points):
            folium.CircleMarker(
                location=[lat, lon],
                radius=5,
                color="red",
                fill=True,
                tooltip=f"STN {int(stn[i])}"
            ).add_to(m)

        # Paparan Peta
        st.subheader(f"Peta Satelit - Menggunakan {pilihan}")
        st_folium(m, width="100%", height=600)

        # Kira Luas
        def calculate_area(x, y):
            return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        
        luas = calculate_area(np.array(e), np.array(n))
        st.info(f"📐 Estimasi Luas Lot: {luas:.3f} unit persegi (Berdasarkan unit koordinat asal)")

    except Exception as err:
        st.error(f"Ralat: {err}")
else:
    st.info("Sila muat naik fail CSV untuk bermula.")
