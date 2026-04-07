# DICOM Viewer

Professional DICOM (Digital Imaging and Communications in Medicine) görüntüleme yazılımı.

## Özellikler

- **DICOM Dosya Yükleme**: Tek dosya veya klasör olarak DICOM serisi yükleme
- **Window/Level Ayarı**: Sağ tık sürükleme ile parlaklık ve kontrast ayarı
- **Zoom & Pan**: Fare tekerleği ile yakınlaşma, sol tık ile kaydırma
- **Seri Gezinme**: Slider veya Ctrl+Tekerlek ile kesitler arası geçiş
- **Metadata Görüntüleyici**: Hasta bilgileri, çekim tarihi, modalite vb.
- **Koyu Tema**: Modern medikal standartlara uygun arayüz

## Kurulum

```bash
pip install -r requirements.txt
```

## Kullanım

```bash
python3 main.py
```

## Klavye Kısayolları

- `Ctrl+O`: Tek dosya aç
- `Ctrl+Shift+O`: Klasör aç
- `Ctrl+Q`: Çıkış

## Fare Kontrolleri

- **Sağ tık sürükleme**: Window/Level (parlaklık/kontrast) ayarı
- **Sol tık sürükleme**: Pan (kaydırma)
- **Tekerlek**: Zoom (yakınlaştırma/uzaklaştırma)
- **Ctrl + Tekerlek**: Slice değiştirme

## Gereksinimler

- Python 3.10+
- PyQt6
- pydicom
- numpy
- pyqtgraph

## Lisans

MIT License