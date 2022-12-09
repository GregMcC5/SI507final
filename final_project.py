import requests
import json
import csv
import hashlib
import plotly.graph_objects as go
from fuzzywuzzy import fuzz

##################
# Welcome to my final project script.
#
# My script constructs a tree data structure that takes an address from the user and pulls information
# on the elected officeholders that represent somone at that address at various levels of government, 
# from the Google Civics API and the Open Secrets API. The constructed tree is a RepTree class object, with 
# information on the user's a) federal officeholders, b) state office holders, c) local/county officeholder, and
# d) information on the other members of the US Congress from the user's state.
#
# This tree holds bibliographic information on the officeholders, but also financial information from Open Secrets on1
# members of Congress. Speifically it has info on what industries and individuals/companies financially supported
# that member of Congress the most during the most recen election cycle in which iformation is available.
#
# Please note that this script construct a new tree for each passed address, so the exact size and content of the 
# tree will vary by user. Much content of the Google Civics data is cached on the basis of the address, so new
# addresses may take several moments to construct. For testing purposes you may user the address of the 
# University of Michigan, for which the data is cached:
#
# 500 S State St, Ann Arbor, MI 48109
#
# If entering a new address, this script may take a few moments to perform all the necessary API calls, so please me patient. Additionally, the 
# API key from Open Secrets only allows for 200 calls per day. For each member of Congress in the tree, two calls to this API are made, so please,
# be careful in making too many requests (no requests are made for cached data)
#
# Additionally, the resulting tree for this address is stored in a JSON (YourTree.json) file and can be accessed via the offline_final.py script,
# which builds the same tree from specified JSON data, but facilitate all the same kinds of interaction
#
# My code below is organized into 5 sections:
#   -API Keys for the Google Civics API and Open Secrets API
#   -Classes that make up the user's Tree
#   -Functions that are used to construct the user's tree.
#   -Function that faciliate interaction with and navigation within the tree.
#   -Execution (The call to main())
#
# To get a sense of how this script work, I reccomend having a look at main() and then having a look at the make_tree() function that takes an addess
# from the user and then calls the other constructor functions to build the user's tree. The returned tree is is then passed to navigate_tree() which launches the
# user interface with calls to the other constructor functions.
#
# In addition to printing data on the user's officeholders, this script utilizes plotly to allow users to plot different pieces of data as well including:
#   -Graph pie chart of the partisan makeup of all the officeholders representing the user.
#   -Graph pie chart of the partisan makeup of federal officeholders representing the user.
#   -Graph pie chart of the partisan makeup of state officeholders representing the user.
#   -Graph pie chart of the partisan makeup of local officeholders representing the user.
#   -Graph pie chart of the partisan makeup of the whole Congressional delegation from the user's state
#   -Bar Chart the top ten industries supporting any member of Congress representing the user or from their state
#   -Bar chart the top ten individuals/companies supporting any member of Congress representing the user or from their state
#
# Please reach out to Gregory McCollum (gregmcc@umich.edu) if you have any questions or encounter any issues. Thank you. -Greg

#--API Keys--

GOOGLE_API_KEY = "AIzaSyAIAjQDes_3Ld_PwJyUNg-BHCE1nkvvzLg"
OPEN_SECRETS_API_KEY = "30076322fa3cbe38573a912475fc3569"


#--Classes that compose the user's Tree and store data--

class RepTree:

    def __init__(self, local, state, federal, other=None):

        self.federal = federal
        self.state = state
        self.local = local
        if other:
            self.other = other

    def json_version(self):
        '''makes JSON-friendly version of whole tree

        This function calls the json.version() function for each person in the RepTree and organizes them into a dictionary.
        Used for printing tree as JSON. Read by the offline_final.py function contruct_tree_from_json().

        Parameters:
        ----------
        self

        Returns:
        ----------
        dictionary
            a dicitonary of key-values, with each level of government and the other (if it extists) level with all the reps at that level as their JSON/dictionary selves.

        '''
        if self.other:
            return {"federal" : [rep.json_version() for rep in self.federal.reps], "state" : [rep.json_version() for rep in self.state.reps], "local" : [rep.json_version() for rep in self.local.reps], "other" : [rep.json_version() for rep in self.other.reps]}
        else:
            return {"federal" : [rep.json_version() for rep in self.federal.reps], "state" : [rep.json_version() for rep in self.state.reps], "local" : [rep.json_version() for rep in self.local.reps]}

    def graph_parties(self):
        '''displays a pie chart of the partisan make up of all officeholders representing the user.
        
        This function builds a dicitonary countering the number of officeholders associated with the user on the basis of party.
        Then this dicitonary's keys and values are passed as to the plotly.graph_objects Figure object and displayed.
        
        Parameters:
        ----------
        self

        Returns:
        ----------
        None
        '''
        party_data = {}

        for rep in self.federal.reps:
            if rep.party not in party_data.keys():
                party_data[rep.party] = 1
            elif rep.party in party_data.keys():
                party_data[rep.party] += 1
        for rep in self.state.reps:
            if rep.party not in party_data.keys():
                party_data[rep.party] = 1
            elif rep.party in party_data.keys():
                party_data[rep.party] += 1
        for rep in self.local.reps:
            if rep.party not in party_data.keys():
                party_data[rep.party] = 1
            elif rep.party in party_data.keys():
                party_data[rep.party] += 1

        fig = go.Figure(data=[go.Pie(labels=list(party_data.keys()), values=list(party_data.values()))])
        fig.show()


class GovLevel:

    def __init__(self, level, reps):

        self.level = level
        self.reps = reps

    def graph_parties(self):
        '''displays a pie chart of the partisan make up of all officeholders representing the user.
        
        This function builds a dicitonary countering the number of officeholders at this level associated with the user on the basis of party.
        Then this dicitonary's keys and values are passed as to the plotly.graph_objects Figure object and displayed.
                
        Parameters:
        ----------
        self

        Returns:
        ----------
        None
        
        '''
        party_data = {}

        for rep in self.reps:
            if rep.party not in party_data.keys():
                party_data[rep.party] = 1
            elif rep.party in party_data.keys():
                party_data[rep.party] += 1

        fig = go.Figure(data=[go.Pie(labels=list(party_data.keys()), values=list(party_data.values()))])
        fig.show()


