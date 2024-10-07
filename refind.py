
import time
import re
import csv
import random
from datetime import datetime
from datetime import datetime, timedelta

import pandas as pd
from bs4 import BeautifulSoup

from fpdf import FPDF

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def validate_address(address):
    address_regex = r'(?i)^\d+\s[A-Za-z0-9\s]+(?:\s[A-Za-z]+)?,\s[A-Za-z\s]+,\s[A-Z]{2}(?:\s\d{5})?$'
    return bool(re.match(address_regex, address))

def strip_chars(text):
    return re.sub(r'[^\d]', '', text)

def hex_to_rgb(hex_color):
    length = len(hex_color)
    if length > 5: 
        return tuple(int(hex_color[i:i + length // 3], 16) for i in range(0, length, length // 3))
    else:
        return (255, 255, 255)

def scrape_redfin(subject_property):
    options = Options()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_argument("--headless")  
    options.add_argument("--no-sandbox")  
    options.add_argument("--disable-dev-shm-usage") 
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")  
    options.add_argument("--disable-images")
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service()

    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })

    driver.get('https://www.redfin.com')

    try:
        search = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'search-box-input'))
        )
    except TimeoutException:
        try:
            search = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#search-box-input'))
            )
        except TimeoutException:
            search = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id='search-box-input']"))
            )

    search.send_keys(subject_property, Keys.RETURN)
    
    time.sleep(.3)
    driver.execute_script("window.scrollBy(0, 4000);")
    time.sleep(.2)
    driver.execute_script("window.scrollBy(0, 7000);")
    time.sleep(.2)
    driver.execute_script("window.scrollBy(0, -1000);")
    time.sleep(1)
    driver.execute_script("window.scrollBy(0, -1000);")
    time.sleep(1)
    driver.execute_script("window.scrollBy(0, -3000);")
    time.sleep(1)
    driver.execute_script("window.scrollBy(0, -1000);")
    time.sleep(1)
    driver.execute_script("window.scrollBy(0, -3000);")
    time.sleep(1)
    driver.execute_script("window.scrollBy(0, 5000);")
    time.sleep(1)
    driver.execute_script("window.scrollBy(0, -7000);")
    time.sleep(1)
    
    WebDriverWait(driver, 3000).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'top-stats'))
    )
    WebDriverWait(driver, 3000).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'KeyDetailsTable'))
    )
    WebDriverWait(driver, 3000).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'comps'))
    )
    
    data = driver.page_source

    scraped_data = BeautifulSoup(data, 'html.parser')

    driver.quit()

    return scraped_data

def parse_subject(soup):
    # parse address
    raw_address, trash1, trash2 = soup.title.text.split('|')
    sub_address = raw_address.lstrip('\n').strip()

    # parse bed
    try:
        sub_bed = int(soup.select_one('[data-rf-test-id="abp-beds"] .statsValue').text.strip())
    except:
        sub_bed = 'N/A'

    # parse bath
    try:
        sub_bath = float(soup.select_one('[data-rf-test-id="abp-baths"] .statsValue').text.strip())
    except:
        sub_bath = 'N/A'

    # parse price if listed - include price under dataframe, else label as redfin value under dataframe
    listing_price = soup.select_one('[data-rf-test-id="abp-price"] .statsValue').text
    if listing_price:
        sub_price = int(listing_price.replace("$", "").replace(",", ""))
    else:
        sub_price = 'N/A'

    # parse sqft
    try:
        sub_sqft = int(soup.select_one('[data-rf-test-id="abp-sqFt"] .statsValue').text.replace(",", ""))
    except ValueError:
        sub_sqft = 'N/A'

    # parse year
    year_object = soup.find('div', class_='keyDetails-value', string=lambda text: text and 'Built in' in text)

    if year_object:
        year_text = year_object.get_text(strip=True)
        sub_year = int(year_text.split()[-1]) # -1 lets you index the last element
    else:
        sub_year = 'N/A'

    # parse lot
    lot_div = soup.find('div', class_='keyDetails-value', string=lambda text: text and 'lot' in text)

    if lot_div:
        lot_text = lot_div.get_text(strip=True)
        sub_lot = lot_text.split()[0].replace(",", "")
    else:
        lot_div = soup.find('div', class_='keyDetails-value', string=lambda text: text and 'acres' in text)
        if lot_div:
            sub_lot = lot_div.get_text().strip()
        else:
            sub_lot = 'N/A'


    # parse garage
    garage_object = soup.find('div', class_='keyDetails-value', string=lambda text: text and 'garage spaces' in text)

    if garage_object:
        garage_text = garage_object.get_text(strip=True)
        sub_garage = garage_text.split()[0]
        sub_garage = str(sub_garage)
    else:
        sub_garage = 'N/A'

    sub_date_sold = ''
    sub_ppsf = ''
    # sub_condition = ''
    sub_relevance = "subject"

    sub_data = {
        'Address': sub_address,
        'Date Sold': sub_date_sold,
        'Price': sub_price,
        'Bed': sub_bed,
        'Bath': sub_bath,
        'SqFt': sub_sqft,
        'Lot Size': sub_lot,
        '$/SqFt': sub_ppsf,
        'Year': sub_year,
        'Garage': sub_garage,
        'Relevance': sub_relevance
    }
    
    return sub_data

