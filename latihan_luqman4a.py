import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
import math

# --- 1. CONFIG ---
st.set_page_config(page_title="Sistem Plot Lot Johor Grid PRO", layout="wide")

# --- 2. FUNGSI MATEMATIK (BERING & JARAK) ---
def calculate_bearing_distance(e1, n1, e2, n2):
    de = e2 - e1
    dn = n2 - n1
    # Kira Jarak
    distance = math.sqrt(de**2 + dn**2)
    # Kira Bering (Azimuth)
    bearing = math.degrees(math.atan2(de, dn))
    if bearing < 0:
        bearing += 360
    
    # Tukar ke format Darjah Menit (DMS) ringkas
    d = int(bearing)
    m = int((bearing - d) * 60)
    return f"{d}°{m:02d}'", f"{distance:.2f}m"

# --- 3. FUNGSI TUKAR KOORDINAT ---
# EPSG:4390 adalah Cassini Johor. Jika anda guna grid lain, tukar kod EPSG ini.
def convert_johor_to_wgs84(e_list, n_list):
    transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(e_list, n_list)
    return lat, lon

st.title("🗺️ Sistem Plot Lot Johor Grid (Zoom Tinggi)")
st.markdown("Sila muat naik fail CSV yang mengandungi kolum **STN, E, N**.")

# --- 4. UPLOAD FAIL ---
uploaded_file = st.file_uploader("Muat naik fail CSV", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        # Bersihkan data: buang baris kosong pada koordinat
        df = df.dropna(subset=['E', 'N'])
        
        e = df['E'].tolist()
        n = df['N'].tolist()
        stn = df['STN'].tolist()

        # Tukar koordinat ke Lat/Lon untuk Folium
        lats, lons = convert_johor_to_wgs84(e, n)
        points = list(zip(lats, lons))
        
        # --- 5. PENYEDIAAN PETA (ZOOM TINGGI) ---
        # Kita set max_zoom=22 supaya boleh zoom lebih dekat dari biasa
        m = folium.Map(
            location=[np.mean(lats), np.mean(lons)], 
            zoom_start=19, 
            max_zoom=22, 
            tiles=None
        )
        
        # Tambah Google Satellite dengan 'max_native_zoom'
        # Google biasanya ada imej sehingga level 20, level 21-22 akan di-stretch secara automatik
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google Satellite',
            name='Google Satellite',
            overlay=False,
            max_zoom=22,
            max_native_zoom=20
        ).add_to(m)

        # A. LUKIS SEMPADAN & LABEL BERING/JARAK
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)] # Loop balik ke titik pertama
            
            # Lukis garisan sempadan
            folium.PolyLine([p1, p2], color="yellow", weight=3, opacity=0.8).add_to(m)
            
            # Kira B&J menggunakan koordinat asal (E, N)
            brg, dist = calculate_bearing_distance(e[i], n[i], e[(i+1)%len(e)], n[(i+1)%len(n)])
            
            # Letak label di tengah-tengah garisan
            mid_lat = (p1[0] + p2[0]) / 2
            mid_lon = (p1[1] + p2[1]) / 2
            
            folium.Marker(
                [mid_lat, mid_lon],
                icon=folium.DivIcon(
                    html=f'''<div style="font-size: 7pt; color: yellow; background: rgba(0,0,0,0.4); 
                          padding: 1px; border-radius: 2px; width: 60px; text-align: center;">
                          {brg}<br>{dist}</div>'''
                )
            ).add_to(m)

        # B. MARKER SETIAP STESEN
        for i in range(len(points)):
            popup_info = f"<b>STN {stn[i]}</b><br>N: {n[i]:.3f}<br>E: {e[i]:.3f}"
            
            # Bulatan kecil pada setiap stesen
            folium.CircleMarker(
                location=points[i],
                radius=4, 
                color="white", 
                fill=True, 
                fill_color="red",
                fill_opacity=1,
                popup=folium.Popup(popup_info, max_width=200)
            ).add_to(m)
            
            # Label nombor stesen
            folium.Marker(
                points[i],
                icon=folium.DivIcon(
                    html=f'<div style="font-size: 9pt; color: #00FFFF; font-weight: bold; margin-left: 8px;">{stn[i]}</div>'
                )
            ).add_to(m)

        # --- 6. PAPAR PETA ---
        st_folium(m, width="100%", height=700)

        # --- 7. ANALISIS LUAS ---
        # Formula Shoelace untuk luas
        luas_m2 = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
        
        st.write(f"### 📐 Hasil Analisis:")
        c1, c2, c3 = st.columns(3)
        c1.metric("Bilangan Stesen", len(stn))
        c2.metric("Luas (m²)", f"{luas_m2:,.2f} m²")
        c3.metric("Luas (Ekar)", f"{(luas_m2 / 4046.86):.4f} ekar")

    except Exception as err:
        st.error(f"Ralat semasa memproses fail: {err}")
else:
    st.info("Sila muat naik fail CSV untuk memulakan pemplotan.")