class Representative:

    def __init__(self, rep_dict, role, level):

        level_dict = {
        "country" : "Federal",
        "administrativeArea1" : "State",
        "administrativeArea2" : "Local",
        "regional" : "Local", "locality" : "Local", "subLocality1" : "Local", "subLocality2" : "Local", "Federal" : "Federal", "State" : "State", "Local" : "Local"}

        self.rep_dict = rep_dict

        try:
            self.name = rep_dict["name"]
        except:
            self.name = None
        try:
            self.party = rep_dict["party"]
        except:
            self.party = None
        try:
            self.role = role
        except:
            self.role = None

        if level in level_dict.keys():
            self.level = level_dict[level]

        try:
            self.address = " ".join([val for val in rep_dict["address"][0].values()])
        except:
            self.address = "No address available"

        try:
            self.phone = rep_dict["phones"][0]
        except:
            self.phone = None

        try:
            self.website = rep_dict["urls"][0]
        except:
            self.website = None

        self.financial_info = None
        self.os_id = None
    
    def short_info(self):
        '''displays the representative's name, office, and party in a single line.

        Parameters:
        ----------
        self

        Returns:
        ----------
        (f"{self.name} - {self.role} - {self.party}")
        
        '''
        return(f"{self.name} - {self.role} - {self.party}")
    
    def full_info(self):
        '''displays all the reprsetnative's info in a small biography

        Parameters:
        ----------
        self

        Returns:
        ----------
        ————————————————————
        ———Information on———
           {self.name}
        ————————————————————
        -Position: {self.role}
        -Party: {self.party}
        -Level: {self.level}
        -Address: {self.address}
        -Phone Number: {self.phone}
        -Website: {self.website}
        ————————————————————
        
        '''

        return(f'''
        ————————————————————
        ———Information on———
           {self.name}
        ————————————————————
        -Position: {self.role}
        -Party: {self.party}
        -Level: {self.level}
        -Address: {self.address}
        -Phone Number: {self.phone}
        -Website: {self.website}
        ————————————————————
        ''')

    def json_version(self):
        return self.__dict__


