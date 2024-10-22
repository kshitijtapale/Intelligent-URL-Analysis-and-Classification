import pickle

# Replace 'file_path.pkl' with the path to your .pkl file
file_path = 'app/Test/feature_selector.pkl'

# Open the file in read-binary mode and load the data
with open(file_path, 'rb') as file:
    data = pickle.load(file)

# Print the content of the .pkl file
print(data)
