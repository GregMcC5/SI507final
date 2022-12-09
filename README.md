
# Who Represents Me? - SI507 Final Project
Gregory McCollum's final project for SI507 in Fall 2022 Semester.
Contact Greg at gregmcc@umich.edu

## Overview

This project uses Python to help users learn more about the officeholders who represent them at various levels of government. It constructs a tree based on the user's input address and develop a navigable tree composed of data on the federal, state, and local officeholders that represents someone living at that address. With this tree the user can get more details on particular officeholders, and for member of US Congress, learn about what companies and industries are financially supporting those members of Congress. In addition to the user's House Representative and Senators, information is available on everyone in the Congressional Delegation from the user's state.

This final_project.py script constructs the user's tree on the basis of the address,  retrieves the data from APIs or from cached data, and allows user interaction with the tree. Th is script also writes the user's tree to a JSON file called YourTree.json.

The offline_final.py project constructs the user's tree from a JSON file (like the one developed by the main script), and then allows user interaction with the tree.

For testing purposes, you can try out final_project.py with your own address or with the address of the University of Michigan, for which the data is cached: 

 - 500 S State St, Ann Arbor, MI 48109

For testing offline_final.py, you can use MichiganTree.json when prompted. Also, while this script does cache user's results, no address information is saved in any caches.

## Data Sources

Information on this project comes from Google Civics API and the Open Secrets API. Learn more about those API here:
    - Google Civics:https://developers.google.com/civic-information/docs/using_api
    - Open Secrets: https://www.opensecrets.org/open-data/api-documentation

These API require Keys to access. The documentation above provides details on how to access keys. My keys have been provided in this repository.

## Data Structure

These scripts organize the data into a navigable tree. A new tree is constructed for each address and are personalized to each user. The tree is composed of several levels of "stacked" class objects that hold each other in attributes. A the top level, a single RepTree class object is returned, which holds 4 GovLevel class objects (one for Federal, State, Local government levels, and one the user's whole state Congressional Delegation) in correpsonding attributes (self.federal, self.state, etc.). Each GovLevel object holds a list of officholders as Representative class objects (for officeholders who aren't Congress members), CongressPerson calss objects (a subclass of Reprsentative, used for members of Congress), or OtherCongressPerson (used for all members of Congress from the user's state). These class objects hold all the information related to a particular officeholder.

 This structure is also discuss within the script, but can here is a visual design of it also:

                    ----------------------------------------------------------------------------------------------------
                    -Top Level (RepTree object)
                        |
                        -Federal Officals (GovLevel object)
                            |
                            -List of Federal Officeholders
                                |
                                Individual Officeholder Bibliographic Information and/Or Financial Information (Representative and CongressPerson objects)
                        |
                        -State Officals (GovLevel object)
                            |
                            -List of State Officeholders
                                |
                                Individual Officeholder Information (Representative objects)
                        |
                        -Local Officals (GovLevel object)
                            |
                            -List of Local Officeholders
                                |
                                Individual Officeholder Information (Representative objects)
                        |
                        -All Members of the User's State Congressional Delegation (GovLevel object)
                            |
                            -List of Members of Congress from state
                                |
                                Individual Member of Congrsss Bibliographic Information and Financial Information (OtherCongressPerson objects)
                    ----------------------------------------------------------------------------------------------------

## Running the Code

This code requires a handful of non-standard Python libraries to use. These can all be installed with pip:

- requests – (Used to access data from Google Civics API and Open Secrets API, https://pypi.org/project/requests/)

- hashlib – Used to store user-input addresses as cryptography hash values in final_cahche.json, rather than storing user personal information, https://pypi.org/project/hashlib/

- plotly – Used to plot information on the institutions and industries that financially supported members of Congress in bar charts, and graph the partisan composition of the user’s returned officeholders, https://pypi.org/project/plotly/

- fuzzywuzzy – Used to perform fuzzy matching on members of Congress’ names when the Google Civics’ name doesn’t precisely match the Open Secret’s name (‘Ben Cardin’ vs. ‘Benjamin L. Cardin’, https://pypi.org/project/fuzzywuzzy/)


When running the scripts, follow the prompts on entering an address or filename. Once in the tree, select the numbered options at each level. You can enter "Done" or "Back" at any point to navigate back "up" a level in the tree.

## Repository Inventory

Scripts:

- final_project.py - The main script. It constructs a tree from API and cached data and faciliates interaction with it. It also writes the YouTree.json file.

- offline_project.py - This script constructs a tree based on a JSON file (like YourTree.json) and facilitates interaction with it.

Caches:

- final_cache.json - The data cache for Google Civics API material, using the cryptographed version of the address as the key, and the response data as the value (in JSON format). Hold data on the offices and incumbent officeholders associated with an address.

- industry_cache.json - The data cache for Open Secrets API candIndustry material. Holds records on a particular member of Congress' top-giving industries. OS_IDs (Open Secrets IDs) are used as the key values here.

- contributor_cache.json - The data cache for Open Secrets API candIndustry material. Holds records on a particular member of Congress' top-giving companies. OS_IDs (Open Secrets IDs) are used as the key values here.

Others:

- os_congress.csv - From Open Secrets, includes data on each current member of Congress matched with their OS_ID. Used to match members of Congress with their ids in final_project.py.

- YourTree.json - The tree written by final_project.py. Reflected the most recently constructed tree by the script. Can be opened and navigated by offline_project.py.

- MichiganTree.json - The tree written by final_project.py when using th University of Michigan address: 500 S State St, Ann Arbor, MI 48109. Can be opened and navigated by offline_project.py.

- READEME.md - This document.
