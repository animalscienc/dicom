# DICOM Görüntüleyici - Teknik Şartname

## 1. Proje Genel Bakış

- **Proje Adı**: DICOM Viewer
- **Tip**: Masaüstü Medikal Görüntüleme Uygulaması
- **Kullanıcı Hedefi**: Radyologlar, Tıp öğrencileri ve Medikal görüntüleme uzmanları
- **Python Versiyon**: 3.10+

## 2. Teknik Yığın

| Bileşen | Teknoloji |
|---------|-----------|
| Programlama Dili | Python 3.10+ |
| GUI Framework | PyQt6 |
| DICOM Okuma | pydicom |
| Sayısal İşleme | numpy |
| Görüntüleme | pyqtgraph |

## 3. Fonksiyonel Gereksinimler

### 3.1 Dosya Yükleme
- Tek .dcm dosyası seçme (QFileDialog)
- Klasör seçme ile DICOM serisi yükleme
- Desteklenen formatlar: .dcm, .DCM

### 3.2 Görüntü Manipülasyonu
- **Window/Level (W/L)**: Sağ tık sürükleme ile parlaklık ve kontrast ayarı
- **Zoom**: Fare tekerleği ile yakınlaştırma/uzaklaştırma
- **Pan**: Sol tık sürükleme ile görüntü kaydırma

### 3.3 Seri Gezinme
- Klasör yüklendiğinde slice navigasyonu
- Slider ile kesitler arası geçiş
- Fare tekerleği ile slice değiştirme

### 3.4 Metadata Görüntüleyici
- Hasta bilgileri (Ad, Soyad, ID)
- Çekim tarihi ve zamanı
- Modalite (CT, MR, CR, DX vb.)
- Cihaz bilgileri
- Görüntü boyutları

## 4. Arayüz Tasarımı

### 4.1 Tema
- Koyu tema (Dark Mode)
- Arka plan: #1e1e1e
- Panel arka plan: #252526
- Metin rengi: #d4d4d4

### 4.2 Düzen
```
+--------------------------------------------------+
|  Menu Bar                                        |
+----------+---------------------------+----------+
|          |                           | Metadata |
| File     |    Görüntü Alanı          | Panel    |
| Info     |    (Center)               | (Right)  |
|          |                           |          |
+----------+---------------------------+----------+
|  Slider / Slice Info                           |
+--------------------------------------------------+
|  Status Bar                                     |
+--------------------------------------------------+
```

### 4.3 Renk Paleti
- Ana Arka Plan: #1e1e1e
- Panel Arka Plan: #252526
- Kenarlık: #3c3c3c
- Seçili Öğe: #094771
- Buton: #0e639c
- Metin: #d4d4d4
- Başlık: #ffffff

## 5. UI Bileşenleri

### 5.1 Menü Bar
- File: Open File, Open Folder, Exit
- View: Reset Zoom, Reset Window/Level
- Help: About

### 5.2 Ana Görüntü Alanı
- pyqtgraph.GraphicsLayoutWidget
- Mouse event handling

### 5.3 Metadata Panel
- QTableWidget veya QTreeWidget
- Etiket adı - değer çiftleri

### 5.4 Slider
- QSlider: Min-Max slice sayısı
- Label: Mevcut slice / toplam slice

### 5.5 Status Bar
- Dosya yolu
- Görüntü boyutları
- Window/Level değerleri

## 6. Modül Yapısı

```
dicom_viewer/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── ui/
│   ├── main_window.py   # MainWindow class
│   ├── image_view.py    # ImageView widget
│   └── metadata_panel.py
├── core/
│   ├── dicom_loader.py  # DICOM loading logic
│   └── image_processor.py
└── utils/
    └── constants.py     # UI constants
```

## 7. MVP Kapsamı

İlk aşamada:
- Tek dosya yükleme
- Basit görüntüleme (pyqtgraph)
- Window/Level ayarı
- Metadata gösterimi
- Koyu tema

Sonraki aşamalarda:
- Klasör yükleme
- Seri navigasyonu
- Zoom/Pan iyileştirmeleri