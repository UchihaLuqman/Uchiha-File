import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Sistem Plot Lot Luqman", layout="wide")

st.title("🗺️ Sistem Visualisasi Lot Tanah (Poligon)")
st.write("Sila muat naik fail CSV koordinat anda untuk membina pelan lot.")

# 2. Fungsi Muat Naik Fail (Dinamik)
uploaded_file = st.file_uploader("Pilih fail CSV koordinat", type=["csv"])

if uploaded_file is not None:
    try:
        # Membaca fail yang dimuat naik
        df = pd.read_csv(uploaded_file)
        
        # Buang baris kosong
        df = df.dropna(subset=['E', 'N'])

        # 3. Paparan Data di Sidebar
        st.sidebar.header("Data Koordinat Lot")
        st.sidebar.dataframe(df)

        # 4. Ambil List Koordinat
        e = df['E'].tolist()
        n = df['N'].tolist()
        stn = df['STN'].tolist()

        # 5. Bina Grafik Lot
        st.subheader("Pelan Lot Tanah (Bina Poligon)")
        fig, ax = plt.subplots(figsize=(10, 8))

        # A. Gabungkan data untuk tutup poligon (Bina semula dari STN 1)
        e_closed = e + [e[0]]
        n_closed = n + [n[0]]

        # B. Lukis Sempadan Lot (Hitam)
        ax.plot(e_closed, n_closed, color='black', marker='o', markersize=8, linewidth=2, label='Sempadan Lot')
        
        # C. Garis Penutup (Merah Putus-putus untuk menunjukkan sambungan akhir ke awal)
        ax.plot([e[-1], e[0]], [n[-1], n[0]], color='red', linestyle='--', linewidth=2, label='Garis Penutup')

        # D. Warnakan Lot (Warna hijau muda menandakan kawasan Lot yang berjaya dibina)
        ax.fill(e_closed, n_closed, color='green', alpha=0.2)

        # 6. Label Stesen
        for i in range(len(stn)):
            ax.annotate(f"  STN {int(stn[i])}", (e[i], n[i]), 
                        fontsize=12, fontweight='bold', verticalalignment='bottom')

        # 7. Pengaturan Tampilan
        ax.set_xlabel('Easting (E)')
        ax.set_ylabel('Northing (N)')
        ax.set_aspect('equal') # PENTING: Supaya bentuk lot tepat (tidak herot)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend()
        
        st.pyplot(fig)

        # 8. Info Penutupan & Luas
        def calculate_area(x, y):
            return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        
        luas = calculate_area(np.array(e), np.array(n))
        
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"✅ Lot berjaya dibina dari {len(stn)} stesen.")
        with col2:
            st.info(f"📐 Estimasi Luas Lot: {luas:.3f} unit persegi")

    except Exception as err:
        st.error(f"Ralat semasa membaca fail: {err}")
else:
    st.info("Sila muat naik fail CSV (Pastikan ada kolum 'STN', 'E', 'N') untuk melihat Lot.")