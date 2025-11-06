
"""
Modem Yeniden Başlatma Scripti
Her iki günde bir sabah 06:30'da modem arayüzüne girip yeniden başlatma işlemi yapar.
"""

import time
import schedule
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('modem_restart.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Modem ayarları
MODEM_IP = "192.168.1.1"
USERNAME = "admin"
PASSWORD = "admin"
TIMEOUT = 30


def setup_driver():
    """Chrome WebDriver'ı ayarlar"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Arka planda çalışır
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        logging.error(f"WebDriver oluşturulamadı: {e}")
        raise


def restart_modem():
    """Modem arayüzüne girip yeniden başlatma işlemini yapar"""
    driver = None
    try:
        logging.info("Modem yeniden başlatma işlemi başlatılıyor...")
        
        # WebDriver'ı başlat
        driver = setup_driver()
        
        # Modem arayüzüne git
        url = f"http://{MODEM_IP}"
        logging.info(f"Modem arayüzüne bağlanılıyor: {url}")
        driver.get(url)
        time.sleep(3)
        
        # Kullanıcı adı ve şifre alanlarını bul ve doldur
        try:
            # Zyxel modem için spesifik ID'ler
            logging.info("Giriş formu alanları aranıyor...")
            
            # Kullanıcı adı alanını bul (id="username")
            username_field = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            logging.info("Kullanıcı adı alanı bulundu")
            
            # Şifre alanını bul (id="userpassword", type="password" olan masked versiyonu)
            password_field = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input#userpassword[type='password']"))
            )
            logging.info("Şifre alanı bulundu")
            
            # Giriş butonunu bul (id="loginBtn")
            login_button = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "loginBtn"))
            )
            logging.info("Giriş butonu bulundu")
            
            # Kullanıcı adını gir
            username_field.clear()
            username_field.send_keys(USERNAME)
            logging.info(f"Kullanıcı adı girildi: {USERNAME}")
            time.sleep(0.5)
            
            # Şifreyi gir
            password_field.clear()
            password_field.send_keys(PASSWORD)
            logging.info("Şifre girildi")
            time.sleep(0.5)
            
            # Butonun enable olmasını bekle (başlangıçta disabled olabilir)
            WebDriverWait(driver, 10).until(
                lambda d: not login_button.get_attribute("disabled")
            )
            logging.info("Giriş butonu aktif hale geldi")
            
            # Giriş butonuna tıkla
            driver.execute_script("arguments[0].click();", login_button)
            logging.info("Giriş butonuna tıklandı")
            
            # Giriş işleminin tamamlanmasını bekle
            time.sleep(3)
            
            # "Başka kullanıcı oturumu" uyarısını kontrol et ve "Uygula" butonuna tıkla
            try:
                alert_ok_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "alertOKBtn"))
                )
                if alert_ok_button and alert_ok_button.is_displayed():
                    logging.info("Başka kullanıcı oturumu uyarısı tespit edildi")
                    driver.execute_script("arguments[0].click();", alert_ok_button)
                    logging.info("Uygula butonuna tıklandı (oturum sonlandırıldı)")
                    time.sleep(3)  # Dialog'un kapanması için bekle
            except TimeoutException:
                logging.info("Başka kullanıcı oturumu uyarısı yok (normal)")
            except Exception as e:
                logging.warning(f"Uyarı dialog kontrolü sırasında hata: {e}")
            
            # Giriş başarılı mı kontrol et (login sayfasından çıkıldı mı?)
            time.sleep(2)  # Sayfa yüklenmesi için ek bekleme
            current_url = driver.current_url
            try:
                # Login formu hala görünüyor mu?
                login_form = driver.find_elements(By.ID, "Login-login")
                if login_form:
                    logging.warning("Giriş formu hala görünüyor, giriş başarısız olabilir")
                else:
                    logging.info("Giriş sayfasından çıkıldı, giriş başarılı görünüyor")
            except:
                logging.info("Giriş işlemi tamamlandı")
        
        except TimeoutException as e:
            logging.warning(f"Giriş formu elemanları bulunamadı (sayfa zaten giriş yapılmış olabilir): {e}")
            # Sayfa zaten giriş yapılmış olabilir, devam et
            time.sleep(2)
        except Exception as e:
            logging.warning(f"Giriş işlemi sırasında hata (sayfa zaten giriş yapılmış olabilir): {e}")
            time.sleep(2)
        
        # Şifre yenileme uyarısını kontrol et ve atla
        try:
            current_url = driver.current_url
            logging.info(f"Mevcut URL: {current_url}")
            
            # Password reset sayfasında mıyız?
            if "passwordreset" in current_url.lower() or driver.find_elements(By.ID, "Login-passwordreset"):
                logging.info("Şifre yenileme uyarısı tespit edildi, atlanıyor...")
                
                # "Atla" butonunu bul ve tıkla (id="cgPwSkip")
                skip_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "cgPwSkip"))
                )
                
                if skip_button:
                    driver.execute_script("arguments[0].click();", skip_button)
                    logging.info("Şifre yenileme uyarısı atlandı (Atla butonuna tıklandı)")
                    time.sleep(3)  # Sayfa yönlendirmesi için bekle
                else:
                    logging.warning("Atla butonu bulunamadı")
            else:
                logging.info("Şifre yenileme uyarısı yok, normal akışa devam ediliyor")
        except TimeoutException:
            logging.info("Şifre yenileme sayfası bulunamadı (normal, uyarı yok)")
        except Exception as e:
            logging.warning(f"Şifre yenileme uyarısı kontrolü sırasında hata: {e}")
            # Hata olsa bile devam et
        
        # Hamburger menüyü bul ve tıkla
        # Zyxel modem için spesifik selector: class="navbtn"
        hamburger_menu = None
        try:
            # Önce spesifik Zyxel selector'ını dene
            hamburger_menu = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.navbtn"))
            )
            logging.info("Hamburger menü bulundu (div.navbtn)")
        except TimeoutException:
            logging.warning("div.navbtn bulunamadı, alternatif selector'lar deneniyor...")
            # Alternatif selector'lar
            hamburger_selectors = [
                "button[aria-label*='menu']",
                "button[aria-label*='Menu']",
                "button[class*='menu']",
                "div[class*='navbtn']",
                "div[class*='hamburger']",
                "span[class*='hamburger']",
                "i[class*='menu']",
                "svg[class*='menu']",
                ".menu-toggle",
                "#menu-toggle"
            ]
            
            for selector in hamburger_selectors:
                try:
                    hamburger_menu = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if hamburger_menu and hamburger_menu.is_displayed():
                        logging.info(f"Hamburger menü bulundu: {selector}")
                        break
                except:
                    continue
        
        if hamburger_menu:
            driver.execute_script("arguments[0].click();", hamburger_menu)
            logging.info("Hamburger menü butonuna tıklandı")
            time.sleep(2)
            
            # Menünün açıldığını kontrol et (id="h_menu_list" görünür olmalı)
            try:
                menu_list = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "h_menu_list"))
                )
                if menu_list and menu_list.is_displayed():
                    logging.info("Hamburger menü başarıyla açıldı (h_menu_list görünür)")
                else:
                    logging.warning("Hamburger menü açıldı ama h_menu_list görünmüyor")
            except TimeoutException:
                logging.warning("h_menu_list bulunamadı, menü açılmamış olabilir")
        else:
            logging.error("Hamburger menü bulunamadı!")
            return False
        
        # Yeniden başlat butonunu bul ve tıkla
        # Zyxel modem için spesifik ID: id="navbar_reboot"
        restart_button = None
        try:
            # Önce spesifik Zyxel selector'ını dene
            restart_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "navbar_reboot"))
            )
            logging.info("Yeniden başlat butonu bulundu (id=navbar_reboot)")
        except TimeoutException:
            logging.warning("navbar_reboot bulunamadı, alternatif selector'lar deneniyor...")
            # Alternatif selector'lar
            restart_selectors = [
                "div[id*='reboot']",
                "div[id*='restart']",
                "div[class*='restart']",
                "button:contains('Yeniden Başlat')",
                "button:contains('Restart')",
                "a:contains('Yeniden Başlat')",
                "a:contains('Restart')",
                "li:contains('Yeniden Başlat')",
                "li:contains('Restart')"
            ]
            
            for selector in restart_selectors:
                try:
                    if ':contains' in selector:
                        # XPath kullan
                        restart_button = driver.find_element(By.XPATH, 
                            "//*[contains(text(), 'Yeniden Başlat') or contains(text(), 'Restart') or contains(text(), 'Reboot')]")
                    else:
                        restart_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    if restart_button and restart_button.is_displayed():
                        logging.info(f"Yeniden başlat butonu bulundu: {selector}")
                        break
                except:
                    continue
            
            # XPath ile Türkçe ve İngilizce metinleri ara (son çare)
            if not restart_button:
                xpath_queries = [
                    "//div[contains(text(), 'Yeniden Başlat') or contains(text(), 'Restart') or contains(text(), 'Reboot')]",
                    "//button[contains(text(), 'Yeniden Başlat') or contains(text(), 'Restart') or contains(text(), 'Reboot')]",
                    "//a[contains(text(), 'Yeniden Başlat') or contains(text(), 'Restart') or contains(text(), 'Reboot')]",
                    "//li[contains(text(), 'Yeniden Başlat') or contains(text(), 'Restart') or contains(text(), 'Reboot')]",
                    "//*[contains(@class, 'restart') or contains(@id, 'restart')]"
                ]
                
                for xpath in xpath_queries:
                    try:
                        restart_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        if restart_button and restart_button.is_displayed():
                            logging.info(f"Yeniden başlat butonu bulundu (XPath): {xpath}")
                            break
                    except:
                        continue
        
        if restart_button:
            driver.execute_script("arguments[0].click();", restart_button)
            logging.info("Yeniden başlat butonuna tıklandı")
            time.sleep(2)
            
            # Onay butonunu kontrol et (varsa)
            confirm_selectors = [
                "button:contains('Evet')",
                "button:contains('Yes')",
                "button:contains('Onayla')",
                "button:contains('Confirm')",
                "button[type='submit']"
            ]
            
            for selector in confirm_selectors:
                try:
                    if ':contains' in selector:
                        confirm_btn = driver.find_element(By.XPATH, 
                            "//button[contains(text(), 'Evet') or contains(text(), 'Yes') or contains(text(), 'Onayla') or contains(text(), 'Confirm')]")
                    else:
                        confirm_btn = driver.find_element(By.CSS_SELECTOR, selector)
                    if confirm_btn and confirm_btn.is_displayed():
                        driver.execute_script("arguments[0].click();", confirm_btn)
                        logging.info("Onay butonuna tıklandı")
                        break
                except:
                    continue
            
            logging.info("✓ Modem yeniden başlatma işlemi başarıyla tamamlandı!")
            return True
        else:
            logging.error("Yeniden başlat butonu bulunamadı!")
            # Sayfa kaynağını logla (debug için)
            logging.debug(f"Sayfa başlığı: {driver.title}")
            return False
        
    except TimeoutException:
        logging.error("İşlem zaman aşımına uğradı")
        return False
    except Exception as e:
        logging.error(f"Beklenmeyen hata: {e}", exc_info=True)
        return False
    finally:
        if driver:
            driver.quit()
            logging.info("WebDriver kapatıldı")


def run_scheduled_task():
    """Zamanlanmış görevi çalıştırır"""
    logging.info("=" * 50)
    logging.info("Zamanlanmış görev çalıştırılıyor...")
    restart_modem()
    logging.info("=" * 50)


def main():
    """Ana fonksiyon - zamanlamayı ayarlar ve çalıştırır"""
    logging.info("=" * 60)
    logging.info("Modem Yeniden Başlatma Scripti başlatıldı")
    logging.info("Her iki günde bir sabah 06:30'da çalışacak")
    logging.info("=" * 60)
    
    # Her gün 06:30'da kontrol et, ama sadece 2 günde bir çalıştır
    last_run_date = None
    
    def check_and_run():
        nonlocal last_run_date
        today = datetime.now().date()
        
        if last_run_date is None:
            # İlk çalıştırma - bugün tarihini kaydet ama çalıştırma
            last_run_date = today
            logging.info(f"İlk kontrol: {today}. Sonraki çalıştırma 2 gün sonra olacak.")
        else:
            # Son çalıştırmadan bu yana geçen gün sayısını kontrol et
            days_passed = (today - last_run_date).days
            if days_passed >= 2:
                last_run_date = today
                logging.info(f"2 gün geçti, yeniden başlatma işlemi çalıştırılıyor...")
                run_scheduled_task()
            else:
                logging.info(f"Henüz 2 gün geçmedi. Son çalıştırma: {last_run_date}, Bugün: {today}, Geçen gün: {days_passed}")
    
    # Her gün 06:30'da kontrol et
    schedule.every().day.at("06:30").do(check_and_run)
    
    logging.info("Zamanlayıcı ayarlandı. Her gün 06:30'da kontrol edilecek.")
    logging.info("Script arka planda çalışıyor...")
    logging.info("Script'i durdurmak için Ctrl+C tuşlarına basın")
    logging.info("=" * 60)
    
    # Sonsuz döngü - zamanlanmış görevleri kontrol et
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Her dakika kontrol et
    except KeyboardInterrupt:
        logging.info("Script kullanıcı tarafından durduruldu")


if __name__ == "__main__":
    main()

