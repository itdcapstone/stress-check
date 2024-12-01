import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, classification_report
from imblearn.over_sampling import SMOTE
import numpy as np
import warnings
import pickle
import os

# Suppress warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Set a random seed for reproducibility
random_seed = 42

csv_file_path = 'data.csv'  
df = pd.read_csv(csv_file_path, encoding='utf-8-sig')

# Clean up column names by stripping unwanted spaces or newline characters
df.columns = df.columns.str.strip().str.replace('\n', '', regex=True)

relevant_columns = [
    'Sadness', 'Anxious', 'Peer Pressure', 'Sleep Quality', 'AI Tools', 'Family Stress',
    'Financial Satisfaction', 'Friends Support', 'Resources Access', 'Home Stress',
    'Commute Stress', 'Noise Level', 'Weather Conditions', 'Program Confidence',
    'Academic Stress', 'Advisor Support', 'Stress Level'
]
df = df[relevant_columns]

# Mapping categorical features to numeric values
mappings = {
    'Sadness': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5},
    'Anxious': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5},
    'Peer Pressure': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5},
    'Sleep Quality': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5},
    'AI Tools': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5},
    'Family Stress': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5},
    'Financial Satisfaction': {'Very Satisfied': 1, 'Satisfied': 2, 'Neutral': 3, 'Dissatisfied': 4, 'Very Dissatisfied': 5},
    'Friends Support': {'Strongly Agree': 1, 'Agree': 2, 'Neutral': 3, 'Disagree': 4, 'Strongly Disagree': 5},
    'Resources Access': {'Excellent': 1, 'Good': 2, 'Adequate': 3, 'Poor': 4, 'Very Poor': 5},
    'Home Stress': {'Strongly Disagree': 1, 'Disagree': 2, 'Neutral': 3, 'Agree': 4, 'Strongly Agree': 5},
    'Commute Stress': {'Not at all': 1, 'A little': 2, 'Moderately': 3, 'Significantly': 4, 'Extremely': 5},
    'Noise Level': {'Very Manageable': 1, 'Manageable': 2, 'Neutral': 3, 'Disturbing': 4, 'Very Disturbing': 5},
    'Weather Conditions': {'Strongly Disagree': 1, 'Disagree': 2, 'Neutral': 3, 'Agree': 4, 'Strongly Agree': 5},
    'Program Confidence': {'Yes': 1, 'No': 5},
    'Academic Stress': {'Not at all': 1, 'A little': 2, 'Moderately': 3, 'Significantly': 4, 'Extremely': 5},
    'Advisor Support': {'Completely': 1, 'Very Much': 2, 'Moderately': 3, 'Somewhat': 4, 'Not at all': 5}
}

# Replace categorical features with numeric mappings
df.replace(mappings, inplace=True)

# Mapping 'Stress Level' column to numeric values
stress_level_mapping = {
    'Not at all': 1,
    'A little': 2,
    'Moderately': 3,
    'Significantly': 4,
    'Extremely': 5
}
df['Stress Level'].replace(stress_level_mapping, inplace=True)

# Define target and features
y = df['Stress Level'].astype(int)  # Target
X = df.drop('Stress Level', axis=1)

# Convert all categorical columns to strings before applying OneHotEncoder
categorical_columns = X.select_dtypes(include=['object']).columns
X[categorical_columns] = X[categorical_columns].astype(str)

# Feature engineering: Identify numeric and categorical features
numeric_features = X.select_dtypes(include=['int64', 'float64']).columns
categorical_features = X.select_dtypes(include=['object']).columns

# Transformers for numeric and categorical features
numeric_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

# Preprocessor with ColumnTransformer
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ])

# Preprocess the data
X_preprocessed = preprocessor.fit_transform(X)

# Handle class imbalance using SMOTE
min_class_size = y.value_counts().min()
k_neighbors = max(1, min(4, min_class_size - 1))

if min_class_size > 1:
    smote = SMOTE(random_state=random_seed, k_neighbors=k_neighbors)
    X_res, y_res = smote.fit_resample(X_preprocessed, y)
else:
    X_res, y_res = X_preprocessed, y