class CongressPerson(Representative):

    def __init__(self, rep_dict, role, level, os_id, contributors=None, industries=None):
        super().__init__(rep_dict, role, level)

        self.level = "Federal"
        self.os_id = os_id
        if contributors:
            self.contributors = contributors
        else:
            self.contributors = None
        self.contributor_notice = "The organizations themselves did not donate, rather the money came from the organization's PAC, its individual members or employees or owners, and those individuals' immediate families"
        if industries:
            self.industries = industries
        else:
            self.industries = None

    def short_info(self):
        '''displays the congress members name, office, and party in a single line

        Parameters:
        ----------
        self

        Returns:
        ----------
        (f"{self.name} - {self.role} - {self.party}")
        
        '''
        return(f"{self.name} - {self.role} - {self.party}")


    def full_info(self):
        '''returns all the reprsetnative's info in a small biography

        Parameters:
        ----------
        self

        Returns:
        ----------
        ————————————————————
        ———Information on———
           {self.name}
        ————————————————————
        -Position: {self.role}
        -Party: {self.party}
        -Level: {self.level}
        -Address: {self.address}
        -Phone Number: {self.phone}
        -Website: {self.website}
        ————————————————————
        
        '''
        return(f'''
        ————————————————————
        ———Information on———
           {self.name}
        ————————————————————
        -Position: {self.role}
        -Party: {self.party}
        -Level: {self.level}
        -Address: {self.address}
        -Phone Number: {self.phone}
        -Website: {self.website}
        -Top Donors : {'Available' if self.contributors else "Not Available"}
        -Top Contributing Industries : {'Available' if self.industries else "Not Available"}
        ————————————————————
        ''')


    def get_top_contributors(self, cache=None):
        '''retrieves financial information on the member of Congress based on their os_id.

        This function checks if finacnial information already exists in a cache, and (if not), 
        calls the candContrib method from the Open Secrets API stores it as a list of lists in
        self.contributors. Writes the new information to the passed cache.

        Parameters:
        ----------
        self

        cache - dictionary
            the cache in which the os_id is checked for to see if financial information on the Congressperson already exists.

        Returns:
        ----------
        None
        
        '''

        if cache:
            if check_cache(self.os_id, cache=cache):
                self.contributors = cache[self.os_id]
            else:
                root = "https://www.opensecrets.org/api/?method=candContrib"
                params = {"output" : "json", "cid" : self.os_id, "apikey" : OPEN_SECRETS_API_KEY}
                contributors = requests.get(root, params=params).json()

                self.contributors = [x for x in contributors["response"]["contributors"]["contributor"]]
                contributor_list_a = []
                for x in self.contributors:
                    contributor_list_a.append(list(x["@attributes"].values())[0:])

                self.contributors = contributor_list_a

                cache[self.os_id] = self.contributors

                with open("contributor_cache.json", 'w', encoding='utf-8') as file_obj:
                    json.dump(cache, file_obj, ensure_ascii=False, indent=2)
        else:
            root = "https://www.opensecrets.org/api/?method=candContrib"
            params = {"output" : "json", "cid" : self.os_id, "apikey" : OPEN_SECRETS_API_KEY}
            contributors = requests.get(root, params=params).json()

            self.contributors = [x for x in contributors["response"]["contributors"]["contributor"]]
            contributor_list_b = []
            for x in self.contributors:
                contributor_list_b.append(list(x["@attributes"].values())[0:])

            self.contributors = contributor_list_b

            cache = {}
            cache[self.os_id] = self.contributors

            with open("contributor_cache.json", 'w', encoding='utf-8') as file_obj:
                json.dump(cache, file_obj, ensure_ascii=False, indent=2)
    

    def json_version(self):
        return self.__dict__
        #return {"name": self.name, "party" : self.party, "role" : self.role, "contributors" : self.contributors, "industries" : self.industries}

    def get_top_industries(self, cache=None):
        '''retrieves financial information on the member of Congress based on their os_id.

        This function checks if finacnial information already exists in a cache, and (if not), 
        calls the candIndustry method from the Open Secrets API stores it as a list of lists in
        self.industries. Writes the new information to the passed cache.

        Parameters:
        ----------
        self

        cache - dictionary
            the cache in which the os_id is checked for to see if financial information on the Congressperson already exists.

        Returns:
        ----------
        None
        
        '''

        if cache:
            if check_cache(self.os_id, cache=cache):
                self.industries = cache[self.os_id]
            else:

                root = "https://www.opensecrets.org/api/?method=candIndustry"
                params = {"output" : "json", "cid" : self.os_id, "apikey" : OPEN_SECRETS_API_KEY}
                try:
                    industries = requests.get(root, params=params).json()
                except:
                    print("\n")
                    try:
                        params["cycle"] = "2020"
                        industries = requests.get(root, params=params).json()
                    except:
                        params["cycle"] = "2018"
                        industries = requests.get(root, params=params).json()

                self.industries = [x for x in industries["response"]["industries"]["industry"]]
                industries_list_a = []
                for x in self.industries:
                   industries_list_a.append(list(x["@attributes"].values())[1:])

                self.industries = industries_list_a

                cache[self.os_id] = self.industries

                with open("industry_cache.json", 'w', encoding='utf-8') as file_obj:
                    json.dump(cache, file_obj, ensure_ascii=False, indent=2)
        else:
            root = "https://www.opensecrets.org/api/?method=candIndustry"
            params = {"output" : "json", "cid" : self.os_id, "apikey" : OPEN_SECRETS_API_KEY}
            industries = requests.get(root, params=params).json()

            self.industries = [x for x in industries["response"]["industries"]["industry"]]
            industries_list_b = []
            for x in self.industries:
                industries_list_b.append(list(x["@attributes"].values())[1:])

            self.industries = industries_list_b

            cache = {}
            cache[self.os_id] = self.industries

            with open("industry_cache.json", 'w', encoding='utf-8') as file_obj:
                json.dump(cache, file_obj, ensure_ascii=False, indent=2)

        #print(self.industries)

    def plot_contributors(self):
        '''plots the top ten contributos for that candidate in a bar chart

        This function passes the contents of self.contributors to a plotly graph_objects Figure object as a bar chart
        and displays it.

        Parameters:
        ----------
        self

        Returns:
        ----------
        None

        '''
        if self.contributors:
            x = [contributor[0] for contributor in self.contributors]

            fig = go.Figure(go.Bar(x=x, y=[int(contributor[2]) for contributor in self.contributors], name='PAC Contributions'))
            fig.add_trace(go.Bar(x=x, y=[int(contributor[3]) for contributor in self.contributors], name='Individual Contributions'))
            fig.update_layout(barmode='stack')
            fig.update_layout(
                title=f"Top Campaign Contributors for {self.name}, {self.role} in the most recent election cycle.",
                xaxis_title="Top Campaign Contributors",
                yaxis_title="USD($) Contributed",
                legend_title="Kind of Donations")
            fig.show()
        else:
            print("No Contributor Data Available")
    

    def plot_industries(self):
        '''plots the top ten financially-supporting industries for that candidate in a bar chart

        This function passes the contents of self.industries to a plotly graph_objects Figure object as a bar chart
        and displays it.

        Parameters:
        ----------
        self

        Returns:
        ----------
        None

        '''
        if self.industries:
            x = [industry[0] for industry in self.industries]

            fig = go.Figure(go.Bar(x=x, y=[int(industry[2]) for industry in self.industries], name='PAC Contributions'))
            fig.add_trace(go.Bar(x=x, y=[int(industry[1]) for industry in self.industries], name='Individual Contributions'))
            fig.update_layout(barmode='stack')
            fig.update_layout(
                title=f"Top Contributing Industries for {self.name}, {self.role} in the most recent election cycle.",
                xaxis_title="Top Contributing Industry",
                yaxis_title="USD($) Contributed",
                legend_title="Kind of Donations")
            fig.show()
        else:
            print("No Industry Contribution Data Available")


    def raw_contributors(self):
        '''prints the financial information for the candidate.

        This function prints the contents of self.contributors with a single line for each contributing company
        
        Parameters:
        ----------
        self

        Returns:
        ----------
        None
        '''

        if self.contributors:
            print(self.contributor_notice, "\n--------")
            for contributor in self.contributors:
                print(f'''{contributor[0]} - Total: ${contributor[1]} - from Indiviuals: ${contributor[3]} - from PACS: ${contributor[2]}''', "\n-------")
        else:
            print("No Contributor Data Available")


    def raw_industries(self):
        '''prints the financial information for the candidate.

        This function prints the contents of self.industries with a single line for each contributing company
        
        Parameters:
        ----------
        self

        Returns:
        ----------
        None
        '''

        if self.industries:
            for industry in self.industries:
                print(f'''{industry[0]} - Total: ${industry[3]} - from Indiviuals: ${industry[1]} - from PACS: ${industry[2]}''', "\n-------")
        else:
            print("No Contributing Industry Data Available")