def parse_comps(soup):
    comp_data = []
    homecards = soup.find_all("div", class_="CompHomeCard")
    for card in homecards:
        sub_bed = sub_bath = sub_sqft = comp_lot = "N/A"

        # parse link
        link_tag = card.find("a", href=True)  # Looking for any 'a' tag with a 'href' attribute
        comp_link = 'N/A'
        if link_tag and not link_tag.get('disabled'):
            comp_link = "https://www.redfin.com" + link_tag.get("href", "")
        
        # parse price
        price_tag = card.find("span", class_="homecardV2Price")
        comp_price = int(strip_chars(price_tag.text)) if price_tag else "N/A"

        # parse bed, bath, sqft 
        stats_divs = card.find_all("div", class_="stats")
        for div in stats_divs:
            text = div.text.strip()
            if 'beds' in text and '—' not in text:
                comp_bed = int(strip_chars(text))
            elif 'baths' in text and '—' not in text:
                comp_bath = float(text.replace(' baths', ''))
            elif 'sq ft' in text and '—' not in text:
                comp_sqft = int(strip_chars(text))
    
        # calculate $/sqft
        try:
            comp_ppsf = int(comp_price / comp_sqft)
        except ValueError:
            comp_ppsf = 'N/A'
        
        # parse lot
        home_tag = card.find("div", class_="HomeTags")  # Search within the card
        lot_tag = home_tag.find("span", string=lambda text: re.search(r'\b(smaller|larger)?\s+lot\b', text or '')) if home_tag else None
        comp_lot = lot_tag.text.replace('lot', '').strip() if lot_tag else "N/A"

        # parse date sold
        date = card.select_one('[data-rf-test-id="home-sash"]')
        if date and date.text.strip():
            date_text = date.text.strip().replace('SOLD', '').strip()
            formatted_date = datetime.strptime(date_text, '%b %d, %Y')
            comp_date_sold = formatted_date.strftime('%m/%d/%y')
        else:
            comp_date_sold = "N/A"
        
        # parse year diff
        year_span = home_tag.find("span", string=lambda text: re.search(r'\d+ years (younger|older)', text or ''))
        year_text = year_span.get_text() if year_span else None

        if year_text and 'years' in year_text:
                match = re.search(r'(\d+) years (younger|older)', year_text)
                multiplier = 1 if 'years newer' in year_text else -1 # this allows me to make it positive or negative
                comp_year_diff = multiplier * int(match.group(1))
        else:
            comp_year_diff = "equivalent"

        # parse address
        address_tag = card.find("div", class_="homeAddressV2")
        comp_address = address_tag.text.strip() if address_tag else "N/A"
        
        comp_garage = 'N/A'
        # comp_condition = 'N/A'
        comp_relevance = 'N/A'

        comp = {
            'Address': comp_address,
            'Date Sold': comp_date_sold,
            'Price': comp_price,
            'Bed': comp_bed,
            'Bath': comp_bath,
            'SqFt': comp_sqft,
            'Lot Size': comp_lot,
            '$/SqFt': comp_ppsf,
            'Year': comp_year_diff,
            'Garage': comp_garage,
            'Relevance': comp_relevance
        }

        comp_data.append(comp)

    return comp_data

