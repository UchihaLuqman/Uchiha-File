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
    st.session_state['password'] = 'admin123'
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login_page():
    st.title("🔐 Log Masuk Sistem Plot Lot")
    user_id = st.text_input("ID Pengguna / Nama")
    pwd = st.text_input("Kata Laluan", type="password")
    
    col1, col2 = st.columns([1, 4])
    if col1.button("Login"):
        if pwd == st.session_state['password']:
            st.session_state['logged_in'] = True
            st.session_state['user_name'] = user_id
            st.rerun()
        else:
            st.error("Kata laluan salah!")
            
    if col2.button("Lupa Password?"):
        new_pwd = st.text_input("Masukkan Kata Laluan Baru")
        if new_pwd:
            st.session_state['password'] = new_pwd
            st.success(f"Kata laluan baru disimpan: {new_pwd}")

# --- 2. MAIN APPLICATION ---
if st.session_state['logged_in']:
    st.set_page_config(page_title="Johor Grid PRO", layout="wide")
    
    # --- SIDEBAR ---
    st.sidebar.title(f"👋 Hi, {st.session_state['user_name']}")
    st.sidebar.header("⚙️ Tetapan Paparan")
    size_stn = st.sidebar.slider("Saiz No. Stesen", 5, 20, 10)
    size_bj = st.sidebar.slider("Saiz Bering/Jarak", 5, 15, 9)
    line_weight = st.sidebar.slider("Ketebalan Sempadan", 1, 10, 3)
    
    if st.sidebar.button("Log Keluar"):
        st.session_state['logged_in'] = False
        st.rerun()

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
        # EPSG:4390 adalah Cassini-Soldner Johor (Grid Tempatan)
        transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(e_list, n_list)
        return lat, lon

    st.title("🗺️ Sistem Plot Lot Johor Grid PRO")
    uploaded_file = st.file_uploader("Muat naik CSV (Wajib ada column: STN, E, N)", type=["csv"])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file).dropna(subset=['E', 'N'])
            e, n, stn = df['E'].tolist(), df['N'].tolist(), df['STN'].tolist()
            lats, lons = convert_johor_to_wgs84(e, n)
            points = list(zip(lats, lons))

            # Kira Luas (Metod Shoelace)
            luas_m2 = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
            total_perimeter = 0
            
            # --- SETUP PETA & LAYER GROUPS ---
            m = folium.Map(location=[np.mean(lats), np.mean(lons)], zoom_start=19, max_zoom=22, tiles=None)
            
            fg_sat = folium.FeatureGroup(name="Google Satellite", control=True).add_to(m)
            fg_poly = folium.FeatureGroup(name="Luas/Polygon", control=True).add_to(m)
            fg_dist = folium.FeatureGroup(name="Jarak (Putih)", control=True).add_to(m)
            fg_brg = folium.FeatureGroup(name="Bering (Kuning)", control=True).add_to(m)
            fg_stn = folium.FeatureGroup(name="Stesen & Koordinat", control=True).add_to(m)

            # 1. Lapisan Satelit
            folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                attr='Google Satellite', max_zoom=22, max_native_zoom=20
            ).add_to(fg_sat)

            # 2. Lapisan Polygon (Luas)
            poly_info = f"<div style='font-family: Arial;'><b>INFO LOT</b><br>Luas: {luas_m2:.2f} m²</div>"
            folium.Polygon(
                locations=points, color="yellow", weight=line_weight,
                fill=True, fill_color="yellow", fill_opacity=0.2,
                popup=folium.Popup(poly_info, max_width=200)
            ).add_to(fg_poly)

            # 3. Lapisan Bering, Jarak & Stesen
            for i in range(len(points)):
                # Dapatkan koordinat stesen semasa (p1) dan stesen seterusnya (p2)
                p1, p2 = points[i], points[(i + 1) % len(points)]
                brg, dist_str, dist_val = calculate_bearing_distance(e[i], n[i], e[(i+1)%len(e)], n[(i+1)%len(n)])
                total_perimeter += dist_val
                mid = [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2]

                # Label Jarak
                folium.Marker(mid, icon=folium.DivIcon(html=f'<div style="font-size:{size_bj}pt; color:white; background:rgba(0,0,0,0.5); width:55px; text-align:center; border-radius:3px;">{dist_str}</div>')).add_to(fg_dist)
                
                # Label Bering (Sedikit offset supaya tak bertindih)
                folium.Marker([mid[0]+0.00001, mid[1]], icon=folium.DivIcon(html=f'<div style="font-size:{size_bj}pt; color:yellow; font-weight:bold; text-shadow: 1px 1px #000;">{brg}</div>')).add_to(fg_brg)

                # --- FUNGSI KLIK KOORDINAT ---
                stn_popup_html = f"""
                    <div style="font-family: Arial; width: 140px;">
                        <b style="color:red; font-size:14px;">STN: {stn[i]}</b><br>
                        <hr style="margin: 4px 0;">
                        <b>N:</b> {n[i]:.3f}<br>
                        <b>E:</b> {e[i]:.3f}
                    </div>
                """
                
                # Titik Stesen (Boleh diklik)
                folium.CircleMarker(
                    location=points[i], 
                    radius=6, 
                    color="red", 
                    fill=True, 
                    fill_color="red",
                    fill_opacity=0.9,
                    popup=folium.Popup(stn_popup_html, max_width=250)
                ).add_to(fg_stn)

                # Label No Stesen (pointer-events:none supaya tak ganggu klik pada titik)
                folium.Marker(
                    location=points[i], 
                    icon=folium.DivIcon(
                        html=f'<div style="font-size:{size_stn}pt; color:cyan; font-weight:bold; margin-left:12px; pointer-events:none; text-shadow: 1px 1px #000;">{stn[i]}</div>'
                    )
                ).add_to(fg_stn)

            # Control Panel & Fullscreen
            folium.LayerControl(collapsed=False).add_to(m)
            Fullscreen().add_to(m)

            # Papar Peta
            st_folium(m, width="100%", height=650)

            # Statistik & Export
            st.write("---")
            st.write("### 📊 Ringkasan Lot")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Perimeter (m)", f"{total_perimeter:.2f}")
            c2.metric("Luas (m²)", f"{luas_m2:.2f}")
            c3.metric("Luas (Ekar)", f"{(luas_m2 / 4046.856):.4f}")
            
            # Export GeoJSON
            features = [{"type": "Feature", "properties": {"Luas_m2": luas_m2}, "geometry": {"type": "Polygon", "coordinates": [[ [lon, lat] for lat, lon in points ] + [[lons[0], lats[0]]]]}}]
            geojson_data = json.dumps({"type": "FeatureCollection", "features": features})
            c4.download_button("📥 Download GeoJSON", data=geojson_data, file_name="lot_johor.geojson", mime="application/json")

        except Exception as err:
            st.error(f"Terjadi ralat semasa memproses fail: {err}")
    else:
        st.info("Sila muat naik fail CSV untuk bermula. Pastikan format: STN, E, N")
else:
    login_page()