class OtherCongressPerson:

    def __init__(self, name, os_id, party, district, contributors=None, industries=None):
        self.name = name
        self.os_id = os_id
        self.level = "Federal"
        self.district = district.replace(" ", "")
        if party == "D" or party == "Democratic Party":
            self.party = "Democratic Party"
        elif party == "R" or party == "Republican Party":
            self.party = "Republican Party"
        elif party == "I" or party == "Independent":
            self.party = "Independent"
        else:
            self.party = "Unknown"

        if contributors:
            self.contributors = contributors
        else:
            self.contributors = None

        self.contributor_notice = "The organizations themselves did not donate, rather the money came from the organization's PAC, its individual members or employees or owners, and those individuals' immediate families"
        
        if industries:
            self.industries = industries
        else:
            self.industries = None
    
    def short_info(self):
        '''displays the congress members name, office, and party in a single line

        Parameters:
        ----------
        self

        Returns:
        ----------
        (f"{self.name} - {self.role} - {self.party}")
        
        '''

        return(f"{self.name} - {self.district} - {self.party}")


    def full_info(self):
        return(f'''
        ————————————————————
        ———Information on———
           {self.name}
        ————————————————————
        -District: {self.district}
        -Party: {self.party}
        -Level: {self.level}
        -Top Donors: {'Available' if self.contributors else "Not Available"}
        -Top Contributing Industries: {'Available' if self.industries else "Not Available"}
        ————————————————————
        ''')


    def get_top_contributors(self, cache=None):
        '''retrieves financial information on the member of Congress based on their os_id.

        This function checks if finacnial information already exists in a cache, and (if not), 
        calls the candContrib method from the Open Secrets API stores it as a list of lists in
        self.contributors. Writes the new information to the passed cache.

        Parameters:
        ----------
        self

        cache - dictionary
            the cache in which the os_id is checked for to see if financial information on the Congressperson already exists.

        Returns:
        ----------
        None
        
        '''


        if cache:
            if check_cache(self.os_id, cache=cache):
                self.contributors = cache[self.os_id]
            else:
                root = "https://www.opensecrets.org/api/?method=candContrib"
                params = {"output" : "json", "cid" : self.os_id, "apikey" : OPEN_SECRETS_API_KEY}
                contributors = requests.get(root, params=params).json()

                self.contributors = [x for x in contributors["response"]["contributors"]["contributor"]]
                contributor_list_a = []
                for x in self.contributors:
                    contributor_list_a.append(list(x["@attributes"].values())[0:])

                self.contributors = contributor_list_a

                cache[self.os_id] = self.contributors

                with open("contributor_cache.json", 'w', encoding='utf-8') as file_obj:
                    json.dump(cache, file_obj, ensure_ascii=False, indent=2)

        else:
            root = "https://www.opensecrets.org/api/?method=candContrib"
            params = {"output" : "json", "cid" : self.os_id, "apikey" : OPEN_SECRETS_API_KEY}
            contributors = requests.get(root, params=params).json()

            self.contributors = [x for x in contributors["response"]["contributors"]["contributor"]]
            contributor_list_b = []
            for x in self.contributors:
                contributor_list_b.append(list(x["@attributes"].values())[0:])

            self.contributors = contributor_list_b

            cache = {}
            cache[self.os_id] = self.contributors

            with open("contributor_cache.json", 'w', encoding='utf-8') as file_obj:
                json.dump(cache, file_obj, ensure_ascii=False, indent=2)

    
    def json_version(self):
        return self.__dict__
        

    def get_top_industries(self, cache=None):
        '''retrieves financial information on the member of Congress based on their os_id.

        This function checks if finacnial information already exists in a cache, and (if not), 
        calls the candIndustry method from the Open Secrets API stores it as a list of lists in
        self.industries. Writes the new information to the passed cache.

        Parameters:
        ----------
        self

        cache - dictionary
            the cache in which the os_id is checked for to see if financial information on the Congressperson already exists.

        Returns:
        ----------
        None
        
        '''

        if cache:
            if check_cache(self.os_id, cache=cache):
                self.industries = cache[self.os_id]
            else:

                root = "https://www.opensecrets.org/api/?method=candIndustry"
                params = {"output" : "json", "cid" : self.os_id, "apikey" : OPEN_SECRETS_API_KEY}
                try:
                    industries = requests.get(root, params=params).json()
                except:
                    print("\n")
                    try:
                        params["cycle"] = "2020"
                        industries = requests.get(root, params=params).json()
                    except:
                        params["cycle"] = "2018"
                        industries = requests.get(root, params=params).json()

                self.industries = [x for x in industries["response"]["industries"]["industry"]]
                industries_list_a = []
                for x in self.industries:
                   industries_list_a.append(list(x["@attributes"].values())[1:])

                self.industries = industries_list_a

                cache[self.os_id] = self.industries

                with open("industry_cache.json", 'w', encoding='utf-8') as file_obj:
                    json.dump(cache, file_obj, ensure_ascii=False, indent=2)

        else:
            root = "https://www.opensecrets.org/api/?method=candIndustry"
            params = {"output" : "json", "cid" : self.os_id, "apikey" : OPEN_SECRETS_API_KEY}
            industries = requests.get(root, params=params).json()

            self.industries = [x for x in industries["response"]["industries"]["industry"]]
            industries_list_b = []
            for x in self.industries:
                industries_list_b.append(list(x["@attributes"].values())[1:])

            self.industries = industries_list_b

            cache = {}
            cache[self.os_id] = self.industries

            with open("industry_cache.json", 'w', encoding='utf-8') as file_obj:
                json.dump(cache, file_obj, ensure_ascii=False, indent=2)


    def plot_contributors(self):
        '''plots the top ten contributos for that candidate in a bar chart

        This function passes the contents of self.contributors to a plotly graph_objects Figure object as a bar chart
        and displays it.

        Parameters:
        ----------
        self

        Returns:
        ----------
        None

        '''

        if self.contributors:
            x = [contributor[0] for contributor in self.contributors]

            fig = go.Figure(go.Bar(x=x, y=[int(contributor[2]) for contributor in self.contributors], name='PAC Contributions'))
            fig.add_trace(go.Bar(x=x, y=[int(contributor[3]) for contributor in self.contributors], name='Individual Contributions'))
            fig.update_layout(barmode='stack')
            fig.update_layout(
                title=f"Top Campaign Contributors for {self.name} in the most recent election cycle.",
                xaxis_title="Top Campaign Contributors",
                yaxis_title="USD($) Contributed",
                legend_title="Kind of Donations")
            fig.show()
        else:
            print("No Contributor Data Available")
    

    def plot_industries(self):
        '''plots the top ten financially-supporting industries for that candidate in a bar chart

        This function passes the contents of self.industries to a plotly graph_objects Figure object as a bar chart
        and displays it.

        Parameters:
        ----------
        self

        Returns:
        ----------
        None

        '''
        if self.industries:
            x = [industry[0] for industry in self.industries]

            fig = go.Figure(go.Bar(x=x, y=[int(industry[2]) for industry in self.industries], name='PAC Contributions'))
            fig.add_trace(go.Bar(x=x, y=[int(industry[1]) for industry in self.industries], name='Individual Contributions'))
            fig.update_layout(barmode='stack')
            fig.update_layout(
                title=f"Top Contributing Industries for {self.name} in the most recent election cycle.",
                xaxis_title="Top Contributing Industry",
                yaxis_title="USD($) Contributed",
                legend_title="Kind of Donations")
            fig.show()
        else:
            print("No Industry Contribution Data Available")


    def raw_contributors(self):
        '''prints the financial information for the candidate.

        This function prints the contents of self.contributors with a single line for each contributing company
        
        Parameters:
        ----------
        self

        Returns:
        ----------
        None
        '''
        if self.contributors:
            print(self.contributor_notice, "\n--------")
            for contributor in self.contributors:
                print(f'''{contributor[0]} - Total: ${contributor[1]} - from Indiviuals: ${contributor[3]} - from PACS: ${contributor[2]}''', "\n-------")
        else:
            print("No Contributor Data Available")


    def raw_industries(self):
        '''prints the financial information for the candidate.

        This function prints the contents of self.industries with a single line for each contributing company
        
        Parameters:
        ----------
        self

        Returns:
        ----------
        None
        '''
        if self.industries:
            for industry in self.industries:
                print(f'''{industry[0]} - Total: ${industry[3]} - from Indiviuals: ${industry[1]} - from PACS: ${industry[2]}''', "\n-------")
        else:
            print("No Contributing Industry Data Available")