# Build and tune the KNN model using GridSearchCV
knn = KNeighborsClassifier()
cv = StratifiedKFold(n_splits=min(5, min_class_size), shuffle=True, random_state=random_seed)

param_grid = {
    'n_neighbors': list(range(1, 31)),
    'metric': ['euclidean', 'manhattan', 'minkowski', 'cosine'],
    'weights': ['uniform', 'distance']
}

grid_search_knn = GridSearchCV(knn, param_grid, cv=cv, scoring='accuracy', n_jobs=-1)
grid_search_knn.fit(X_res, y_res)

# Retrieve the best model
best_knn_model = grid_search_knn.best_estimator_

# Evaluate the model using cross-validation
y_pred = cross_val_predict(best_knn_model, X_res, y_res, cv=cv)
accuracy = accuracy_score(y_res, y_pred)
print(f"Best Parameters: {grid_search_knn.best_params_}")
print(f"Cross-validated Accuracy: {accuracy:.4f}")
print(f"Classification Report:\n{classification_report(y_res, y_pred)}") 

conf_matrix = confusion_matrix(y_res, y_pred)

# Display the confusion matrix
disp = ConfusionMatrixDisplay(conf_matrix, display_labels=best_knn_model.classes_)
disp.plot(cmap='viridis')  # Choose a color map, e.g., 'viridis'
plt.title("Confusion Matrix")
plt.show()



# Save the model and preprocessor
os.makedirs('models', exist_ok=True)

with open('models/knn_model.pkl', 'wb') as model_file:
    pickle.dump(best_knn_model, model_file)

with open('models/preprocessor.pkl', 'wb') as preprocessor_file:
    pickle.dump(preprocessor, preprocessor_file)

print("Model and preprocessor have been saved.")


def predict_stress(new_student_data):
    # Convert new student data to DataFrame
    new_student_df = pd.DataFrame(new_student_data)

    # Preprocess the new student's data
    new_student_transformed = preprocessor.transform(new_student_df)

    # Predict the stress level
    predicted_stress_level = best_knn_model.predict(new_student_transformed)

    return predicted_stress_level[0]

# Function for identifying stressors and providing details
def identify_common_stressors(new_student_data):
    # Define the stressor categories and their related columns
    stressor_categories = {
        'Psychological Stressors': {
            'Sadness or depression about workload': 'Sadness',
            'Anxiety about performance': 'Anxious',
            'Peer pressure': 'Peer Pressure',
            'Sleep issues': 'Sleep Quality'
        },
        'Socio-economic Stressors': {
            'Financial dissatisfaction': 'Financial Satisfaction',
            'Family conflicts': 'Family Stress',
            'Lack of social support from friends': 'Friends Support',
            'Access to academic resources': 'Resources Access'
        },
        'Environmental Stressors': {
            'Stress due to poor rest at home': 'Home Stress',
            'Long commutes': 'Commute Stress',
            'Noise levels during study hours': 'Noise Level',
            'Extreme weather conditions': 'Weather Conditions'
        },
        'Academic Stressors': {
            'Stress about exams, assignments, and deadlines': 'Academic Stress',
            'Lack of support from advisors or mentors': 'Advisor Support',
            'Confidence in program choice': 'Program Confidence'
        }
    }

    # Function to check if the stressor response indicates high stress (4: 'Often' or 5: 'Always')
    def is_high_stress(val):
        return val in [4, 5]

    # Initialize the dictionary to store stressor counts and details
    high_stressors = {}

    # Iterate over each category and its stressors
    for category, stressors in stressor_categories.items():
        # Initialize count and details for each category
        high_stressors[category] = {
            'count': 0,
            'details': {}
        }
        
        # Iterate over each stressor in the category
        for stressor, column in stressors.items():
            response = new_student_data.get(column, [0])[0]  # Get response, default to 0 if not present
            if is_high_stress(response):
                # Increment the count of high stressors for the category
                high_stressors[category]['count'] += 1
                # Add the specific stressor and its response to the details
                high_stressors[category]['details'][stressor] = response

    # Output the count and details of high stressors per category
    return high_stressors

    


