import final_project as fp
import json

###################
# Welcome to my final project offline script.
#
# This script constructs a tree from data stored in a JSON file, rather than with a passed address (as final_project.py does).
# This file imports my final_project.py script as a module and refers to different class objects and functions throughout.
# While this script constructs the tree differently, it facilitates the exact same kinds and level of interaction with and navigation
# through the tree, because it calls the navigate_tree() function from the main script.
#
# For testing purposes, the JSON of all the data from the University of Michigan address are held in the MichiganTree.json file. Enter the
# filename when prompted and it will allows you to interact with the tree exactly as you would if you were able to access it through the address
# in the other script.

def construct_tree_from_json(filename):
    '''constructs the rep tree from a give json filepath
    
    This function takes a passed filepath and reads it, and then parses it for information to consturct lists of Representatives CongressPerson and OtherCongressPerson class objects,
    sort them into GovLevel class objects and associate them with a RepTree object and is then returned.

    Parameters:
    ----------
    filepath - string
        refers to a JSON file in the current directory

    Returns:
    ----------
    tree - RepTree oject
        a RepTree object holding all the information parsed from the JSON file.
    
    '''
    #-Load Tree from JSON
    json_tree = None
    try:
        with open(filename, 'r', encoding='utf-8') as obj:
            json_tree = json.load(obj)
    except:
        print("Issue Loading Tree")
        return None

    #-Construct Tree Object
    if json_tree:
        state_people = [fp.Representative(rep_dict=x["rep_dict"], role=x["role"], level="State") for x in json_tree["state"]]
        local_people = [fp.Representative(rep_dict=x["rep_dict"], role=x["role"], level="Local") for x in json_tree["local"]]
        federal_people = []
        other_people = [fp.OtherCongressPerson(name=x["name"], os_id=x["os_id"], party=x["party"], district=x["district"],contributors=x["contributors"], industries=x["industries"]) for x in json_tree["other"]]

        for person in json_tree["federal"]:
            if person["os_id"] is not None:
                federal_people.append(fp.CongressPerson(rep_dict=person["rep_dict"], role=person["role"], level="Federal", os_id=person["os_id"], contributors=person["contributors"], industries=person["industries"]))
            else:
                federal_people.append(fp.Representative(rep_dict=person["rep_dict"], role=person["role"], level="Federal"))

        federal = fp.GovLevel(level="Federal", reps=federal_people)
        state = fp.GovLevel(level="State", reps=state_people)
        local = fp.GovLevel(level="Local", reps=local_people)
        other = fp.GovLevel(level="Other", reps=other_people)

        tree = fp.RepTree(local=local, state=state, federal=federal, other=other)

        print(f"{'tree construced' if tree else 'tree not constructed'}")

        return tree


def main():

    print('''
    ################################
    ####### Who ####################
    ####### Represents #############
    ####### Me? ####################
    ####### (Offline Version) ######
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
                    filename = input("\nPlease enter json filename with the tree in it (with extension) > ")
                    tree = construct_tree_from_json(filename)
                    fp.tree_navigator(tree)
                    break
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

                    In this offline version, data is retrieved from a JSON file constructed by the original script.

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
                        -Enter the full filename (with extension) that features the tree.

                        -Use the specified number options to navigate "down" the tree. Enter the phrase "back" or "done"
                        at any point to navigate "up" a step in the tree.

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



if __name__ == "__main__":
    main()