#--Functions Building the User's Tree from API data [called by make_tree()]--

def get_rep_info(address):
    '''Takes a given address and retrievs the Google Civics API respond from it
    
    This function take a user's address passes it to the Google Civics API's representatives method as the 'address' parameter
    and returns a JSON-version of the data if the status code is 200.

    Parameters:
    ----------
    address - str
        corresponds to a location of the user's choice

    Returns:
    ----------
    data - dictionary
        the Google Civics response data
    '''

    root_url = "https://civicinfo.googleapis.com/civicinfo/v2/representatives"
    params = {"key" : GOOGLE_API_KEY, "address" : address}

    data = None
    try:
        response = requests.get(root_url, params=params)
        if response.status_code == 200:
            data = response.json()
    except:
        print("\nAn API issue occurred, please try again.\n")

    return data


def construct_other_congresspersons(address, congress_ids):
    '''builds a list of OtherCongressPerson object based on the user's address

    This function looks for a state name or code in the entered address and then uses that code
    to get information on all the members of Congress from that state from the Open Secrets
    congress_ids sheet. That information is used to construct a OtherCongressPerson object for 
    each member of Congress from that State/

    Parameters:
    ----------
    address - str
        corresponds to a location of the user's choice
    
    congress_ids - list
        from Open Secrets, includes information on each member of Congress.

    Returns:
    ----------
    other_congress_persons - list 
        a list of OtherCongressPerson objects with an object for every member of Congress coming from the user's state
    
    '''
    states = {
        "AL" : ["alabama", "al"],
        "AK" : ["alaska", 'ak'],
        "AZ" : ["arizona", "az"],
        "AR" : ["arkansas", "ar"],
        "CA" : ["california", "ca"],
        "CO" : ["colorado", 'co'],
        "CT" : ["connecticut", "ct"],
        "DE" : ["delaware", "de"],
        "DC" : ["district of columbia", "dc"],
        "FL" : ["flordia", "fl"],
        "GA" : ["georgia", "ga"],
        "HI" : ["hawaii", "hi"],
        "ID" : ["idaho", "id"],
        "IL" : ["illinois", "il"],
        "IN" : ["indiana", "in"],
        "IA" : ["iowa", "ia"],
        "KS" : ["kansas", "ks"],
        "LA" : ["louisiana", "la"],
        "ME" : ["maine", "me"],
        "MD" : ["maryland", "md"],
        "MA" : ["massachusetts", "ma"],
        "MI" : ["michigan", "mi"],
        "MS" : ["mississippi", "ms"],
        "MO" : ["missouri", "mo"],
        "MT" : ["montana", "mt"],
        "NE" : ["nebraska", "ne"],
        "NV" : ["nevada", "nv"],
        "NH" : ["new hampshire", "nh"],
        "NJ" : ["new jersey", "nj"],
        "NM" : ["new mexico", "nm"],
        "NY" : ["new york", "ny"],
        "NC" : ["north carolina", "nc"],
        "ND" : ["north dakota", "nd"],
        "OH" : ["ohio", "oh"],
        "OK" : ["oklahoma", "ok"],
        "OR" : ["oregon", 'or'],
        "PA" : ["pennsylvania", "pa"],
        "PR" : ["puerto rico", "pr"],
        "RI" : ["rhode island","ri"],
        "SC" : ["south carolina", "sc"],
        "SD" : ["south dakota", "sd"],
        "TN" : ["tennessee", "tn"],
        "TX" : ["texas", "tx"],
        "UT" : ["utah", "ut"],
        "VT" : ["vermont", "vt"],
        "VA" : ["virginia", "va"],
        "WV" : ["west virginia", "wv"],
        "WI" : ["wisconsin", "wi"],
        "WY" : ["wyoming", "wy"],}

    other_congress_persons = []
    state = None
    for key, val in states.items():
        for value in val:
            if " " + value + " " in address.lower():
                state = key
    for row in congress_ids:
        if state == row[3][:2]:
            new_person = OtherCongressPerson(name=row[1].split(",")[1].strip() + " " + row[1].split(",")[0].strip(" "), os_id=row[0], party=row[2], district=f"{state} - {row[3][2:]}")
            other_congress_persons.append(new_person)
    return other_congress_persons


def construct_Reps(data):
    '''builds list fo Representative objects based on information from the Google Civics API

    This funciton takes data from the Google Civics API response and builds a list of
    Representative objects based on the data for each officeholder/offical.

    Parameters:
    ----------
    data - dict
        a dicitionary of data from Google Civics API that includes information on local, state, and federal officeholders

    Returns:
    ----------
    officials - list
        a list of Representative-class objects based on the Google Civics data

    '''
    if data:
        office_indices ={}
        for role in data["offices"]:
            office_indices[role["name"]] = [role["officialIndices"], role["levels"][0]]

    officials = []
    for key,val in office_indices.items():
        for person_index in val[0]:
            officials.append(Representative(data["officials"][person_index], key, val[1]))

    return officials


