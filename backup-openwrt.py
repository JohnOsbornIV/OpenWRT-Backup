import os
import time
import keyring
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

openwrt_user = keyring.get_password("openwrt", "username")
openwrt_pass = keyring.get_password("openwrt", "password")
minio_user = keyring.get_password("minio", "username")
minio_pass = keyring.get_password("minio", "password")

options = Options()
options.add_experimental_option("detach", True)
options.add_argument('--ignore-certificate-errors')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
print("✅ Launched Chrome, logging in to OpenWRT.")

driver.get("http://192.168.1.1")
time.sleep(.5)

username_field = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "luci_username"))
)

username_field.clear()
username_field.send_keys(openwrt_user)

password_field = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "luci_password"))
)
password_field.clear()
password_field.send_keys(openwrt_pass)

login_button = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, 'btn'))
)
login_button.click()

print("✅ Logged in to OpenWrt.")

time.sleep(.5)

driver.get("https://192.168.1.1/cgi-bin/luci/admin/system/flash")
generate_archive_button = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, '//button[text()="Generate archive"]'))
)
generate_archive_button.click()

print("✅ Generated archive.")

driver.get("https://192.168.1.1/cgi-bin/luci/admin/logout")
time.sleep(.5)

print("✅ Logged out of OpenWrt.")

time.sleep(.5)
download_dir = "/home/john/Downloads"

def get_latest_file(path, extension=".tar.gz"):
    files = [
        os.path.join(path, f)
        for f in os.listdir(path)
        if (
            f.endswith(extension)
            and "backup" in f.lower()
            and "openwrt" in f.lower()
            and os.path.isfile(os.path.join(path, f))
        )
    ]
    if not files:
        raise FileNotFoundError(f"No OpenWRT backup files with extension '{extension}' found in {path}")
    return max(files, key=os.path.getctime)

latest_file = get_latest_file(download_dir)
print(f"📦 Will upload: {os.path.basename(latest_file)}")

time.sleep(.5)
driver.get("http://192.168.1.111:9000/")

print("✅ Logging in to MinIO.")

minio_username_field = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "accessKey"))
)

minio_username_field.clear()
minio_username_field.send_keys(minio_user)

minio_password_field = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "secretKey"))
)
minio_password_field.clear()
minio_password_field.send_keys(minio_pass)

minio_login_button = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, 'do-login'))
)
minio_login_button.click()

print("✅ Logged in to MinIO.")

minio_backup_bucket = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, 'browse-backups'))
)
minio_backup_bucket.click()

time.sleep(1)

# Grab all hidden file inputs and send the file to the correct one
upload_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')

# Find a hidden input and upload
for upload_input in upload_inputs:
    if upload_input.is_displayed():
        continue  # skip visible ones (they're not the uploader)
    try:
        upload_input.send_keys(latest_file)
        print(f"✅ Uploaded: {latest_file}")
        break
    except Exception as e:
        print(f"❌ Failed to send file to input: {e}")

print("📦 Uploaded to MinIO.")

minio_logout_button = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, 'sign-out'))
)

input("Press Enter when you're ready to log out of MinIO.")

minio_logout_button.click()

print("✅ Logged out of MinIO.")
