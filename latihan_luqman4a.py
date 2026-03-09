import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from pyproj import Transformer

# --- 1. CONFIG ---
st.set_page_config(page_title="Sistem Plot Lot Johor Grid", layout="wide")

# --- 2. FUNGSI TUKAR KOORDINAT (JOHOR GRID -> WGS84) ---
def convert_johor_to_wgs84(e_list, n_list):
    # EPSG:4390 = Kertau 1948 / Johor Grid
    # EPSG:4326 = WGS84 (Global GPS Lat/Lon)
    # always_xy=True memastikan input diproses sebagai (Easting, Northing)
    transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(e_list, n_list)
    return lat, lon

st.title("🗺️ Sistem Visualisasi Lot Tanah (Johor Grid)")
st.write("Sistem ini menggunakan unjuran Kertau / Johor Grid (EPSG:4390) untuk pemetaan.")

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
        lats, lons = convert_johor_to_wgs84(e, n)
        points = list(zip(lats, lons))
        
        # B. Setting Peta
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
            color="#000080",     # Biru Tua (Identiti Johor)
            weight=3,
            fill=True,
            fill_color="#FF0000",# Merah (Identiti Johor)
            fill_opacity=0.3,
            tooltip="Kawasan Lot Johor Grid"
        ).add_to(m)

        # D. Marker Stesen
        for i in range(len(points)):
            folium.CircleMarker(
                location=points[i],
                radius=5,
                color="white",
                fill=True,
                fill_color="blue",
                fill_opacity=1,
                popup=f"STN {stn[i]}"
            ).add_to(m)

        # --- 4. PAPAR PETA ---
        st_folium(m, width="100%", height=600)

        # --- 5. ANALISIS LUAS ---
        # Formula Shoelace menggunakan koordinat meter (E, N)
        luas_m2 = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
        
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Bilangan Stesen", len(stn))
        c2.metric("Luas (m²)", f"{luas_m2:.2f}")
        c3.metric("Luas (Ekar)", f"{(luas_m2 / 4046.86):.4f}")

    except Exception as err:
        st.error(f"Ralat: {err}. Sila pastikan data anda adalah koordinat Johor Grid yang sah.")
else:
    st.info("Sila muat naik fail CSV untuk melihat plot lot Johor anda.")

# --- 6. SIDEBAR ---
with st.sidebar:
    st.header("Info Sistem")
    st.info("Sistem: Kertau / Johor Grid")
    st.write("Kod EPSG: **4390**")
    st.divider()
    st.write("Nota: Pastikan unit koordinat dalam CSV adalah **Meter**.")
