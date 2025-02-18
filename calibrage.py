import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import re
from bs4 import BeautifulSoup
import requests
import io

def setup_chrome_driver():
    """
    Set up and return a Chrome WebDriver with automatic ChromeDriver installation
    """
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--headless")
        
        # Use webdriver_manager to automatically install and manage ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        st.error(f"Error setting up ChromeDriver: {str(e)}")
        st.info("Installing ChromeDriver automatically...")
        try:
            # Force reinstall ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as e:
            st.error(f"Failed to install ChromeDriver: {str(e)}")
            return None

def extract_data(xpath, driver):
    """
    Extract data from the page using the provided XPath.
    If the element exists, return its text; otherwise, return "N/A".
    """
    try:
        element = driver.find_element(By.XPATH, xpath)
        return element.text
    except:
        return "N/A"

def scrape_google_maps(search_query, driver):
    try:
        # Open Google Maps
        driver.get("https://www.google.com/maps")
        time.sleep(5)  # Wait for the page to load
        
        # Enter the search query into the search box
        search_box = driver.find_element(By.XPATH, '//input[@id="searchboxinput"]')
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.ENTER)
        time.sleep(5)  # Wait for results to load
        
        # Zoom out globally to ensure all results are loaded
        actions = ActionChains(driver)
        for _ in range(10):  # Zoom out multiple times
            actions.key_down(Keys.CONTROL).send_keys("-").key_up(Keys.CONTROL).perform()
            time.sleep(1)  # Wait for the map to adjust
        
        # Scroll and collect all listings
        all_listings = set()  # Use a set to avoid duplicates
        previous_count = 0
        max_scrolls = 50  # Limit the number of scrolls to prevent infinite loops
        scroll_attempts = 0
        
        while scroll_attempts < max_scrolls:
            # Scroll down to load more results
            scrollable_div = driver.find_element(By.XPATH, '//div[contains(@aria-label, "Results for")]')
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            time.sleep(3)  # Wait for new results to load
            
            # Collect all visible listings
            current_listings = driver.find_elements(By.XPATH, '//a[contains(@href, "https://www.google.com/maps/place")]')
            current_count = len(current_listings)
            
            # Add new listings to the set
            for listing in current_listings:
                href = listing.get_attribute("href")
                if href:
                    all_listings.add(href)
            
            # Check if no new results were loaded
            if current_count == previous_count:
                break
            
            # Update the previous count
            previous_count = current_count
            scroll_attempts += 1
        
        # Extract details for each unique listing
        results = []
        for i, href in enumerate(all_listings):
            driver.get(href)
            time.sleep(3)  # Wait for the sidebar to load
            
            # Extract details
            name = extract_data('//h1[contains(@class, "DUwDvf lfPIob")]', driver)
            address = extract_data('//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]', driver)
            phone = extract_data('//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]', driver)
            website = extract_data('//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]', driver)
            
            # Append to results
            results.append({
                "Name": name,
                "Address": address,
                "Phone Number": phone,
                "Website": website
            })
        
        # Return results as a DataFrame
        return pd.DataFrame(results)
    
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

def extract_emails_from_text(text):
    """
    Extract email addresses from text using regex
    """
    return re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)

def scrape_website_for_emails(url):
    """
    Scrape a website for email addresses
    """
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract emails from the homepage
        emails = set(extract_emails_from_text(soup.get_text()))
        
        # Check the footer for emails
        footer = soup.find('footer')
        if footer:
            emails.update(extract_emails_from_text(footer.get_text()))
        
        # Find links to the contact page
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
        
        # Initialize Chrome driver with automatic installation
        driver = setup_chrome_driver()
        
        if driver is None:
            st.error("Failed to initialize Chrome driver. Please make sure Chrome browser is installed on your system.")
            return
        
        try:
            df = scrape_google_maps(search_query, driver)
            driver.quit()
            
            if df is not None:
                # Process websites and emails
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
                
                # Save to Excel
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
        except Exception as e:
            st.error(f"An error occurred during scraping: {str(e)}")
            if driver:
                driver.quit()

if __name__ == "__main__":
    main()
