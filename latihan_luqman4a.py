import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
import math
import json
from folium.plugins import Fullscreen

# --- 1. PENGURUSAN PASSWORD & SESSION ---
if 'password' not in st.session_state:
    st.session_state['password'] = 'admin123'  # Password default
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login_page():
    st.title("🔐 Log Masuk Sistem")
    user_id = st.text_input("Type ID / Nama")
    pwd = st.text_input("Password", type="password")
    
    col1, col2 = st.columns([1, 4])
    if col1.button("Login"):
        if pwd == st.session_state['password']:
            st.session_state['logged_in'] = True
            st.session_state['user_name'] = user_id
            st.rerun()
        else:
            st.error("Password salah!")
            
    if col2.button("Lupa Password?"):
        new_pwd = st.text_input("Masukkan Password Baru")
        if new_pwd:
            st.session_state['password'] = new_pwd
            st.success(f"Password baru disimpan: {new_pwd}")

# --- 2. CONFIG PAGE ---
if st.session_state['logged_in']:
    st.set_page_config(page_title="Johor Grid PRO", layout="wide")
    
    # --- SIDEBAR (TETAPAN) ---
    st.sidebar.title(f"👋 Hi, {st.session_state['user_name']}")
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Tetapan Paparan")
    
    size_stn = st.sidebar.slider("Saiz Label Stesen", 5, 20, 10)
    size_bj = st.sidebar.slider("Saiz Label Bering/Jarak", 5, 15, 8)
    line_weight = st.sidebar.slider("Ketebalan Garisan", 1, 10, 3)
    
    if st.sidebar.button("Log Keluar"):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- FUNGSI MATEMATIK ---
    def calculate_bearing_distance(e1, n1, e2, n2):
        de = e2 - e1
        dn = n2 - n1
        distance = math.sqrt(de**2 + dn**2)
        bearing = math.degrees(math.atan2(de, dn))
        if bearing < 0: bearing += 360
        d = int(bearing)
        m = int((bearing - d) * 60)
        return f"{d}°{m:02d}'", f"{distance:.2f}m", distance

    def convert_johor_to_wgs84(e_list, n_list):
        transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(e_list, n_list)
        return lat, lon

    st.title("🗺️ Sistem Plot Lot Johor Grid PRO")

    uploaded_file = st.file_uploader("Muat naik CSV (STN, E, N)", type=["csv"])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df = df.dropna(subset=['E', 'N'])
            e, n, stn = df['E'].tolist(), df['N'].tolist(), df['STN'].tolist()
            lats, lons = convert_johor_to_wgs84(e, n)
            points = list(zip(lats, lons))

            # --- ANALISIS LUAS & PERIMETER ---
            luas_m2 = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
            total_perimeter = 0
            
            # Peta Setup
            m = folium.Map(location=[np.mean(lats), np.mean(lons)], zoom_start=19, max_zoom=22)
            Fullscreen(position="topright", title="Skrin Penuh", title_cancel="Keluar").add_to(m)
            
            folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                attr='Google Satellite', name='Google Satellite', max_zoom=22, max_native_zoom=20
            ).add_to(m)

            # Lukis Polygon (Lot) - Klik untuk info luas/perimeter
            poly_info = f"<b>INFO LOT</b><br>Luas: {luas_m2:.2f} m²<br>Luas: {(luas_m2/4046.86):.4f} Ekar"
            folium.Polygon(
                locations=points,
                color="yellow",
                weight=line_weight,
                fill=True,
                fill_color="yellow",
                fill_opacity=0.1,
                popup=folium.Popup(poly_info, max_width=200)
            ).add_to(m)

            # Bering, Jarak & Perimeter Calculation
            for i in range(len(points)):
                p1, p2 = points[i], points[(i + 1) % len(points)]
                brg, dist_str, dist_val = calculate_bearing_distance(e[i], n[i], e[(i+1)%len(e)], n[(i+1)%len(n)])
                total_perimeter += dist_val
                
                mid = [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2]
                folium.Marker(mid, icon=folium.DivIcon(html=f'''<div style="font-size: {size_bj}pt; color: yellow; background: rgba(0,0,0,0.5); text-align: center; width: 60px;">{brg}<br>{dist_str}</div>''')).add_to(m)

            # Marker Stesen
            for i in range(len(points)):
                # Klik stesen keluar koordinat
                stn_popup = f"<b>STN {stn[i]}</b><hr>N: {n[i]:.3f}<br>E: {e[i]:.3f}"
                folium.CircleMarker(location=points[i], radius=5, color="white", fill=True, fill_color="red", popup=folium.Popup(stn_popup, max_width=150)).add_to(m)
                folium.Marker(points[i], icon=folium.DivIcon(html=f'<div style="font-size: {size_stn}pt; color: cyan; font-weight: bold; margin-left: 10px;">{stn[i]}</div>')).add_to(m)

            # Papar Peta
            st_folium(m, width="100%", height=600)

            # Statistik Luas
            st.write("### 📊 Ringkasan Maklumat Lot")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Perimeter", f"{total_perimeter:.2f} m")
            c2.metric("Luas (m²)", f"{luas_m2:.2f}")
            c3.metric("Luas (Ekar)", f"{(luas_m2 / 4046.86):.4f}")
            
            # --- FUNGSI EXPORT QGIS (GEOJSON) ---
            features = [{
                "type": "Feature",
                "properties": {"Luas_m2": luas_m2, "Perimeter": total_perimeter},
                "geometry": {"type": "Polygon", "coordinates": [[ [lon, lat] for lat, lon in points ] + [[lons[0], lats[0]]]]}
            }]
            geojson_data = json.dumps({"type": "FeatureCollection", "features": features})
            c4.download_button("📥 Export QGIS (GeoJSON)", data=geojson_data, file_name="lot_johor.geojson", mime="application/json")

        except Exception as err:
            st.error(f"Ralat: {err}")
    else:
        st.info("Sila muat naik CSV.")

else:
    login_page()