def sort_reps(reps):
    '''sorts Representatives by level of govenrment

    This function takes a list of Representative objects (from construct_reps())
    and sorts them by the level of government in their .level attribute. Sorts
    them into Federal, State, and Local levels.

    Parameters:
    ----------
    reps - list
        list of Reprsentative Objects

    Returns:
    ----------
    dictionary (of lists)
        a dictionary grouping the Representatives by level, sorted into a list held in each value
    
    '''
    federal_reps = [rep for rep in reps if rep.level == "Federal"]
    state_reps = [rep for rep in reps if rep.level == "State"]
    local_reps = [rep for rep in reps if rep.level == "Local"]
    return {"federal" : federal_reps, "state": state_reps, "local" : local_reps}


def make_congressperson(rep, congress_ids):
    '''for turns a Representative into a CongressPerson object if applicable.

    This function takes a passed Representative object and checks to see if the name
    of the corresponding officeholder is in the Open Secret's Congress Ids list with the following criteria:

        a. checking if names match
        b. checking if last name and party affiliation match
        c. checking if last name matches and then uses fuzzy matching to see if full name matches (in case of nicknames or spelling variations)

    This method accounts for distinctions in first names (Chris vs. Christopher) between the Google Civics API data and the Open Secrets data.

    If a match is found, a CongressPerson object is contstructed with the Representive info and info from the Congress_ids list.

    Parameters:
    ----------
    rep - Representative Object
        a representative object that might (or might not) correspond to a member of Congress
    
    congress_ids - list
        from Open Secrets, includes information on each current member of Congress and information to retrieve financial info on that member.

    Returns:
    ----------
    CongressPerson Object -OR- Representative Object
        if a corresponding memebr of Congress is found, returns CongressPerson Object, else return Rep unchanged
    '''
    for person in congress_ids[1:]:
        if rep.name == person[1].split(" ")[1] + " " + person[1].split(" ")[0].strip(","):
            return CongressPerson(rep.rep_dict, rep.role, rep.level, person[0])
        elif rep.name.split(" ")[-1] == person[1].split(" ")[0].strip(",") and rep.party[1] == person[2]:
            return CongressPerson(rep.rep_dict, rep.role, rep.level, person[0])
    for person in congress_ids[1:]:
        if rep.name.split(" ")[-1] == person[1].split(",")[0]:
            if fuzz.ratio(rep.name, person[1].split(",")[1].strip(" ") + " " + person[1].split(",")[0].strip(",").strip(" ")) > 70:
                return CongressPerson(rep.rep_dict, rep.role, rep.level, person[0])
    return rep


def check_cache(input, cache=None):
    '''check if a passed value is a key in a given cache
    
    This function checks if a passed value is a key in a specified cache.
    If it is, the corresponding cache value is returned. If not, Nonn is returned

    Parameters:
    ----------
    input - str
        a value that might be stored as a key value in a cache

    Returns:
    ----------
    cache - dicitionary
        a dictionary of materials read from a cache file.

    '''
    if cache:
        if input in cache.keys():
            if cache[input] is not None:
                return cache[input]
    else:
        return None


def make_tree():
    '''makes the user's RepTree

    This function builds the user's RepTree by asking for an address and calling the funcitons and classes above to contruct it.
    This function reads the relevant caches in and uses them in calling the function above. This function also writes the
    contructed tree to a JSON file.

    Parameters:
    ----------
    None

    Returns:
    ----------
    tree - RepTree Object
        a RepTree object containg information gathered from the Google Civics API and Open Secrets API with the user's given address as the starting point.
        This tree is used by the navigation funcitons lists below.

    '''
    #loading caches
    with open("os_congress.csv", 'r', encoding="utf-8", newline='') as file_obj:
            congress_ids = []
            reader = csv.reader(file_obj, delimiter=",")
            for row in reader:
                congress_ids.append(row)

    cache = None
    try:
        with open("final_cache.json", 'r', encoding="utf-8") as file_obj:
            cache = json.load(file_obj)
    except:
        print("\n")

    contributor_cache = None
    try:
        with open("contributor_cache.json", 'r', encoding="utf-8") as file_obj:
            contributor_cache = json.load(file_obj)
    except:
        print("\n")

    industry_cache = None
    try:
        with open("industry_cache.json", 'r', encoding="utf-8") as file_obj:
            industry_cache = json.load(file_obj)
    except:
        print("\n")

    #Recieveing Address
    address = input("\n     Please submit an address: ")
    address_code = hashlib.md5(address.encode()).hexdigest()

    print('''
        ---------------------------
        Now Building Your Officeholder Tree.
        This may take a few moments.
        ---------------------------
    ''')

    #Checking cache and/or getting rep info
    if check_cache(address_code, cache=cache):
        rep_data = check_cache(address_code, cache=cache)
    else:
        rep_data = get_rep_info(address)

        if cache and check_cache(address_code, cache=cache) is None:
            cache[address_code] = {key : val for key, val in rep_data.items() if key != "normalizedInput"}

            with open("final_cache.json", 'w', encoding='utf-8') as file_obj:
                json.dump(cache, file_obj, ensure_ascii=False, indent=2)

        elif cache is None:
            cache = {}
            cache[address_code] = {key : val for key, val in rep_data.items() if key != "normalizedInput"}

            with open("final_cache.json", 'w', encoding='utf-8') as file_obj:
                json.dump(cache, file_obj, ensure_ascii=False, indent=2)


    #Orgnaizing officeholder info and constructing OtherCongressPersons
    sorted_officials = sort_reps(construct_Reps(rep_data))
    other_congress_people = construct_other_congresspersons(address=address, congress_ids=congress_ids)

    #Turning relevant Reps in CongressPersons objects
    new_feds = []
    for rep in sorted_officials["federal"]:
        if "President" not in rep.role:
            new_feds.append(make_congressperson(rep, congress_ids))
        else:
            new_feds.append(rep)


    sorted_officials["federal"] = new_feds

    #Getting Financial Info
    sorted_officials = [val for val in sorted_officials.values()]
    for fed in sorted_officials[0]:
        if fed.os_id:
            fed.get_top_contributors(cache=contributor_cache)
            fed.get_top_industries(cache=industry_cache)

    for rep in other_congress_people:
        if rep.os_id:
            rep.get_top_contributors(cache=contributor_cache)
            rep.get_top_industries(cache=industry_cache)

    #building class tree
    federal = GovLevel(level="Federal", reps=sorted_officials[0])
    state = GovLevel(level="State", reps=sorted_officials[1])
    local = GovLevel(level="Local", reps=sorted_officials[2])
    other = GovLevel(level="Other", reps=other_congress_people)

    #building top-level
    tree = RepTree(local=local, state=state, federal=federal, other=other)
    print("\n   Your Tree Has Been Successfuly Constructed!\n")

    with open("YourTree.json", 'w', encoding='utf-8') as file_obj:
        json.dump(tree.json_version(), file_obj, ensure_ascii=False, indent=2)

    return tree


