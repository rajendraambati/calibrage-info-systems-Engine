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

# [Previous functions remain the same: extract_data, extract_emails_from_text, scrape_website_for_emails]

def main():
    st.set_page_config(
        page_title="Calibrage Info Systems",
        page_icon="🔍",
        layout="wide"
    )
    
    # [Previous styling code remains the same]
    
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
                # [Rest of the processing code remains the same]
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
            driver.quit()

if __name__ == "__main__":
    main()
