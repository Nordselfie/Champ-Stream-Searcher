from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import Main as MainC


link = input("Insert Link to scrap: ").strip()

# link = "https://www.deeplol.gg/pro/Doublelift"

# Setup WebDriver
options = Options()
driver = webdriver.Chrome(options=options)
driver.get(link)
driver.implicitly_wait(5)

accounts = []

# Get all summoner links
account_elements = driver.find_elements(By.XPATH, '//a[contains(@href, "/summoner/") and contains(., "#")]')

for element in account_elements:
    try:
        # Get all span elements inside this summoner block
        spans = element.find_elements(By.TAG_NAME, 'span')
        
        # Heuristic: Region = 1st span, Name = 2nd, Tag = 3rd
        if len(spans) >= 3:
            region = spans[0].text.strip()
            name = spans[1].text.strip()
            tag = spans[2].text.strip()
            
            gamename, tagline = name.split("#")
            gamename = gamename.strip()
            tagline = tagline.strip()
            
            streamername = link.split("/")[-1]
            
            
            fixedregion = MainC.fix_region(region)
            MainC.add_streamer_mapping(streamername, name, fixedregion)
            
            accounts.append({
                'name': gamename,
                'tag': tag,
                'region': region
            })
            
    except Exception as e:
        print(f"Error parsing account block: {e}")

# Output
for acc in accounts:
    print(f"Name: {acc['name']}, Tag: {acc['tag']}, Region: {acc['region']}")

driver.quit()
