import pandas as pd
import random
from faker import Faker

fake = Faker()

# Number of users to generate
num_users = 30

# Generate unique usernames
usernames = [fake.user_name() for _ in range(num_users)]

# Initialize dictionaries to store followers and following lists for each user
followers_dict = {username: set() for username in usernames}
following_dict = {username: set() for username in usernames}

# Create follower and following relationships with bidirectional consistency
for username in usernames:
    follower_count = random.randint(1, min(50, num_users - 1))
    # Randomly select followers for the user
    follower_list = random.sample([user for user in usernames if user != username], follower_count)
    
    for follower in follower_list:
        # Add each follower to the user's follower list and ensure mutual following in the following list
        followers_dict[username].add(follower)
        following_dict[follower].add(username)

# Function to generate random interaction counts
def generate_interactions():
    return {
        'likes': random.randint(0, 100),      # Likes 
        'comments': random.randint(0, 50),    # Comments 
        'shares': random.randint(0, 30)       # Shares 
    }

# Initialize a list to store weighted edges
weighted_edges = []

# Convert sets to lists and prepare data for DataFrame
data = []
for username in usernames:
    interactions = generate_interactions()
    user_data = {
        'Username': username,
        'Email': fake.email(),  # Generate a fake email
        'Password': username,  # Generate a fake password
        'Account Type': random.choice(['influencer', 'business_analyst']),  # Randomly assign account type
        'Follower Count': len(followers_dict[username]),
        'Follower List': list(followers_dict[username]),
        'Following Count': len(following_dict[username]),
        'Following List': list(following_dict[username]),
        'Likes': interactions['likes'],
        'Comments': interactions['comments'],
        'Shares': interactions['shares']
    }
    data.append(user_data)
    
    # Calculate weights for edges based on interactions
    for follower in followers_dict[username]:
        # Randomize follower interactions for each connection
        follower_interactions = generate_interactions()
        
        # Define weight as a combination of interactions, e.g., more weight on likes/comments/shares
        weight = follower_interactions['likes'] * 0.5 + follower_interactions['comments'] * 0.3 + follower_interactions['shares'] * 0.2
        
        # Append edge with calculated weight to the weighted_edges list
        weighted_edges.append({
            'User': username,
            'Follower': follower,
            'Likes': follower_interactions['likes'],
            'Comments': follower_interactions['comments'],
            'Shares': follower_interactions['shares'],
        })

# Create DataFrames and save to CSV
df_users = pd.DataFrame(data)
df_users.to_csv('fake_social_network_data.csv', index=False)

df_edges = pd.DataFrame(weighted_edges)
df_edges.to_csv('fake_social_network_edges.csv', index=False)

print("Data saved to fake_social_network_data.csv and fake_social_network_edges.csv")
