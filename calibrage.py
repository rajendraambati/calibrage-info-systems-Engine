import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import re
from bs4 import BeautifulSoup
import requests
import io

# Function to extract data using XPath
def extract_data(xpath, driver):
    try:
        element = driver.find_element(By.XPATH, xpath)
        return element.text
    except:
        return "N/A"

# Main function to scrape Google Maps
def scrape_google_maps(search_query, driver):
    try:
        driver.get("https://www.google.com/maps")
        time.sleep(5)
        
        search_box = driver.find_element(By.XPATH, '//input[@id="searchboxinput"]')
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.ENTER)
        time.sleep(5)
        
        actions = ActionChains(driver)
        for _ in range(10):
            actions.key_down(Keys.CONTROL).send_keys("-").key_up(Keys.CONTROL).perform()
            time.sleep(1)
        
        all_listings = set()
        previous_count = 0
        max_scrolls = 50
        scroll_attempts = 0
        
        while scroll_attempts < max_scrolls:
            scrollable_div = driver.find_element(By.XPATH, '//div[contains(@aria-label, "Results for")]')
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            time.sleep(3)
            
            current_listings = driver.find_elements(By.XPATH, '//a[contains(@href, "https://www.google.com/maps/place")]')
            current_count = len(current_listings)
            
            for listing in current_listings:
                href = listing.get_attribute("href")
                if href:
                    all_listings.add(href)
            
            if current_count == previous_count:
                break
            
            previous_count = current_count
            scroll_attempts += 1
        
        results = []
        for href in all_listings:
            driver.get(href)
            time.sleep(3)
            
            name = extract_data('//h1[contains(@class, "DUwDvf lfPIob")]', driver)
            address = extract_data('//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]', driver)
            phone = extract_data('//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]', driver)
            website = extract_data('//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]', driver)
            
            results.append({
                "Name": name,
                "Address": address,
                "Phone Number": phone,
                "Website": website
            })
        
        return pd.DataFrame(results)
    
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

# Function to extract emails
def extract_emails_from_text(text):
    return re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)

# Function to scrape a website for emails
def scrape_website_for_emails(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        emails = set(extract_emails_from_text(soup.get_text()))
        
        footer = soup.find('footer')
        if footer:
            emails.update(extract_emails_from_text(footer.get_text()))
        
        contact_links = [a['href'] for a in soup.find_all('a', href=True) if 'contact' in a['href'].lower()]
        for link in contact_links:
            if not link.startswith("http"):
                link = url.rstrip("/") + "/" + link.lstrip("/")
            try:
                contact_response = requests.get(link, timeout=10)
                contact_soup = BeautifulSoup(contact_response.content, 'html.parser')
                emails.update(extract_emails_from_text(contact_soup.get_text()))
            except Exception:
                continue
        
        return list(emails)
    
    except Exception:
        return []

# Main function
def main():
    st.set_page_config(
        page_title="Calibrage Info Systems",
        page_icon="🔍",
        layout="wide"
    )

    st.markdown("""
    <style>
        .stApp {
            background-color: #000000;
        }
        .css-18e3th9 {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .stButton > button {
            background-color: #4CAF50;
            color: white;
            border-radius: 8px;
            font-size: 16px;
            height: 40px;
            width: 150px;
        }
        .stTextInput > div > div > input {
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
        }
        .stDownloadButton > button {
            background-color: #008CBA;
            color: white;
            border-radius: 8px;
            font-size: 16px;
            height: 40px;
            width: 200px;
        }
        .success-message {
            color: green;
            font-size: 20px;
        }
        .error-message {
            color: red;
            font-size: 20px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🔍 Calibrage Info Systems Data Search Engine")
    
    search_query = st.text_input("Enter the search Term Below 👇", "")
    placeholder = st.empty()
    
    if st.button("Scrap It!"):
        if not search_query.strip():
            st.error("Please enter a valid search query.")
            return
        
        placeholder.markdown("**Processing..... Please Wait**")
        
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)
        
        df = scrape_google_maps(search_query, driver)
        driver.quit()
        
        if df is not None:
            websites = df["Website"].tolist()
            email_results = []
            for website in websites:
                if website != "N/A" and isinstance(website, str) and website.strip():
                    urls_to_try = [f"http://{website}", f"https://{website}"]
                    emails_found = []
                    for url in urls_to_try:
                        emails = scrape_website_for_emails(url)
                        emails_found.extend(emails)
                    email_results.append(", ".join(set(emails_found)) if emails_found else "N/A")
                else:
                    email_results.append("N/A")
            
            df["Email"] = email_results
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
            output.seek(0)
            
            placeholder.empty()
            st.success("Done! 👇Click Download Button Below")
            st.download_button(
                label="Download Results",
                data=output,
                file_name="final_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