#--Functions Faciliating User Interaction with Tree--

def tree_navigator(tree):
    '''facilitates navigation through tree

    This function allows users to navigate to the GovLevel objects held by the passsed RepTree Object with a While Loop.
    It also allows user to see to graph the party affiliations from all their officeholdes by calling the RepTree's
    graph_parties() function. It calls level_navigator with the user's choice

    Parameters:
    ----------
    tree - RepTree Object
        User's RepTree object containing their officeholder info.

    Returns:
    ----------
    None.
    '''
    if type(tree) == RepTree:
        while True:
            print(f'''

                Welcome to your Personalized Tree of Officeholders and Elected Officials
                -----------------------------------------------------------------------
                Your Tree Features information on:
                    -{len(tree.federal.reps)} federal officeholders
                    -{len(tree.state.reps)} state officeholders
                    -{len(tree.local.reps)} local officeholders
                    {f'-{len(tree.other.reps)} total members of Congress from your state' if tree.other else ""}

                Options:
                    1. Graph Party Affiliations for all my officeholders
                    2. Learn More about my federal officeholders
                    3. Learn More about my state officeholders
                    4. Learn More about my local officeholders
                    {f'5. Learn more about the other Congressional representatives from my state' if tree.other else ""}

                    0. Exit
            ''')
            input2 = input("Select an option: ")
            if input2.strip().lower() in ("exit", "quit", "leave", "goodbye", "good-bye", "depart"):
                print("\nThank you!\n")
                quit()
            elif int(input2.strip()) == 1:
                tree.graph_parties()
            elif int(input2.strip()) == 2:
                level_navigator(tree.federal)
            elif int(input2.strip()) == 3:
                level_navigator(tree.state)
            elif int(input2.strip()) == 4:
                level_navigator(tree.local)
            elif int(input2.strip()) == 5:
                level_navigator(tree.other)
            elif int(input2.strip()) == 0:
                print("\nThank you!\n")
                break

    else:
        print("An error occurred, please try again.")


def level_navigator(level):
    '''facilitates navigation through GovLevel

    This function allows users navigate to the list of represenatives/officeholders held by the GovLevel object
    or graph the partisan affiliation of all officeholders at that level. 

    Parameters:
    ----------
    level - GovLevel Object
        an object holding officeholders corresponding to a particular level of govenment (Federal, State, Local, Other)

    Returns:
    ----------
    None.
    '''
    if type(level) == GovLevel:
        if level.level.lower() != "other":
            print(f'''
                Your {level.level} Officeholders
                --------------------------------
                More information is available for {len(level.reps)} {level.level} officeholders.''')

            if level.level == "Federal":

                print(f'''
                Financial Information is available for Members of the US House of Representative and the US Senate.
                Financial Informaiton is available for {len([x for x in level.reps if x.os_id is not None])} of your federal officeholders''')
        elif level.level.lower() == "other":
            print(f'''
                Congressional Representatives and Representatives from you state ({level.reps[0].district[:2]}).
                --------------------------------
                More information is available on all {len(level.reps)} members of Congress from your state.
                Financial information is available for these members also.''')


        while True:

            print(f'''
                {level.level if level.level.lower() != 'other' else "My State Member"} Options:
                ---------------------
                1. Graph party affiliation for my {level.level if level.level.lower() != 'other' else "state's"} {'officeholders' if level.level.lower() != "other" else "Congressional delegation"}.
                2. List my {level.level if level.level.lower() != 'other' else "state's"} officeholders and learn more.\n''')

            input2 = input("Select an option or 'done' to return to the full tree: ")
            if input2.strip().lower() in ("done", "back"):
                break
            elif input2.strip().lower in ("quit", "exit"):
                print("\nThank you!\n")
                quit()
            elif int(input2.strip()) == 1:
                level.graph_parties()
            elif int(input2.strip()) == 2:
                rep_navigator(level.reps)
    else:
        print("sorry an issue occurred")


def rep_navigator(reps):
    '''facilitates navigation through a list of officeholders

    This function allows presents users with a list of officeholders from the GovLevel's .reps attribute.
    This function allows organizes each officeholder into a dicitonary with a corresponding number key and prints each officeholder's brief info.
    User's can then select an officeholder to learn more about.

    Parameters:
    ----------
    reps - a list
        a list of officeholders in Representative, CongressPerson, or OtherCongressPerson objects

    Returns:
    ----------
    None.
    '''
    rep_dict = {}
    i = 1
    for rep in reps:
        rep_dict[f"{i}"] = rep
        i += 1

    while True:
        print(f"\n---Your {reps[0].level} OfficeHolders--")
        for key, val in rep_dict.items():
            print(f"{key} - {val.short_info()}")

        input3 = input("\nSelect the number of an officeholder to learn more or done: ")
        if input3.strip().lower() in ("done", "back"):
            break
        elif input3.strip().lower() in ("exit", "quit", "leave", "goodbye", "good-bye", "depart"):
            print("thank You!")
            quit()
        elif input3.strip() in list(rep_dict.keys()):
            selected = [val for key, val in rep_dict.items() if key == input3.strip()][0]
            print(selected.full_info())
            if type(selected) == CongressPerson or type(selected)==OtherCongressPerson:
                congressperson_navigator(selected)
            elif type(selected) == Representative:
                individual_navigator(selected)
        elif input3.strip().lower() in ("done", "back"):
            break
        elif input3.strip().lower() in ("exit", "quit", "leave", "goodbye", "good-bye", "depart"):
            print("thank You!")
            quit()
        elif input3.strip() not in list(rep_dict.keys()):
            print("Invalid entry. Please enter a number correspondign to particular officeholder")


