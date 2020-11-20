from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from twilio.rest import Client

## environment variables -- hide from share
account_sid = ""
auth_token = ""
my_number = ""
purchased_number = ""
full_allergy_report_url = ""

## scrape
def simple_get(url):
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None

## handle response
def is_good_response(resp):
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)

## handle error
def log_error(e):
    print(e)

## scrape for Allergy report
raw_html = simple_get(full_allergy_report_url)
html = BeautifulSoup(raw_html, 'html.parser')


## parse html response
def parse_allergens(html):
    allergens = {'Tree':{}, 'Grass':{}, 'Ragweed':{}}
    allergens_count = 0
    for i in range(9):
        day_level = html.select('li')[i].text.split(": ")
        if day_level[1] == "None":
                allergens_count += 1
        if i > 5:
            allergens['Ragweed'][day_level[0]] = day_level[1]
        elif i < 3:
            allergens['Tree'][day_level[0]] = day_level[1]
        else:
            allergens['Grass'][day_level[0]] = day_level[1]
    return allergens, allergens_count

parsed_allergens = parse_allergens(html)
allergens = parsed_allergens[0]
allergens_count = parsed_allergens[1]

## send SMS via Twilio
def send_twilio_message(allergens, allergens_count, phone_number):
    client = Client(account_sid, auth_token)
    msgbody = ""
    forecast = ["The pollen is here! HIDE! TAKE YOUR MEDICINE! Forecast:"]
    if allergens_count == 9:
        msgbody = "There are no current allergens, no sniffles for you!"
    else:
        for allergen in allergens:
            for key in allergens[allergen]:
                if allergens[allergen][key] != "None":
                   forecast_string = allergen + " " + key + ": " + allergens[allergen][key]
                   forecast.append(forecast_string)
        msgbody = " ".join(forecast)
    client.api.account.messages.create(
        to = phone_number,
        from_ = purchased_number,
        body = msgbody
        )

## Text Trish
send_twilio_message(allergens, allergens_count, my_number)