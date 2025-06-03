import os
import time
import csv
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    """設定 Chrome 瀏覽器選項"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 無界面模式
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # 設定下載路徑
    download_path = "/tmp/downloads"  # GitHub Actions 的臨時目錄
    os.makedirs(download_path, exist_ok=True)
    
    prefs = {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    return webdriver.Chrome(options=chrome_options)

def download_csv_file(driver, website_url, button_selector):
    """
    自動點擊下載按鈕下載 CSV 文件
    
    Args:
        driver: WebDriver 實例
        website_url: 目標網站 URL
        button_selector: 下載按鈕的選擇器
    """
    try:
        print(f"正在訪問網站: {website_url}")
        driver.get(website_url)
        
        # 等待頁面載入完成
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 如果需要登入，在這裡添加登入邏輯
        # login_if_needed(driver)
        
        # 等待下載按鈕出現並點擊
        print("等待下載按鈕...")
        download_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector))
        )
        
        print("點擊下載按鈕...")
        download_button.click()
        
        # 等待文件下載完成
        print("等待文件下載...")
        time.sleep(10)  # 根據文件大小調整等待時間
        
        return True
        
    except Exception as e:
        print(f"下載過程發生錯誤: {e}")
        return False

def login_if_needed(driver):
    """如果需要登入，在這裡實作登入邏輯"""
    # 範例登入流程
    try:
        # 檢查是否需要登入
        if "login" in driver.current_url.lower():
            username_field = driver.find_element(By.ID, "username")
            password_field = driver.find_element(By.ID, "password")
            
            # 使用環境變數存儲帳號密碼（安全做法）
            username_field.send_keys(os.getenv("WEBSITE_USERNAME", ""))
            password_field.send_keys(os.getenv("WEBSITE_PASSWORD", ""))
            
            login_button = driver.find_element(By.ID, "login-button")
            login_button.click()
            
            # 等待登入完成
            WebDriverWait(driver, 10).until(
                EC.url_changes(driver.current_url)
            )
            print("登入成功")
    except Exception as e:
        print(f"登入過程發生錯誤: {e}")

def find_latest_csv_file(download_path="/tmp/downloads"):
    """找到最新下載的 CSV 文件"""
    try:
        csv_files = [f for f in os.listdir(download_path) if f.endswith('.csv')]
        if not csv_files:
            print("沒有找到 CSV 文件")
            return None
            
        # 找到最新的文件
        latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(download_path, x)))
        file_path = os.path.join(download_path, latest_file)
        print(f"找到 CSV 文件: {file_path}")
        return file_path
        
    except Exception as e:
        print(f"查找 CSV 文件時發生錯誤: {e}")
        return None

def parse_csv_data(csv_file_path):
    """
    解析 CSV 數據
    
    Args:
        csv_file_path: CSV 文件路徑
        
    Returns:
        解析後的數據列表
    """
    try:
        data = []
        print(f"正在解析 CSV 文件: {csv_file_path}")
        
        with open(csv_file_path, 'r', encoding='utf-8-sig') as file:  # utf-8-sig 處理 BOM
            csv_reader = csv.DictReader(file)
            
            for row_num, row in enumerate(csv_reader, 1):
                # 清理數據（移除空白字符）
                cleaned_row = {key.strip(): value.strip() for key, value in row.items() if key}
                
                # 這裡可以添加數據驗證和轉換邏輯
                if cleaned_row:  # 只添加非空行
                    data.append(cleaned_row)
            
        print(f"成功解析 {len(data)} 行數據")
        return data
        
    except Exception as e:
        print(f"解析 CSV 文件時發生錯誤: {e}")
        return []

def transform_data(raw_data):
    """
    轉換數據格式以符合 API 要求
    
    Args:
        raw_data: 原始 CSV 數據
        
    Returns:
        轉換後的數據
    """
    transformed_data = []
    
    for row in raw_data:
        # 根據你的 API 需求轉換數據格式
        # 這是一個範例，你需要根據實際情況修改
        transformed_row = {
            "id": row.get("ID", ""),
            "name": row.get("Name", ""),
            "value": float(row.get("Value", 0)) if row.get("Value", "").replace(".", "").isdigit() else 0,
            "date": row.get("Date", ""),
            "category": row.get("Category", ""),
            # 添加其他需要的欄位轉換
        }
        transformed_data.append(transformed_row)
    
    return transformed_data

def send_to_api(data, api_url, api_key=None):
    """
    將數據傳送到指定的 API
    
    Args:
        data: 要傳送的數據
        api_url: API 端點 URL
        api_key: API 金鑰（如果需要）
        
    Returns:
        API 回應結果
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "CSV-Auto-Upload/1.0"
        }
        
        # 如果有 API 金鑰，添加到 headers
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            # 或者根據 API 要求使用其他格式
            # headers["X-API-Key"] = api_key
        
        # 準備要傳送的數據
        payload = {
            "data": data,
            "timestamp": time.time(),
            "source": "automated_csv_upload"
        }
        
        print(f"正在傳送數據到 API: {api_url}")
        print(f"數據量: {len(data)} 筆記錄")
        
        # 傳送 POST 請求
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # 檢查回應狀態
        if response.status_code == 200:
            print("✅ 數據傳送成功！")
            print(f"API 回應: {response.json()}")
            return True
        else:
            print(f"❌ API 回應錯誤: {response.status_code}")
            print(f"錯誤內容: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ API 請求超時")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 API")
        return False
    except Exception as e:
        print(f"❌ 傳送數據時發生錯誤: {e}")
        return False

def main():
    """主要執行函數"""
    # 配置參數 - 根據你的實際需求修改
    WEBSITE_URL = "https://your-target-website.com/download-page"  # 目標網站
    DOWNLOAD_BUTTON_SELECTOR = "#download-csv-btn"  # 下載按鈕的 CSS 選擇器
    API_URL = "https://your-api-endpoint.com/upload"  # 你的 API 端點
    API_KEY = os.getenv("API_KEY")  # 從環境變數獲取 API 金鑰
    
    driver = None
    
    try:
        print("🚀 開始執行自動化流程...")
        
        # 步驟 1: 設定瀏覽器
        driver = setup_driver()
        
        # 步驟 2: 下載 CSV 文件
        success = download_csv_file(driver, WEBSITE_URL, DOWNLOAD_BUTTON_SELECTOR)
        if not success:
            print("❌ 文件下載失敗")
            return
        
        # 步驟 3: 找到下載的 CSV 文件
        csv_file_path = find_latest_csv_file()
        if not csv_file_path:
            print("❌ 找不到下載的 CSV 文件")
            return
        
        # 步驟 4: 解析 CSV 數據
        raw_data = parse_csv_data(csv_file_path)
        if not raw_data:
            print("❌ CSV 數據解析失敗")
            return
        
        # 步驟 5: 轉換數據格式
        transformed_data = transform_data(raw_data)
        
        # 步驟 6: 傳送到 API
        api_success = send_to_api(transformed_data, API_URL, API_KEY)
        
        if api_success:
            print("🎉 整個流程執行成功！")
        else:
            print("❌ API 傳送失敗")
        
        # 清理下載的文件（可選）
        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)
            print("🗑️ 已清理臨時文件")
            
    except Exception as e:
        print(f"❌ 主程式執行錯誤: {e}")
        
    finally:
        # 確保瀏覽器關閉
        if driver:
            driver.quit()
            print("🔒 瀏覽器已關閉")

if __name__ == "__main__":
    main()