def individual_navigator(person):
    '''Allows users to return to the rep list once done viewing a full officeholder bio.

    Used for Representative Objects. It starts a while loop that allows users to view the full bio information presented by the rep_navigator() funciton.
    Users can enter 'done' or 'back' to return to the loop

    Parameters:
    ----------
    person - a Representative class object

    Returns:
    ----------
    None.
    '''
    while True:
        input5 = input("Enter 'Done' or 'Back' to return to full list: ")
        if input5.strip().lower() in ("done", "back"):
            break
        elif input5.strip().lower in ("quit", "exit"):
            print("Thank You!")
            quit()


def congressperson_navigator(person):
    '''allows users to access financial information on members of Congress

        Used for CongressMember or OtherCongressMember class objects. It presents the user with additional options
        to view the member of Congress' financial contributor and contributing industries information gathered from 
        Open Secrets by listing the infromation or charting it using plotly. It calls the class plot_contributor(), plot_industries(),
        raw_contributors() and raw_industries() information to do so.

        Users can enter "done" or "back" to return to the list of Representatives.
    
    Parameters:
    ----------
    person - a CongressMember --OR-- OtherCongressMember class object
        a member of Congress who's financial information the user can view and graph.

    Returns:
    ----------
    None.
    
    '''
    while True:
        print(f'''         {person.name}'s Data Options:
        ----------------------------
        1. Graph data on {person.name}'s top contributors from the last election cycle.
        2. View raw data on {person.name}'s top contributors from the last election cycle.
        3. Graph data on {person.name}'s top industries financially supporting them in the last election cycle.
        4. View raw data on {person.name}'s top industries financially supporting them in the last election cycle.
            ''')
        input4 = input("Select an option or 'Done' to Return to your federal officeholder list: ")
        if input4.strip().lower() in ("done", "back"):
            break
        elif input4.strip().lower in ("quit", "exit"):
            print("Thank You!")
            quit()
        elif int(input4.strip()) == 1:
            person.plot_contributors()
        elif int(input4.strip()) == 2:
            person.raw_contributors()
        elif int(input4.strip()) == 3:
            person.plot_industries()
        elif int(input4.strip()) == 4:
            person.raw_industries()


def main():
    '''
    Presents the main menu and prompts users to launch program, display more information, or leave.
    
    '''

    print('''
    ################################
    ####### Who ####################
    ####### Represents #############
    ####### Me? ####################
    ################################
    ####### An SI507 ###############
    ####### Final Project ##########
    ####### by Gregory McCollum ####
    ####### gregmcc@umich.edu ######
    ################################
    ''')

    while True:
        input1 = input('''
            Main Menu Options:
            -----------------
            1. Launch Program
            2. Summary and Tips
            3. Exit

            Please Select an option: ''')
        if input1:
            try:
                if input1.strip().lower() in ("exit", "quit"):
                    print("Goodbye!")
                    quit()
                elif int((input1.strip())) == 1:
                    tree = make_tree()
                    tree_navigator(tree)
                elif int((input1.strip())) == 2:
                    print('''

                    This programs develops a tree of officeholers, representatives, and elected figures from each
                    user's input address and then allows the user to navigate through to learn more about
                    each official, and for members of Congress learn more the organizations and industries
                    that financially support those members of Congress' most recent election campaign. Users
                    can graph this data and graph data on their officeholders' party affiliations at every
                    level. Additionally, biographical and financial information is available for all
                    members of the Congressional delegation from the user's state.

                    Financial Note: For the top contributors finaical data the organizations themselves did not donate, 
                    rather the money came from the organization's PAC, its individual members or employees or owners, and
                    those individuals' immediate families 

                    Data is retrived from the Google Civics API and Open Secrets API.
                    Documentation on these APIs can be found here:

                        Google Civics: https://developers.google.com/civic-information/docs/using_api
                        Open Secrets: https://www.opensecrets.org/open-data/api
                        
                    Here's a summary of the tree user's can navigate:

                    ----------------------------------------------------------------------------------------------------
                    -Top Level
                        |
                        -Federal Officals
                            |
                            -List of Federal Officeholders
                                |
                                Individual Officeholder Bibliographic Information and/Or Financial Information
                        |
                        -State Officals
                            |
                            -List of State Officeholders
                                |
                                Individual Officeholder Information
                        |
                        -Local Officals
                            |
                            -List of Local Officeholders
                                |
                                Individual Officeholder Information
                        |
                        -All Members of the User's State Congressional Delegation
                            |
                            -List of Members of Congress from state
                                |
                                Individual Member of Congrsss Bibliographic Information and Financial Information
                    ----------------------------------------------------------------------------------------------------

                    Tips:
                        -Enter you full address when prompted in the following format:
                            123 Cherry Grove Road, Columbus, OH 43004

                        -No information on your address is cached by this program.

                        -Use the specified number options to navigate "down" the tree. Enter the phrase "back" or "done"
                        at any point to navigate "up" a step in the tree.

                        -This program utilizes my Open Secrets API key and makes two requests for each member of Congress 
                        returned. This API key only allows for 200 daily queries, so please be wise in using it.

                    ''')
                    while True:
                        input6 = input("Enter 'Done' or 'Back' to return to the Main Menu: ")
                        if input6.strip().lower() in ("done", "back"):
                            break
                        elif input6.strip().lower in ("quit", "exit"):
                            print("\nThank You!\n")
                            quit()
                elif int((input1.strip())) == 3:
                    print("\nGoodbye!\n")
                    break
            except:
                print("\nSorry, Couldn't understand your input. Please try again.\n")


#--Execution--

if __name__ == "__main__":
    main()