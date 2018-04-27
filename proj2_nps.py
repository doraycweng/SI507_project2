## proj_nps.py
## Skeleton for Project 2, Winter 2018
## ~~~ modify this file, but don't rename it ~~~

import requests
import json
from bs4 import BeautifulSoup
import secrets
import plotly.plotly as py


CACHE_FNAME_np = 'cache_np.json'
try:
    cache_file_np = open(CACHE_FNAME_np, 'r')
    cache_contents_np = cache_file_np.read()
    CACHE_DICTION_np = json.loads(cache_contents_np)
    cache_file_np.close()

except:
    CACHE_DICTION_np = {}


def make_request_using_cache_np(url):    

    if url in CACHE_DICTION_np:
        return CACHE_DICTION_np[url]

    else:
        resp = requests.get(url)
        CACHE_DICTION_np[url] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION_np)
        fw = open(CACHE_FNAME_np,"w")
        fw.write(dumped_json_cache)
        fw.close() 
        return CACHE_DICTION_np[url]


CACHE_FNAME_API = 'cache_API.json'
try:
    cache_file_API = open(CACHE_FNAME_API, 'r')
    cache_contents_API = cache_file_API.read()
    CACHE_DICTION_API = json.loads(cache_contents_API)
    cache_file_API.close()

except:
    CACHE_DICTION_API = {}


def params_unique_combination(baseurl, params):
    alphabetized_keys = sorted(params.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, params[k]))
    return baseurl + "_".join(res)

