import joblib

# Load the preprocessor
preprocessor = joblib.load('app\Test\Test_npy')

# Check the type of the preprocessor
print(type(preprocessor))
