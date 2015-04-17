import json
from urllib2 import (Request, urlopen)

RESULT_COUNT = 3
CODE_LIST_FILE = 'code_list.txt'
QPX_ENDPOINT = 'https://www.googleapis.com/qpxExpress/v1/trips/search?key=AIzaSyDUl8LR3B0b6_TODUTO62xRvC7BLZZ_o0c'
USD_PREFIX = 'USD'

def get_connections(origin, destination, departureDate, arrivalDate):

    with open(CODE_LIST_FILE, 'r') as code_file:
        codes = code_file.readlines()

    direct_early = format_request(origin, destination, departureDate, 1)
    direct_late = format_request(origin, destination, arrivalDate, 1)

    stopover_options = []

    for code in codes:
        first_leg_request = format_request(origin, code, departureDate, 0)
        second_leg_request = format_request(code, destination, arrivalDate, 0)
        first_leg_response = format_response(post_request(first_leg_request))
        second_leg_response = format_response(post_request(second_leg_request))
        best_combo = get_best_combinations(first_leg_response, second_leg_response)
        for combination in best_combo:
            obj = {'saleTotal': '%s%0.2f' % (USD_PREFIX, get_total_price(combination))}
            obj['slice'] = []
            for leg in combination:
                obj['slice'].extend(leg['slice'])
            stopover_options.append(obj)
    stopover_options.sort(key=lambda x: get_price_number(x['saleTotal']))

    direct_options = format_response(post_request(direct_early))['response']['options']
    direct_options.extend(format_response(post_request(direct_late))['response']['options'])
    direct_options.sort(key=lambda x: get_price_number(x['saleTotal']))
    response = {'response': {'stopoverOptions': stopover_options[0:RESULT_COUNT], 'directOptions': direct_options[0:RESULT_COUNT]}}
    response['request'] = {'origin': origin, 'destination': destination, 'departureDate': departureDate, 'arrivalDate': arrivalDate}
    return response


def format_request(origin, destination, date, max_stops):
    return json.dumps({ 'request': { 'passengers': {'adultCount': 1}, 'slice': [ { 'origin': origin, 'destination': destination, 'date': date } ], 'solutions': RESULT_COUNT, 'maxStops': max_stops } })


def post_request(json_request):
    headers = {'Content-Type': 'application/json'}
    search_request = Request(QPX_ENDPOINT, json_request, headers)
    return json.loads(urlopen(search_request).read())


def format_response(raw_response):

    response_data = {'response': {'options': []}}

    trip_options = raw_response['trips']['tripOption']
    cities = raw_response['trips']['data']['city']
    airports = raw_response['trips']['data']['airport']

    code_city_map = {}
    for city in cities:
        code_city_map[city['code']] = city['name']

    airport_city_map = {}
    for airport in airports:
        airport_city_map[airport['code']] = code_city_map[airport['city']]

    for trip in trip_options:
        option_data = {'saleTotal': trip['saleTotal'], 'slice': []}

        for sl in trip['slice']:
            for leg in sl['segment']:
                leg_obj = leg['leg'][0]
                leg_data = {}
                leg_data['origin'] = leg_obj['origin']
                leg_data['originName'] = airport_city_map[leg_obj['origin']]
                leg_data['departureTime'] = leg_obj['departureTime']
                leg_data['destination'] = leg_obj['destination']
                leg_data['destinationName'] = airport_city_map[leg_obj['destination']]
                leg_data['arrivalTime'] = leg_obj['arrivalTime']
                option_data['slice'].append(leg_data)

        response_data['response']['options'].append(option_data)

    return response_data


def combine_results(combined_arrays, all_arrays, start_index, output):

    if start_index < len(all_arrays):
        new_arrays = []
        for combined_array in combined_arrays:
            for item in all_arrays[start_index]:
                new_array = [i for i in combined_array]
                new_array.append(item)
                new_arrays.append(new_array)
        output[0] = new_arrays
        combine_results(new_arrays, all_arrays, start_index + 1, output)


def get_best_combinations(first_leg, second_leg):
    output = [[]]
    combine_results([[]], [first_leg['response']['options'], second_leg['response']['options']], 0, output)
    combos = output[0]
    combos.sort(key=lambda x: get_total_price(x))
    return combos[0:RESULT_COUNT]


def get_total_price(legs):
    total = 0
    for leg in legs:
        total += get_price_number(leg['saleTotal'])
    return total

def get_price_number(price):
    return float(price[3:])
