# Created by  Chris Brundige & Jerry Cooper

# This script is designed to scrape data from a website and upload it to a
# Socrata data portal. The script uses Selenium to scrape the data from the
# website and then uses the requests library to upload the data to the portal.
import requests
import json
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
import pandas as pd
from dotenv import load_dotenv
import os

# load environment variables
load_dotenv()

token = os.getenv("TOKEN")
secret = os.getenv("SECRET")
url = os.getenv("URL")

# URL TO SCRAPE
scraped_site_url = "http://www.hamiltoncountyherald.com/PublicNotices.aspx"


def scrapeData(url):
    # Set Chrome Browser Options
    options = ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # Initialize Driver
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # Initialize list to hold dictionaries produced by view_links function
    final_data = []

    def date_links():
        # Initialize list to hold values to append to hyperlinks in left-hand date section
        web_links = [2, 3, 4, 5]

        try:

            # Initialize counter variable to terminate loop
            counter = 0

            # Loop to start process of walking date links on left side of page
            while counter <= 1000:
                for link in web_links:
                    date_links = driver.find_elements("xpath",
                                                      '/html/body/form/div[3]/table/tbody/tr[3]/td/div/table/tbody/tr/td[2]/div/table/tbody/tr/td[1]/a[' + str(
                                                          link) + ']')

                    # Once correct link is located, click it and execute view_links function call
                    for dates in date_links:
                        dates.click()
                        view_links()

                    # Increment counter by one for every turn of week loop
                    # This is mostly here to prevent run away while loop which
                    # does happen if site has error
                    counter += 1



        # Catch keyboard interrupt commands or manual stops
        except KeyboardInterrupt:

            print("\nLooks like someone executed a Keyboard Interrupt.\n")

        # Catch all other errors and report them to the user
        except Exception as e:

            return f"\nSomething happened, but it doesnt appear to be related to the website (site didnt crash)\n The actual error was: {e}"

    def view_links():
        # Use driver to dig down to the correct table
        driver.implicitly_wait(5)  # this forces the driver to wait until data loaded
        tables = driver.find_elements(By.TAG_NAME, 'table')[0]
        foreclosure_table = tables.find_elements(By.TAG_NAME, 'table')[7]
        views = foreclosure_table.find_elements(By.TAG_NAME, 'tr')[1:]

        # loop through each of the 'View' links
        for view in views:
            # Store the current window handle
            win_handle_before = driver.current_window_handle

            # Perform the click operation that opens new window
            view.find_element(By.TAG_NAME, 'a').click()

            # Removed the call to sleep since it didnt seem to be necessary.
            # The driver already uses the implicit wait function so that should
            # be enough. Leaving code here in case needed later.
            # time.sleep(.5)

            # Switch to new window opened
            for win_handle in driver.window_handles:
                driver.switch_to.window(win_handle)

            # Perform the actions on new window
            final_data.append(scrape_data_from_site())

            # Close the new window, if that window not required
            driver.close()

            # Switch back to original browser (first window)
            driver.switch_to.window(win_handle_before)
            # time.sleep(.5)

    def scrape_data_from_site():
        # Create list of labels of data you want to scrape
        labels = ["lbl1", "lbl2", "lbl3", "lbl4", "lbl5", "lbl6", "lbl7", "lbl8", "lbl9", "lbl10", "lbl11"]

        # Empty list to append data values to
        list_of_data = []

        # Create loop to iterate through list and print values of labels
        for items in labels:
            link = driver.find_element("id", items)
            link_label = link.text
            list_of_data.append(link_label)

        # Create list of titles to use as dict keys
        titles = ["Borrower", "Address", "city_state_zip", "Original Trustee", "Attorney", "Instrumental No.",
                  "Substitute Trustee",
                  "Advertised Auction Date", "Date of First Public Notice", "Trust Date", "DR No."]

        # Zip the titles and labels data together into one dict
        zipped_data = dict(zip(titles, list_of_data))

        return zipped_data

    date_links()

    # Use pandas to create a dataframe from the returned data
    df = pd.DataFrame(final_data)
    # export to csv
    df.to_csv("data.csv")
    # remove duplicates
    df.drop_duplicates(subset="DR No.", inplace=True)
    # export to json
    df.to_json("data.json")

    return final_data


def post_request(url, data):
    r = requests.post(url, auth=(f"{token}", f"{secret}"), json=data)
    return r.status_code


# upload data to chattadata
def uploadData(data):
    try:
        post_request(url, data)
    except Exception as e:
        print(e)
        print("Error uploading data to chattadata")


if __name__ == "__main__":
    # scrape data from URL and store in data variable
    data = scrapeData(scraped_site_url)
    # upload data to chattadata
    uploadData(data)
