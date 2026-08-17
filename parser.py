import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_cybershoke_duels_connects(gm):
    url = "https://cybershoke.net/ru/cs2/servers/duels"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Использование нового, более стабильного headless-режима
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")       # Обязательно для стабильности на Linux (Ubuntu/Debian)
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080") # Разворачиваем окно на Full HD, чтобы кнопки не спрятались
    chrome_options.add_argument("--lang=ru")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    server_data = []
    
    try:
        print("1. Загружаем страницу Cybershoke...")
        driver.get(url)
        
        # Ставим ожидание в 10 секунд
        wait = WebDriverWait(driver, 5)
        
        print(f"2. Ищем кнопку фильтра для карты: {gm.upper()}...")
        
        # Переводим в верхний регистр (DUST2 / MIRAGE), так как на кнопках текст капсом
        search_target = "DUST2" if gm.lower() == 'dust' else "MIRAGE"
        
        # Ищем кнопку, которая содержит в себе текст нужной карты (без жесткой привязки к классам или точной строке)
        xpath_selector = f"//button[contains(., '{search_target}')]"
        
        gbutton = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_selector)))
            
        print(f"3. Нажимаем на кнопку фильтра '{search_target}'...")
        # Кликаем через выполнение JS, чтобы обойти возможное перекрытие другими элементами
        driver.execute_script("arguments[0].click();", gbutton)
        
        print("4. Ждем 4 секунды, чтобы список серверов обновился...")
        time.sleep(1)
        
        print("5. Парсим DOM-дерево через BeautifulSoup...")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Регулярное выражение для извлечения IP:PORT из ссылки
        ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{1,5}\b')
        
        # Поиск контейнеров серверов (на скриншоте у них id начинается с "server")
        server_blocks = soup.find_all(lambda tag: tag.name == 'div' and tag.get('id', '').startswith('server'))
        
        # Резервный поиск, если структура id поменялась
        if not server_blocks:
            connect_links = soup.find_all('a', href=re.compile(r'\+connect'))
            server_blocks = [link.find_parent('div') for link in connect_links if link.find_parent('div')]

        print(f"6. Найдено сырых блоков для анализа: {len(server_blocks)}")

        for block in server_blocks:
            # Вытаскиваем ссылку с коннектом
            link_tag = block.find('a', href=re.compile(r'\+connect'))
            if not link_tag:
                continue
                
            href_value = link_tag.get('href', '')
            ip_match = ip_pattern.search(href_value)
            if not ip_match:
                continue
                
            ip_port = ip_match.group(0)
            
            # Вытаскиваем блок с онлайном (по классу со скриншота)
            info_tag = block.find('div', class_='block-servers-group-info')
            
            if info_tag:
                # Получаем чистый текст со всеми внутренними цифрами
                raw_text = info_tag.get_text(separator=" ").strip()
                
                # Ищем цифры онлайна: регулярка ищет паттерны типа "0 / 16", "8/16" или просто "8 16"
                online_match = re.search(r'([0-9]{1,2})\s*/?\s*([0-9]{1,2})', raw_text)
                if online_match:
                    online = f"{online_match.group(1)}/{online_match.group(2)}"
                else:
                    # Если разделитель не нашелся, берем первые попавшиеся цифры в теге
                    digits = re.findall(r'\d+', raw_text)
                    online = f"{digits[0]}/{digits[1]}" if len(digits) >= 2 else "?/?"
            else:
                online = "?/?"
            
            # Добавляем, исключая дубликаты
            if not any(s['connect'] == f"connect {ip_port}" for s in server_data):
                server_data.append({
                    "connect": f"connect {ip_port}",
                    "online": online
                })

    except Exception as e:
        print(f"❌ Произошла ошибка во время работы скрипта: {e}")
    finally:
        driver.quit()
        
    return server_data

if __name__ == "__main__":
    # Тестируем сбор для dust
    servers = get_cybershoke_duels_connects('dust')
    
    print(f"\nНайдено серверов: {len(servers)}")
    print("-" * 50)
    for s in servers:
        print(f"{s['connect']} | Онлайн: {s['online']}")
    print("-" * 50)
