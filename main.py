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

def preview_data(data, max_rows=10):
    """
    預覽和檢視 CSV 資料
    
    Args:
        data: 解析後的資料
        max_rows: 最多顯示幾行資料
    """
    print("\n" + "="*80)
    print("📊 CSV 資料預覽")
    print("="*80)
    
    if not data:
        print("❌ 沒有資料可以顯示")
        return
    
    # 顯示基本資訊
    print(f"📋 總共有 {len(data)} 筆資料")
    
    # 顯示欄位名稱
    if data:
        columns = list(data[0].keys())
        print(f"📄 欄位名稱 ({len(columns)} 個欄位):")
        for i, col in enumerate(columns, 1):
            print(f"   {i}. {col}")
    
    print("\n" + "-"*80)
    print(f"📖 前 {min(max_rows, len(data))} 筆資料內容:")
    print("-"*80)
    
    # 顯示前幾筆資料
    for i, row in enumerate(data[:max_rows], 1):
        print(f"\n📝 第 {i} 筆資料:")
        for key, value in row.items():
            # 限制顯示長度，避免過長的內容
            display_value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
            print(f"   {key}: {display_value}")
    
    if len(data) > max_rows:
        print(f"\n... (還有 {len(data) - max_rows} 筆資料未顯示)")
    
    print("\n" + "="*80)
    print("✅ 資料預覽完成！")
    print("="*80)

def save_data_to_json(data, filename="csv_data_preview.json"):
    """
    將資料儲存為 JSON 檔案以便檢視
    
    Args:
        data: 要儲存的資料
        filename: 檔案名稱
    """
    try:
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 資料已儲存到 {filename}")
        print(f"📁 你可以下載這個檔案來檢視完整資料")
        return True
    except Exception as e:
        print(f"❌ 儲存檔案失敗: {e}")
        return False

def main():
    """主要執行函數 - 簡化版本，只測試 CSV 下載和資料檢視"""
    # 配置參數 - 台南市水利局抽水站資料查詢
    WEBSITE_URL = "https://wrbpu.tainan.gov.tw/TainanPumpWeb/PumpInfo/PumpQuantityReport_AlonePage.aspx"  # 台南市抽水站資料
    DOWNLOAD_BUTTON_SELECTOR = "#QueryButton"  # 查詢按鈕選擇器
    
    # 暫時註解掉 API 相關設定，先專注在資料擷取
    # API_URL = "https://your-api-endpoint.com/upload"  # 你的 API 端點
    # API_KEY = os.getenv("API_KEY")  # 從環境變數獲取 API 金鑰
    
    driver = None
    
    try:
        print("🚀 開始執行 CSV 資料擷取測試...")
        
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
        
        # 步驟 5: 預覽資料內容
        preview_data(raw_data, max_rows=5)  # 只顯示前5筆資料
        
        # 步驟 6: 儲存資料為 JSON 檔案供檢視
        save_data_to_json(raw_data)
        
        # 步驟 7: 轉換數據格式（暫時只顯示，不傳送 API）
        transformed_data = transform_data(raw_data)
        print(f"\n🔄 資料轉換完成，共 {len(transformed_data)} 筆轉換後的資料")
        
        # 預覽轉換後的資料
        print("\n📋 轉換後資料預覽:")
        if transformed_data:
            print("轉換後的第一筆資料格式:")
            for key, value in transformed_data[0].items():
                print(f"   {key}: {value}")
        
        # 暫時註解掉 API 傳送，等確認資料正確後再啟用
        # 步驟 8: 傳送到 API (暫時跳過)
        # api_success = send_to_api(transformed_data, API_URL, API_KEY)
        
        print("\n🎉 CSV 資料擷取測試完成！")
        print("📋 請檢查上方的資料預覽，確認是否符合預期")
        print("📁 完整資料已儲存為 csv_data_preview.json 檔案")
        
        # 清理下載的文件（可選）
        # if os.path.exists(csv_file_path):
        #     os.remove(csv_file_path)
        #     print("🗑️ 已清理臨時文件")
            
    except Exception as e:
        print(f"❌ 主程式執行錯誤: {e}")
        
    finally:
        # 確保瀏覽器關閉
        if driver:
            driver.quit()
            print("🔒 瀏覽器已關閉")

if __name__ == "__main__":
    main()
