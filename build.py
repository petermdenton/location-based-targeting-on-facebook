# Usage:
# mkvirtualenv demo_fb_location_targeting -p python3
# workon demo_fb_location_targeting # use this when you work on the project in a new Terminal window
# pip install -r requirements.txt
#
# Variables:
#.env file stories Google Maps, Google Sheets ID, Clearbit API Token, Facebook Access Token, Facebook Campaign ID

import sys, time, os, json, datetime
from random import randint

import requests
from sys import argv
from requests.auth import HTTPBasicAuth

# settings.py
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), verbose=True)

def query_google_maps(address):

  url = "https://maps.googleapis.com/maps/api/place/textsearch/json?query=" + address + "&key=" + os.getenv('GOOGLE_MAPS_API_KEY')
  print(url)
  response = requests.get(url)
  if response.status_code == 200:
    data = json.loads(response.text)
    return data
    log (f'Status code: {response.status_code}')


def build_fb_schema(name,formatted_address_lat,formatted_address_lng,location_interests):

  #These variables define the exclusion radius. Play with these to adjust how close or far you want to be from the building itself.

  north_lat = formatted_address_lat + 0.0095
  north_lng = formatted_address_lng
  east_lat  = formatted_address_lat
  east_lng  = formatted_address_lng + 0.0145
  south_lat = formatted_address_lat - 0.0095
  south_lng = formatted_address_lng
  west_lat  = formatted_address_lat
  west_lng  = formatted_address_lng -0.0145

  post_to_facebook(name,formatted_address_lat,formatted_address_lng,north_lat,north_lng,east_lat,east_lng,south_lat,south_lng,west_lat,west_lng,location_interests)

def build_geo_from_domain_via_clearbit(domain):

  # This function simply takes a web address and finds the physical location of the company via Clearbit.

  url = 'https://company.clearbit.com/v2/companies/find'
  params = {
      'domain':domain
  }
  auth = os.getenv('CLEARBIT_ACCESS_TOKEN')
  response = requests.get(url=url, params=params, auth=HTTPBasicAuth(auth, ''))
  if response.status_code == 200:
    data = response.json()
    return data

def build_fb_interests(location_interests):

  # This function queries the Facebook Marketing API to get a list of interests based on a keyword.

  url = 'https://graph.facebook.com/v2.11/search'
  params = {
      'type':'adinterest',
      'q':location_interests,
      'access_token': os.getenv('FACEBOOK_ACCESS_TOKEN'),
  }
  response = requests.get(url=url, params=params)
  if response.status_code == 200:
    data = response.json()
    return data

def build_array_of_interests(location_interests):

  interests_array = ''
  interests = build_fb_interests(location_interests)
  field_list = interests['data']
  for fields in field_list:
    interests_array += "{'id':"+fields['id']+",'name':'"+fields['name']+"'},"

  return interests_array

def post_to_facebook(name,formatted_address_lat,formatted_address_lng,north_lat,north_lng,east_lat,east_lng,south_lat,south_lng,west_lat,west_lng,location_interests):

  interest_array = build_array_of_interests(location_interests)

  url = 'https://graph.facebook.com/v3.1/act_'+os.getenv('FACEBOOK_AD_ACCOUNT')+'/adsets'

  params = {
      'name':name,
      'optimization_goal':'LINK_CLICKS',
      'billing_event':'IMPRESSIONS',
      'daily_budget':'1000',
      'bid_strategy':'LOWEST_COST_WITHOUT_CAP',
      'status':'ACTIVE',
      'campaign_id':os.getenv('FACEBOOK_CAMPAIGN_ID'),
      'targeting': json.dumps({
        "excluded_geo_locations": {
          "custom_locations": [
          {
            "latitude": north_lat,
            "longitude": north_lng,
            "radius": "1",
            "distance_unit": "kilometer"
          },
          {
            "latitude": east_lat,
            "longitude": east_lng,
            "radius": "1",
            "distance_unit": "kilometer"
          },
          {
            "latitude": south_lat,
            "longitude": south_lng,
            "radius": "1",
            "distance_unit": "kilometer"
          },
          {
            "latitude": west_lat,
            "longitude": west_lng,
            "radius": "1",
            "distance_unit": "kilometer"
          }
          ],
        },
        "geo_locations": {
          "custom_locations":
          [
          {
            "latitude": formatted_address_lat,
            "longitude": formatted_address_lng,
            "radius": "1",
            "distance_unit": "kilometer"
          }],
          "location_types": ["recent"]
        },
        'interests': '['+interest_array+']',
      }, indent=None),
      'access_token': os.getenv('FACEBOOK_ACCESS_TOKEN')
  }
  resp = requests.post(url=url, data=params)
  print(resp)
  data = resp.json()

def load_urls():
  f = open('urls.txt', 'r')
  roles = f.readlines()
  roles = [role.strip() for role in roles]
  return list(roles)

def process_urls():

  #Get the list of the URLs you want to build locations for
  company_urls = load_urls()

  for u_url in company_urls:
    u_interests = os.getenv('FB_INTERESTS')
    clear_bit_response = build_geo_from_domain_via_clearbit(u_url)
    location_address = clear_bit_response['location']
    location_name = clear_bit_response['name']
    formatted_address_lat = clear_bit_response['geo']['lat']
    formatted_address_lng = clear_bit_response['geo']['lng']
    build_fb_schema(location_name,formatted_address_lat,formatted_address_lng,u_interests)

#Start
process_urls()

