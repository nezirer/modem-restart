# Zyxel EX3501-T0 Modem Otomatik Yeniden Başlatma Scripti

Modem arayüzüne otomatik giriş yapıp yeniden başlatma işlemini yapan basit bir Python scripti. Zyxel EX3501-T0 modem için yazıldı ama başka Zyxel modemlerde de çalışabilir.

## Ne İşe Yarar?

Modem her iki günde bir sabah 06:30'da otomatik olarak yeniden başlatılır. Manuel olarak yapmanıza gerek kalmaz.

## Nasıl Çalışıyor?

1. Modem arayüzüne giriş yapar (192.168.1.1)
2. Gerekirse uyarıları atlar (başka kullanıcı oturumu, şifre yenileme vs.)
3. Menüden yeniden başlat butonuna tıklar
4. İşlem tamamlanır

ChromeDriver'ı da yüklemeniz gerekiyor. Chrome tarayıcısı yüklüyse, ChromeDriver'ı [buradan](https://chromedriver.chromium.org/downloads) indirip PATH'e ekleyin.


python modem_restart.py

Script çalışmaya başlar ve her gün 06:30'da kontrol eder. Eğer son çalıştırmadan 2 gün geçtiyse yeniden başlatma yapar.

### Arka Planda Çalıştırma

Terminal kapansa bile çalışmaya devam etmesi için:

```bash
nohup python modem_restart.py > output.log 2>&1 &
```

Bu şekilde terminali kapatabilirsiniz, script çalışmaya devam eder.

### Durdurma

Çalışan scripti durdurmak için:

```bash
ps aux | grep modem_restart.py
kill <PID>
```


## Ayarlar

Modem IP'si, kullanıcı adı veya şifresini değiştirmek için `modem_restart.py` dosyasının başındaki değişkenleri düzenleyin:

```python
MODEM_IP = "192.168.1.1"
USERNAME = "admin"
PASSWORD = "admin"
```

Tüm işlemler `modem_restart.log` dosyasına kaydedilir. Scriptin çalışıp çalışmadığını buradan kontrol edebilirsiniz.

- `modem_restart.log` dosyasına bakın, hata mesajları orada
- ChromeDriver'ın doğru yüklendiğinden emin olun

İstediğiniz gibi kullanabilirsiniz, sorumluluk size aittir.