def make_request_using_cache_google_API(baseurl, params):
    unique_ident = params_unique_combination(baseurl,params)

    if unique_ident in CACHE_DICTION_API:
        print("Getting cached data...")
        return CACHE_DICTION_API[unique_ident]
    else:
        print("Making a request for new data...")
        resp = requests.get(baseurl, params=params)
        CACHE_DICTION_API[unique_ident] = json.loads(resp.text)
        dumped_json_cache = json.dumps(CACHE_DICTION_API)
        fw = open(CACHE_FNAME_API,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return CACHE_DICTION_API[unique_ident]


## you can, and should add to and modify this class any way you see fit
## you can add attributes and modify the __init__ parameters,
##   as long as tests still pass
##
## the starter code is here just to make the tests run (and fail)
class NationalSite():
    def __init__(self, type, name, desc, url=None):
        self.type = type
        self.name = name
        self.description = desc
        self.url = url

        # needs to be changed, obvi.
        self.address_street = ''
        self.address_city = ''
        self.address_state = ''
        self.address_zip = ''

    def __str__(self):
    	return '{} ({}): {}, {}, {} {}'.format(self.name, self.type, self.address_street, self.address_city, self.address_state, self.address_zip)

## you can, and should add to and modify this class any way you see fit
## you can add attributes and modify the __init__ parameters,
##   as long as tests still pass
##
## the starter code is here just to make the tests run (and fail)
class NearbyPlace():
    def __init__(self, name, lat, lon):
        self.name = name
        self.lat = lat
        self.lon = lon

    def __str__(self):
    	return self.name 

## Must return the list of NationalSites for the specified state
## param: the 2-letter state abbreviation, lowercase
##        (OK to make it work for uppercase too)
## returns: all of the NationalSites
##        (e.g., National Parks, National Heritage Sites, etc.) that are listed
##        for the state at nps.gov
def get_sites_for_state(state_abbr):
    site_list = []
    baseurl = "https://www.nps.gov/"
    state_url = baseurl + state_abbr
    page_text = make_request_using_cache_np(state_url)
    page_soup = BeautifulSoup(page_text, 'html.parser')
    list_parks = page_soup.find(id = 'list_parks')
    if list_parks != None:
        all_site = list_parks.find_all('li', class_='clearfix')
        for site in all_site:
            site_type = site.find('h2').text
            name = site.find('h3').text
            des = site.find('p').text
            detail_url = baseurl + site.find('h3').find('a')['href']
            detail_text = make_request_using_cache_np(detail_url)
            detail_soup = BeautifulSoup(detail_text, 'html.parser')
            address = detail_soup.find(id='ParkFooter').find(class_='mailing-address')
            if address != None:
                street_item = address.find(itemprop='streetAddress')
                if street_item != None:
                    street = street_item.text
                city_item = address.find(itemprop='addressLocality')
                if city_item != None:
                    city = city_item.text
                state_item = address.find(itemprop='addressRegion')
                if state_item != None:
                    state = state_item.text
                zip_num_item = address.find(itemprop='postalCode')
                if zip_num_item != None:
                    zip_num = zip_num_item.text
                site = NationalSite(site_type, name, des, detail_url)
                site.address_street = street.strip()
                site.address_city = city.strip()
                site.address_state = state.strip()
                site.address_zip = zip_num.strip()
                site_list.append(site)

    return site_list


def get_geo_for_site(national_site):
    baseurl_1 = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
    params_1 = {"query": national_site.name + " " + national_site.type , "key" : secrets.google_places_key}
    results = make_request_using_cache_google_API(baseurl_1, params_1)["results"]
    if len(results) > 0:
        if len(results) == 1:
            site_lat = results[0]["geometry"]["location"]["lat"]
            site_lng = results[0]["geometry"]["location"]["lng"]
        elif len(results) > 1:
            i = 0 
            for site in results:
                if site["name"].lower() == national_site.name.lower() + " " + national_site.type.lower():
                    break
                else:
                    i+=1 
            if i < len(results):
                site_lat = results[i]["geometry"]["location"]["lat"]
                site_lng = results[i]["geometry"]["location"]["lng"]
        return (site_lat, site_lng)
    else: 
        return None

## Must return the list of NearbyPlaces for the specifite NationalSite
## param: a NationalSite object
## returns: a list of NearbyPlaces within 10km of the given site
##          if the site is not found by a Google Places search, this should
##          return an empty list
def get_nearby_places_for_site(national_site):
    nearby_places = []
    geoinfo = get_geo_for_site(national_site)
    if geoinfo != None: 
        site_lat = geoinfo[0]
        site_lng = geoinfo[1]
        baseurl_2 = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?'
        params_2 = {"location": str(site_lat) + "," + str(site_lng) , "radius": 10000 , "key": secrets.google_places_key}
        results_nearby = make_request_using_cache_google_API(baseurl_2, params_2)["results"]
        for result in results_nearby:
            place = NearbyPlace(result["name"], result["geometry"]["location"]["lat"], result["geometry"]["location"]["lng"] )
            nearby_places.append(place)

    return nearby_places


## Must plot all of the NationalSites listed for the state on nps.gov
## Note that some NationalSites might actually be located outside the state.
## If any NationalSites are not found by the Google Places API they should
##  be ignored.
## param: the 2-letter state abbreviation
## returns: nothing
## side effects: launches a plotly page in the web browser
def plot_sites_for_state(state_abbr):
    site_geo = []
    lat = []
    lon = []
    text = []
    site_list = get_sites_for_state(state_abbr)
    for site in site_list:
        geoinfo = get_geo_for_site(site)
        if geoinfo != None:
            if geoinfo[0] != None and geoinfo[1] != None:
                site_geo.append(geoinfo)
                text.append(site.name)

    for geo in site_geo:
        lat.append(geo[0])
        lon.append(geo[1])

    data = [ dict(
        type = 'scattergeo',
        locationmode = 'USA-states',
        lon = lon,
        lat = lat,
        text = text,
        mode = 'markers',
        marker = dict(
            size = 10,
            symbol = 'star',
        ))]

    min_lat = 10000
    max_lat = -10000
    min_lon = 10000
    max_lon = -10000

    for str_v in lat:
        v = float(str_v)
        if v < min_lat:
            min_lat = v
        if v > max_lat:
            max_lat = v
    for str_v in lon:
        v = float(str_v)
        if v < min_lon:
            min_lon = v
        if v > max_lon:
            max_lon = v

    center_lat = (max_lat+min_lat) / 2
    center_lon = (max_lon+min_lon) / 2

    max_range = max(abs(max_lat - min_lat), abs(max_lon - min_lon))
    padding = max_range * .10
    lat_axis = [min_lat - padding, max_lat + padding]
    lon_axis = [min_lon - padding, max_lon + padding]

    layout = dict(
            title = 'National sites in ' +  state_abbr.upper() + '<br>(Hover for site names)',
            geo = dict(
            scope='usa',
            projection=dict( type='albers usa' ),
            showland = True,
            landcolor = "rgb(250, 250, 250)",
            subunitcolor = "rgb(100, 217, 217)",
            countrycolor = "rgb(217, 100, 217)",
            lataxis = {'range': lat_axis},
            lonaxis = {'range': lon_axis},
            center= {'lat': center_lat, 'lon': center_lon },
            countrywidth = 3,
            subunitwidth = 3
            ),
        )

    fig = dict(data=data, layout=layout )
    py.plot( fig, validate=False, filename='National sites')


## Must plot up to 20 of the NearbyPlaces found using the Google Places API
## param: the NationalSite around which to search
## returns: nothing
## side effects: launches a plotly page in the web browser
def plot_nearby_for_site(site_object):
    site_lat = []
    site_lon = []
    site_text = []
    nearby_geo = []
    nearby_lat = []
    nearby_lon = []
    nearby_text = []

    geoinfo = get_geo_for_site(site_object)
    if geoinfo != None:
        if geoinfo[0] != None and geoinfo[1] != None:
                site_lat.append(geoinfo[0])
                site_lon.append(geoinfo[1])
                site_text.append(site_object.name)

    nearby_list = get_nearby_places_for_site(site_object)
    for nearby in nearby_list:
        if nearby.lat != None and nearby.lon != None:
            nearby_lat.append(nearby.lat)
            nearby_lon.append(nearby.lon)
            nearby_text.append(nearby.name)

    trace1 = dict(
        type = 'scattergeo',
        locationmode = 'USA-states',
        lon = site_lon,
        lat = site_lat,
        text = site_text,
        mode = 'markers',
        marker = dict(
            size = 20,
            symbol = 'star',
            color = 'red'
        ))
    trace2 = dict(
        type = 'scattergeo',
        locationmode = 'USA-states',
        lon = nearby_lon,
        lat = nearby_lat,
        text = nearby_text,
        mode = 'markers',
        marker = dict(
            size = 8,
            symbol = 'circle',
            color = 'blue'
        ))

    data = [trace1, trace2]


    min_lat = 10000
    max_lat = -10000
    min_lon = 10000
    max_lon = -10000

    lat_vals = site_lat + nearby_lat
    lon_vals = site_lon + nearby_lon
    for str_v in lat_vals:
        v = float(str_v)
        if v < min_lat:
            min_lat = v
        if v > max_lat:
            max_lat = v
    for str_v in lon_vals:
        v = float(str_v)
        if v < min_lon:
            min_lon = v
        if v > max_lon:
            max_lon = v

    center_lat = (max_lat+min_lat) / 2
    center_lon = (max_lon+min_lon) / 2

    max_range = max(abs(max_lat - min_lat), abs(max_lon - min_lon))
    padding = max_range * .10
    lat_axis = [min_lat - padding, max_lat + padding]
    lon_axis = [min_lon - padding, max_lon + padding]

    layout = dict(
            title = 'Nearby places for ' + site_object.name + '<br>(Hover for airport names)',
            geo = dict(
                scope='usa',
                projection=dict( type='albers usa' ),
                showland = True,
                landcolor = "rgb(250, 250, 250)",
                subunitcolor = "rgb(100, 217, 217)",
                countrycolor = "rgb(217, 100, 217)",
                lataxis = {'range': lat_axis},
                lonaxis = {'range': lon_axis},
                center = {'lat': center_lat, 'lon': center_lon },
                countrywidth = 3,
                subunitwidth = 3
                ),
            )


    fig = dict(data=data, layout=layout )
    py.plot( fig, validate=False, filename='nearby places' )
    

if __name__ == "__main__":
    site_list = []
    nearby_list = []
    result_site = {}
    index = 1 
    cmd_help = """
            list <stateabbr>
                available anytime
                lists all National Sites in a state
                valid inputs: a two-letter state abbreviation
            nearby <result_number>
                available only if there is an active result set
                lists all Places nearby a given result
                valid inputs: an integer 1-len(result_set_size)
            map
                available only if there is an active result set
                displays the current results on a map
            exit
                exits the program
            help
                lists available commands (these instructions)"""
           
    while(True): 
        answer = input('Enter command(or "help" for options):')
        words = answer.split()
        if len(words) > 0:
            cmd = words[0]
            if len(words) == 1 and cmd == "help":
                print(cmd_help)
            elif len(words) == 1 and cmd == "exit":
                print("Bye!")
                break
            elif len(words) == 2 and cmd == "list":
                stateabbr = str(words[1])
                site_list = get_sites_for_state(stateabbr)
                print("National Sites in " + stateabbr + "\n")
                for site in site_list:
                    print(str(index) + " " + str(site))
                    result_site[index] = site
                    index += 1
            elif len(words) == 2 and cmd == "nearby" and len(site_list) != 0:
                num = int(words[1])
                if num < len(site_list):
                    nearby_list = get_nearby_places_for_site(result_site[num])
                    print("Places near " + result_site[num].name + result_site[num].type + "\n")
                    for index, place in enumerate(nearby_list, 1):
                        print(index, place)
                else:
                    print("The index exceeds the range.")
            elif len(words) == 1 and cmd == "map":
                if len(nearby_list) != 0:
                    plot_nearby_for_site(result_site[num])
                elif len(site_list) != 0:
                    plot_sites_for_state(stateabbr)










