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
    """
    EPSG:3381 adalah kod untuk Cassini-Soldner (Perak).
    EPSG:4326 adalah kod untuk WGS84 (Latitude/Longitude).
    """
    # Pastikan 'always_xy=True' supaya urutan adalah (Easting, Northing)
    transformer = Transformer.from_crs("EPSG:3381", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(e_list, n_list)
    return lat, lon

st.title("🗺️ Sistem Visualisasi Lot Tanah (Cassini Perak)")
st.write("Sistem ini menukarkan koordinat Cassini Perak ke paparan Google Satellite secara automatik.")

# --- 3. MUAT NAIK FAIL ---
uploaded_file = st.file_uploader("Muat naik fail CSV (Pastikan ada kolum STN, E, N)", type=["csv"])

if uploaded_file is not None:
    try:
        # Baca Data
        df = pd.read_csv(uploaded_file)
        df = df.dropna(subset=['E', 'N'])
        
        e = df['E'].tolist()
        n = df['N'].tolist()
        stn = df['STN'].tolist()

        # A. Tukar ke Lat/Lon
        lats, lons = convert_cassini_to_wgs84(e, n)
        points = list(zip(lats, lons))
        
        # B. Tentukan Pusat Peta
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)
        
        # C. Bina Peta Folium (Zoom 19 untuk paparan dekat)
        m = folium.Map(location=[center_lat, center_lon], zoom_start=19, tiles=None)
        
        # Masukkan Layer Google Satellite
        folium.TileLayer(
            tiles = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr = 'Google',
            name = 'Google Satellite',
            overlay = False,
            control = True
        ).add_to(m)

        # D. Lukis Poligon Lot Tanah
        folium.Polygon(
            locations=points,
            color="cyan",      # Warna garisan sempadan
            weight=3,
            fill=True,
            fill_color="yellow", # Warna dalam lot
            fill_opacity=0.2,
            tooltip="Kawasan Lot (Cassini Perak)"
        ).add_to(m)

        # E. Letak Marker untuk setiap Stesen (STN)
        for i, (lat, lon) in enumerate(points):
            folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                color="red",
                fill