def analyze(subject_data, comp_data):
    def usd_format(price):
        try:
            return "${:,.0f}".format(price)
        except TypeError:
            return 'N/A'
    
    def trunc_format(price):
        try:
            if price < 1000:
                return f'{price:.0f}' 
            elif price < 1000000:
                return f'{price / 1000:.0f}k' 
            else:
                new_format = f'{price / 1000000:.1f}M'
                if '.0' in new_format:
                    new_format = new_format.replace('.0', '')
                return new_format
        except TypeError:
            return 'N/A'
    
    def order_by_recency(comp_data):
        sorted_comps = sorted(
            comp_data, 
            key=lambda x: datetime.strptime(x['Date Sold'], '%m/%d/%y') if x['Date Sold'] != "N/A" else datetime.min,
            reverse=True
        )
        comp_count = len(sorted_comps)
        
        # if more than 4 comps exist
        if comp_count > 4:
            today = datetime.now().date()
            ninety_days = today - timedelta(days=90)
            limit = comp_count - 4
            temp_comps = []
   
            # Remove all comps over 90 days old, break once you've reached the max
            for comp in reversed(sorted_comps):
                if limit <= 0:
                    temp_comps.append(comp)
                else:
                    if comp['Date Sold'] == "N/A" or datetime.strptime(comp['Date Sold'], '%m/%d/%y').date() > ninety_days:
                        temp_comps.append(comp)
                    else:
                        limit -= 1
                    
            # place back in order of recency 
            sorted_comps = temp_comps[::-1]
            return sorted_comps
    
    def get_avg_price(comps):
        price_sum = 0
        valid_prices = 0

        for comp in comps:
            if isinstance(comp['Price'], int):
                price_sum += comp['Price']
                valid_prices += 1

        if valid_prices > 0:
            avg_price = price_sum / valid_prices
            return trunc_format(avg_price)
        else:
            return 'N/A'
    
    def get_avg_ppsf(comps):
        ppsf_sum = 0
        valid_ppsf = 0

        for comp in comps:
            if isinstance(comp['$/SqFt'], int):
                ppsf_sum += comp['$/SqFt']
                valid_ppsf += 1

        if valid_ppsf > 0:
            avg_ppsf = ppsf_sum / valid_ppsf
            return avg_ppsf
        else:
            return 'N/A'
    
    def get_price_by_zip(comps, subject_data):
        sum = 0
        comp_count = 0
        sub_zip = subject_data['Address'].split(',')[-1]
        for comp in comps:
            comp_zip = comp['Address'].split(',')[-1]
            if comp_zip == sub_zip:
                sum += comp['Price']
                comp_count += 1
        zip_price = int(sum / comp_count)

        return trunc_format(zip_price)
    
    def assign_relevance(comps, subject_data):
        today_dt = datetime.today()
        today = today_dt.strftime('%m/%d/%y')
        for comp in comps:
            comp_score = 0
            similar_comps = 0
            divider = 0
            
            # add comp sqft relevance
            if comp['SqFt'] != 'N/A': 
                if abs(subject_data['SqFt'] - comp['SqFt']) < 100:
                    comp['Relevance'].append('equivalent sqft')
                    comp_score += 3
                elif abs(subject_data['SqFt'] - comp['SqFt']) < 200:
                    comp['Relevance'].append('similar sqft')
                    comp_score += 2

            # add comp bed/bath relevance
            if comp['Bed'] != 'N/A':
                if comp['Bed'] == subject_data['Bed']:
                    if comp['Bath'] == subject_data['Bath']:
                        comp['Relevance'].append('same bed/bath')
                        comp_score += 3
                    elif abs(subject_data['Bath'] - comp['Bath']) <= 1:
                        comp['Relevance'].append('similar bed/bath')
                        comp_score += 2
                elif abs(subject_data['Bed'] - comp['Bed']) <= 1 and abs(subject_data['SqFt'] - comp['SqFt']) < 200:
                    comp_score += 2

            # calculate comp year & add year relevance
            if comp['Year'] == 'equivalent':
                comp['Relevance'].append('equivalent year')
                comp_score += 2
            elif comp['Year'] == 'N/A':
                comp['Year Color'] = "ea9999"
            else: # update comp year & check for relevance
                comp['Year'] = comp['Year'] + subject_data['Year']
                if abs(subject_data['Year'] - comp['Year']) < 5:
                    comp['Relevance'].append('similar year')
                    comp_score += 1
                elif abs(subject_data['Year'] - comp['Year']) > 20:
                    comp_score -= 1
                    comp['Year Color'] = "ea9999"

            # Flag comps sold over 90 days ago 
            if comp['Date Sold'] != 'N/A':
                today_dt = datetime.strptime(today, '%m/%d/%y')
                comp_dt = datetime.strptime(comp['Date Sold'], '%m/%d/%y')
                if today_dt - comp_dt > timedelta(days=90):
                    comp['Date Sold Color'] = 'ea9999'
            else:
                comp['Date Sold Color'] = 'ea9999'

            # add lot relevance
            if comp['Lot Size'] == 'similar':
                comp['Revelance'].append('similar lot size')

            # add comp row color 
            if comp_score > 5:
                if comp_score == 6:
                    comp['Row Color'] = 'b6d7a8'
                if comp_score == 7:
                    comp['Row Color'] = '93c47d'
                if comp_score == 8:
                    comp['Row Color'] = '6aa84f'
                if comp_score == 9:
                    comp['Row Color'] = '38761d' # dark green

            # count the most similar comps to determine avg price based on these
            if comp_score > 7:
                similar_comps += comp['Price']
                divider += 1

            # find the avg price based on the most similar comps
            if divider > 1:
                comps_avg_price = int(similar_comps / divider)
                best_comps_avg_price = trunc_format(comps_avg_price)
            else:
                best_comps_avg_price = 'N/A'

            # format price before returning
            if comp['Price'] != 'N/A':
                comp['Price'] = trunc_format(comp['Price'])

            # combine bed/bath
            if comp['Bed'] != 'N/A' and comp['Bath'] != 'N/A':
                bed = str(comp['Bed'])
                bath = str(comp['Bath']).replace('.0', '')
                comp['Bed/Bath'] = bed + '/' + bath

            # replace address with street name only (TODO ADD REDFIN LINK)
            parts = comp['Address'].split(',')
            comp['Address'] = parts[0].strip()
            
        return comps, best_comps_avg_price
    
    def format_subject_data(subject_data):
        # make subject row light blue
        subject_data['Row Color'] = '9fc5e8'

        # combine bed/bath
        if subject_data['Bed'] != 'N/A' and subject_data['Bath'] != 'N/A':
            bed = str(subject_data['Bed'])
            bath = str(subject_data['Bath']).replace('.0', '')
            subject_data['Bed/Bath'] = bed + '/' + bath

        # truncate address
        subject_data['Address'] = subject_data['Address'].split(',')[0]

        subject_data['Price'] = trunc_format(subject_data['Price'])
        
        return subject_data

    comps = order_by_recency(comp_data)
    # comp_count = len(comps)

    avg_comp_price = get_avg_price(comps)

    avg_comp_ppsf = get_avg_ppsf(comps)
    avg_ppsf_price = int(avg_comp_ppsf * subject_data['SqFt'])
    avg_ppsf_and_price = f'{trunc_format(avg_ppsf_price)} ({usd_format(avg_comp_ppsf)}/sqft)'

    same_zip_comps_price = get_price_by_zip(comps, subject_data)

    # Add Relevance key to comps with empty list value
    for comp in comps:
        comp['Relevance'] = []

    # Add row color key to assign colors based on combined relevance factors (color old dates and N/A dates cells yellow)
    for comp in comps:
        comp['Row Color'] = 'white'
        comp['Year Color'] = ''
        comp['Date Sold Color'] = ''
        comp['Bed/Bath'] = ''

    comps, best_comps_price = assign_relevance(comps, subject_data)

    subject = format_subject_data(subject_data)

    values = [
        ('Subject Value', ''),
        ('By avg price:', f'{avg_comp_price}'),
        ('By avg $/SqFt:', f'{avg_ppsf_and_price}'),
        ('By exact zip:', f'{same_zip_comps_price}'),
        ('By most relevant comps:', f'{best_comps_price}')
    ]

    comp_report = f'{subject['Address']}.tsv'
    comp_report = comp_report.replace(' ', '_')

    headers = ['Address', 'Date Sold', 'Price', 'Bed/Bath', 'SqFt', 'Lot Size', '$/SqFt', 'Year', 'Relevance']

    def filter_keys(data, headers):
        return {key: data[key] for key in data if key in headers}
    
    # create comp table 
    with open(comp_report, 'w', newline='') as file:
        writer = csv.DictWriter(file, delimiter='\t', fieldnames=headers)
        writer.writeheader()
        
        filtered_subject = filter_keys(subject, headers)
        writer.writerow(filtered_subject)
        
        filtered_comps = [filter_keys(comp, headers) for comp in comps]
        writer.writerows(filtered_comps)

    value_report = f'{subject['Address']} value.csv'
    value_report = value_report.replace(' ', '_')

    # create subject value table
    with open(value_report, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(values)

    pdf = PDF()
    pdf.add_page()
    col_widths = [36, 14, 14, 11, 10, 16, 8, 15, 65] 
    headers = ['Address', 'Date Sold', 'Price', 'Bed/Bath', 'SqFt', 'Lot Size', '$/SqFt', 'Year', 'Relevance']
    address = subject['Address']
    report_name = f"{address} Report.pdf"
    property = report_name.replace(' ', '_')
    
    subject = [subject]
    
    pdf.add_table(subject, comps, col_widths, headers)
    
    pdf.ln(10)

    col_widths = [36, 22]

    pdf.add_values(values, col_widths)
    
    pdf.output(f'{property}')

    print('Files Created:')
    print(f'{property}')
    print(f'{comp_report}')
    print(f'{value_report}\n')

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Comparable Property Analysis', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 6)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def add_table(self, subject, comps, col_widths, headers):
        self.set_font('Arial', '', 7)
        # Add header
        self.set_font('Arial', 'B', 6)  # Bold font for header
        for header, width in zip(headers, col_widths):
            self.cell(width, 6, header, border=1, align='C')
        self.ln()

        # Add subject rows
        self.set_font('Arial', '', 7)
        for row in subject:
            for key, width in zip(headers, col_widths):
                self.set_fill_color(164, 194, 244)
                self.cell(width, 6, str(row.get(key, '')), border=1, align='L', fill=True)
            self.ln()

        # Add comp rows
        self.set_font('Arial', '', 7)
        for row in comps:
            for key, width in zip(headers, col_widths):
                self.set_fill_color(255, 255, 255)
                if 'Row Color' in row:
                    rgb_color = hex_to_rgb(row['Row Color'])
                    self.set_fill_color(*rgb_color)
                if key == 'Year' and 'Year Color' in row and row['Year Color']:
                    rgb_color = hex_to_rgb(row['Year Color'])
                    self.set_fill_color(*rgb_color)
                if key == 'Date Sold' in row and row['Date Sold Color']:
                    rgb_color = hex_to_rgb(row['Date Sold Color'])
                    self.set_fill_color(*rgb_color)
                value = row.get(key, '')
                if isinstance(value, list):  
                    value = ', '.join(map(str, value))
                
                self.cell(width, 6, str(value), border=1, align='L', fill=True)
            self.ln()

    def add_values(self, values, col_widths):
        for row in values:
            if 'Subject Value' in row:
                self.set_font('Arial', 'B', 7)
            else:
                self.set_font('Arial', '', 7)

            for value, width in zip(row, col_widths):
                self.cell(width, 5, str(value), border=1, align='L')
            self.ln()
            
def main():
    subject_property = input(f"\nREfind primarily supports single family homes in the US. Multi-family support is in progress.\n\nEnter complete address (address, city, state zip):\n\n")
    
    if not validate_address(subject_property):
        print('Invalid address format. Example: 4664 Encino Ave, Encino, CA 91316')
        return
    
    print('\ngenerating report...\n')
    start_time = time.time()

    scraped_data = scrape_redfin(subject_property)

    subject_data = parse_subject(scraped_data)
    comp_data = parse_comps(scraped_data)
    analyze(subject_data, comp_data)

    runtime = time.time() - start_time
    print(f"Run time: {runtime:.2f} seconds\n")


if __name__ == "__main__":
    main()
