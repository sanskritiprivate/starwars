from flask import Flask, render_template
import re
import requests


app = Flask(__name__, template_folder='templates')

# this initial part only runs once when the app is started
# this part initializes some variables that are used when requests are made
characters_endpoint = "https://swapi.dev/api/people/?page={}"
character_search_endpoint = "https://swapi.dev/api/people/?search={}"


all_characters = []

# gets all characters from each page of the swapi /people endpoint
for i in range(1,10):
    all_characters = all_characters + requests.get(characters_endpoint.format(i)).json()["results"]


# character_index_dictionary links the start index of each character name in character_string
# with the character's name. This is helper dictionary also used for substring look up
character_list = []
character_index_dictionary = {}
start_index = 0

for character in all_characters:
    name = character["name"]
    character_list.append(name)

    character_index_dictionary[str(start_index)] = name
    start_index = start_index + len(name) + 1

# character_string is a string concatenation of all characters in the swapi
# I use it to look for substrings when the query doesn't match any character name exactly
character_string = " ".join(character_list)


# initial search page
@app.route("/")
def hello_world():
    return render_template("base.html")


# initial search page redirects to this page
# uses user input query for character name look up
# if no character is found, calls the substring lookup function
# calls starship, homeworld, and species lookup functions for each character
@app.route("/search-character/<query>")
def search_character(query):
    return_json = []
    character_search_results = requests.get(character_search_endpoint.format(query)).json()["results"]

    if len(character_search_results) < 1:
        character_search_results = substring_search(query)

    for character in character_search_results:
        starships = character["starships"]
        homeworld = character["homeworld"]
        species = character["species"]

        return_json.append({"character_name": character["name"],
                            "attributes": {"starships": get_starships(starships),
                                           "homeworld": get_homeworld(homeworld),
                                           "species": get_species(species)}})

    if len(return_json) < 1:
        return render_template("oops.html")
    sorted_json = sort_alphabetically(return_json)
    return render_template("search_characters.html", characters=sorted_json)


# gets and formats starships data from swapi
def get_starships(starships):
    return_json = []
    for starship in starships:
        starship_result = requests.get(starship).json()
        starship_info = {"name": starship_result["name"],
                         "capacity": starship_result["cargo_capacity"],
                         "class": starship_result["starship_class"]}
        return_json.append(starship_info)
    return return_json


# gets and formats homeworld data from swapi
def get_homeworld(homeworld):
    homeworld_response = requests.get(homeworld).json()
    return {"name": homeworld_response["name"],
            "population": homeworld_response["population"],
            "climate": homeworld_response["climate"]}


# gets and formats species data from swapi
def get_species(species):
    return_json = []
    for each_species in species:
        species_result = requests.get(each_species).json()
        species_info = {"name": species_result["name"],
                         "language": species_result["language"],
                         "lifespan": species_result["average_lifespan"]}
        return_json.append(species_info)
    return return_json


# this function does substring lookup in the character_string using python regex
# if found, we find the start index based on the substring match index, find character's name
# from character_index_dictionary and return character search response from swapi
def substring_search(query):
    character_names = set()
    return_json = []

    for match in re.finditer(query, character_string, flags=re.IGNORECASE):
        if character_index_dictionary[str(match.start())]:
            character_names.add(character_index_dictionary[str(match.start())])
        else:
            counter = 1
            found = False
            while not found:
                if character_index_dictionary[str(match.start() - counter)]:
                    character_names.add(character_index_dictionary[str(match.start()-counter)])
                    found = True
                counter = counter - 1

    for name in character_names:
        character_response = requests.get("https://swapi.dev/api/people/?search={}".format(name)).json()["results"]
        return_json.append(character_response)
    return return_json


# sorts the return value alphabetically
# before sending it to the templates
def sort_alphabetically(data):
    character_name_list = []
    temp_dict = {}
    final_sorted_json = []

    for element in data:
        character_name_list.append(element["character_name"])
        temp_dict[str(element["character_name"])] = element
    character_name_list.sort()

    for name in character_name_list:
        final_sorted_json.append(temp_dict[name])
    return final_sorted_json


if __name__ == "__main__":
    app.run()
