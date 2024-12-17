import json
import random

def create_json_collection(input_file, output_file):
    # Set to keep track of unique usernames
    unique_usernames = set()
    
    # Dictionary to store the JSON documents by username for easy lookup
    user_dict = {}

    # Extract the number from the file name and create a user
    file_number = ''.join(filter(str.isdigit, input_file))
    if file_number:
        main_user = {
            "username": f"user{file_number}",
            "followers_list": [],
            "following_list": [],
            "interactions": {},
            "hashtags": []
        }
        user_dict[f"user{file_number}"] = main_user
        unique_usernames.add(f"user{file_number}")

    # Read the text file line by line to initialize users
    with open(input_file, 'r') as file:
        for line in file:
            # Split the line into two numbers
            numbers = line.split()

            # Ensure there are exactly two numbers in the line
            if len(numbers) == 2:
                for num in numbers:
                    username = f"user{num}"

                    # Add only unique usernames
                    if username not in unique_usernames:
                        unique_usernames.add(username)

                        # Create the JSON document
                        document = {
                            "username": username,
                            "followers_list": [],
                            "following_list": [],
                            "interactions": {},
                            "hashtags": []
                        }

                        # Add the document to the dictionary
                        user_dict[username] = document

    # Read the text file again to populate following_list and followers_list
    with open(input_file, 'r') as file:
        for line in file:
            # Split the line into two numbers
            numbers = line.split()

            # Ensure there are exactly two numbers in the line
            if len(numbers) == 2:
                follower = f"user{numbers[0]}"
                following = f"user{numbers[1]}"

                # Add to following_list of follower and followers_list of following
                if follower in user_dict and following in user_dict:
                    user_dict[follower]["following_list"].append(following)
                    user_dict[following]["followers_list"].append(follower)

    # Ensure every other user follows the main user
    if file_number:
        main_username = f"user{file_number}"
        for username in user_dict:
            if username != main_username:
                user_dict[username]["following_list"].append(main_username)
                user_dict[main_username]["followers_list"].append(username)

    # Add random interactions for users that follow each other
    for user in user_dict.values():
        for other_user in user["following_list"]:
            # Generate interactions even if not mutual
            if other_user not in user["interactions"]:
                user["interactions"][other_user] = {"likes": 0, "comments": 0, "reposts": 0}

            # Randomly generate interaction counts
            user["interactions"][other_user]["likes"] += random.randint(0, 1000)
            user["interactions"][other_user]["comments"] += random.randint(0, 1000)
            user["interactions"][other_user]["reposts"] += random.randint(0, 1000)

    # Randomly assign top 5 hashtags for each user
    hashtags_pool = ['#fun', '#tech', '#music', '#art', '#travel', '#sports', '#food', '#fashion', '#gaming', '#fitness']
    for user in user_dict.values():
        # Randomly choose 5 hashtags
        user["hashtags"] = random.sample(hashtags_pool, 5)

    # Write the JSON collection to the output file
    with open(output_file, 'w') as output:
        json.dump(list(user_dict.values()), output, indent=4)

# Specify the input text file and output JSON file
input_file = "0.edges"  # Replace with your text file name
output_file = "0network.json"  # Replace with your desired JSON file name

# Call the function to create the JSON collection
create_json_collection(input_file, output_file)

print(f"JSON collection has been created and saved to {output_file}.")
