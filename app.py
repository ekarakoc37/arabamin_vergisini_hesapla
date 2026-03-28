import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

# 1. SAYFA AYARLARI VE BAŞLIK
st.set_page_config(page_title="Arabamın Vergisini Hesapla", layout="wide")

st.markdown("""
    <meta name="google" content="notranslate">
    <script>document.documentElement.lang = 'tr';</script>
    <style>
    h1 a, h2 a, h3 a, h4 a, h5 a, h6 a { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌱 Arabamın Vergisini Hesapla")
st.markdown("Bu uygulama, araçların matrah ve emisyon değerlerine göre optimize edilmiş net vergi (Z) tutarını hesaplar ve çevreci alternatifler sunar.")

# 2. EVRENSEL VERGİ (Z) HESAPLAMA ALGORİTMASI
def calculate_Z_universal(B0, t0, e0, E, T, X, e_bar):
    t_e = t0 + (e0 - E) / E
    lambda_val = (e_bar - E) / e_bar
    
    B = B0 * (1 - (t_e - T)**2) + X
    G = B * t_e
    R = B * lambda_val
    
    return G - R

# 3. VERİTABANINI OTOMATİK YÜKLEME
try:
    # GitHub'daki excel dosyasını arka planda otomatik okuyoruz
    veritabani = pd.read_excel("arac_veritabani.xlsx")
    
    # Sütun isimlerindeki olası farklılıkları koda uyumlu hale getiriyoruz
    if 'Araç_Adı/Model' in veritabani.columns:
        veritabani = veritabani.rename(columns={'Araç_Adı/Model': 'Marka/Model'})
    elif 'Marka_Model' in veritabani.columns:
        veritabani = veritabani.rename(columns={'Marka_Model': 'Marka/Model'})
        
    veritabani = veritabani.rename(columns={
        'Motor_Tipi': 'Motor Tipi',
        'B0_Matrah': 'Matrah(B0)',
        'e0_Emisyon': 'Emisyon(e0)',
        't0_Katsayi': 'Katsayı (t0)'
    })
        
    if 'Marka/Model' in veritabani.columns:
        veritabani = veritabani.sort_values(by='Marka/Model').reset_index(drop=True)
        
    veritabani.index = veritabani.index + 1
    veri_okundu_mu = True
except Exception as e:
    st.error(f"⚠️ Veritabanı okunamadı! Lütfen GitHub'daki dosya adının 'arac_veritabani.xlsx' olduğundan emin olun. Hata detayı: {e}")
    veri_okundu_mu = False

if veri_okundu_mu:
    # 4. YAN MENÜ (SIDEBAR) KULLANICI GİRİŞLERİ VE ARAÇ SEÇİMİ
    st.sidebar.header("🚗 Araç Seçimi")
    arac_listesi = veritabani['Marka/Model'].tolist()
    # Araç seçme kutusunu sol menüye aldık
    secilen_araclar = st.sidebar.multiselect("Analiz edilecek araçları seçin:", arac_listesi)
    
    st.sidebar.markdown("---")
    
    st.sidebar.header("⚙️ Yasal Parametre Ayarları")
    E_HEDEF = st.sidebar.number_input("İdeal Emisyon Hedefi (E)", value=95)
    E_BAR_UST = st.sidebar.number_input("Maksimum Emisyon Sınırı (ē)", value=180)
    T_TOLERANS = st.sidebar.slider("Tolerans Katsayısı (T)", min_value=1.0, max_value=5.0, value=1.5, step=0.1) 
    X_SABIT = st.sidebar.number_input("Sabit Karbon Maliyeti (X)", value=100000)

    # 5. ARAÇ ANALİZİ VE KARŞILAŞTIRMA BÖLÜMÜ
    if secilen_araclar:
        st.subheader("📊 Araç Analizi ve Karşılaştırma Raporu")
        st.markdown("---")
        hesaplanan_sonuclar = []
        
        sutun_sayisi = 3
        for i in range(0, len(secilen_araclar), sutun_sayisi):
            kolonlar = st.columns(sutun_sayisi)
            
            for j in range(sutun_sayisi):
                if i + j < len(secilen_araclar):
                    arac_adi = secilen_araclar[i + j]
                    arac = veritabani[veritabani['Marka/Model'] == arac_adi].iloc[0]
                    
                    z_vergi = calculate_Z_universal(
                        B0=arac['Matrah(B0)'], t0=arac['Katsayı (t0)'], e0=arac['Emisyon(e0)'],
                        E=E_HEDEF, T=T_TOLERANS, X=X_SABIT, e_bar=E_BAR_UST
                    )
                    
                    toplam_fiyat = arac['Matrah(B0)'] + z_vergi
                    
                    hesaplanan_sonuclar.append({
                        'Model': arac['Marka/Model'],
                        'Matrah (TL)': arac['Matrah(B0)'],
                        'Emisyon (g/km)': arac['Emisyon(e0)'],
                        'Vergi': z_vergi,
                        'Anahtar Teslim (TL)': toplam_fiyat
                    })
                    
                    fiyat_alt = arac['Matrah(B0)'] * 0.85
                    fiyat_ust = arac['Matrah(B0)'] * 1.15
                    alternatifler = veritabani[
                        (veritabani['Matrah(B0)'] >= fiyat_alt) & 
                        (veritabani['Matrah(B0)'] <= fiyat_ust) & 
                        (veritabani['Emisyon(e0)'] < arac['Emisyon(e0)'])
                    ]
                    
                    with kolonlar[j]:
                        st.markdown(f"#### 🚗 {arac['Marka/Model']}")
                        st.metric(label="Hesaplanan Vergi (Z)", value=f"{z_vergi:,.0f} TL", delta=f"{arac['Emisyon(e0)']} g/km Emisyon", delta_color="inverse")
                        
                        if z_vergi < 0:
                            st.success("🎁 **Teşvik Kazandınız!** Çevreye duyarlı bu araç için devlet teşviki uygulanacaktır.")
                        
                        st.write(f"**Matrah (Çıplak Fiyat):** {arac['Matrah(B0)']:,.0f} TL")
                        st.info(f"🏷️ **Anahtar Teslim:** {toplam_fiyat:,.0f} TL")
                        
                        if arac['Emisyon(e0)'] == 0:
                            st.success("🌟 **Mükemmel Seçim!** SIFIR emisyon.")
                        elif not alternatifler.empty:
                            oneriler = alternatifler.sort_values(by='Emisyon(e0)').head(2)
                            oneri_metni = "\n".join([f"- {row['Marka/Model']} ({row['Emisyon(e0)']} g/km)" for _, row in oneriler.iterrows()])
                            
                            if arac['Emisyon(e0)'] > E_HEDEF:
                                st.warning(f"🌍 **Daha Çevreci Alternatifler:**\n{oneri_metni}")
                            else:
                                st.success(f"🌱 **Daha Çevreci Alternatifler:**\n{oneri_metni}")
                        else:
                            st.info("👍 Kendi segmentindeki en düşük emisyonlu araçlardan biri.")
            
            st.markdown("---")

        # 6. GRAFİK ÇİZİMİ
        if len(secilen_araclar) > 1:
            st.markdown("### Vergi (Z) Tutarı Karşılaştırması")
            modeller = [item['Model'] for item in hesaplanan_sonuclar]
            vergiler = [item['Vergi'] for item in hesaplanan_sonuclar]
            
            grafik_genislik = max(10, len(modeller) * 0.7)
            fig, ax = plt.subplots(figsize=(grafik_genislik, 6))
            
            cubuklar = ax.bar(modeller, vergiler, color='#2c3e50')
            ax.set_ylabel('Net Vergi Tutarı (TL)')
            ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',').replace(',', '.')))
            
            plt.xticks(rotation=45, ha='right')
            ax.grid(axis='y', linestyle='--', alpha=0.5)
            
            if len(modeller) <= 15:
                for cubuk in cubuklar:
                    yval = cubuk.get_height()
                    dikey_hiza = 'bottom' if yval >= 0 else 'top'
                    ax.text(cubuk.get_x() + cubuk.get_width()/2, yval, f'{int(yval):,}', ha='center', va=dikey_hiza, rotation=45 if len(modeller)>5 else 0, fontsize=9)
            
            plt.tight_layout()
            st.pyplot(fig)
            
        # 7. EXCEL OLARAK İNDİRME BÖLÜMÜ
        st.subheader("Raporu İndir")
        
        df_rapor = pd.DataFrame(hesaplanan_sonuclar)
        df_rapor.rename(columns={'Model': 'Araç Modeli', 'Vergi': 'Hesaplanan Vergi (TL)'}, inplace=True)
        
        df_rapor['Matrah (TL)'] = df_rapor['Matrah (TL)'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
        df_rapor['Hesaplanan Vergi (TL)'] = df_rapor['Hesaplanan Vergi (TL)'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
        df_rapor['Anahtar Teslim (TL)'] = df_rapor['Anahtar Teslim (TL)'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_rapor.to_excel(writer, index=False, sheet_name='Vergi_Analizi')
            worksheet = writer.sheets['Vergi_Analizi']
            
            for i, col in enumerate(df_rapor.columns):
                column_letter = chr(65 + i) 
                max_len = max(df_rapor[col].astype(str).map(len).max(), len(str(col))) + 4
                worksheet.column_dimensions[column_letter].width = max_len
        
        st.download_button(
            label="📊 Sonuçları Excel Olarak İndir",
            data=buffer.getvalue(),
            file_name="arac_vergi_raporu.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("👈 Analize başlamak için sol menüden araç veya araçlar seçiniz.")