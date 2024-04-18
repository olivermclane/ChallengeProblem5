"""
Author: Oliver McLane
Date: 2024-04-17
This file allows you to split csv data into multiple different csv called Team.csv and Institutions.csv, it uses a fuzzy-match
based algorithm that matches together different universities together. You are prompted to either enter a csv path, test with the
preset file or quit the CLI tool.
"""
import pandas as pd
from fuzzywuzzy import process, fuzz

# Define a dictionary to convert US state abbreviations to full names
state_abbreviations = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming"
}


def fuzzy_grouping(dataframe, column_name, threshold=87):
    # Extract unique institution names
    names = dataframe[column_name].unique()
    # Dictionary to hold the mapping from original to grouped name
    grouped_names = {}

    # Iterate through each name
    for name in names:
        if grouped_names:
            # Check for fuzzy match in already grouped names
            match, score = process.extractOne(name, list(grouped_names.keys()), scorer=fuzz.token_sort_ratio)
            if score > threshold:
                # If a close match is found above threshold, group it under the matched name
                grouped_names[name] = grouped_names[match]
            else:
                # Otherwise, group it under itself
                grouped_names[name] = name
        else:
            # Initialize with the first name if empty
            grouped_names[name] = name

    # Apply the grouping to the original dataframe column
    dataframe['Grouped Institution'] = dataframe[column_name].map(grouped_names)
    return dataframe


def save_csv(file_path):
    # Try to load the data from the CSV file
    try:
        # Load the data from the CSV file
        data_2015 = pd.read_csv(file_path)
    except Exception as e:
        print(f"Failed to load data: {e}")
        return

    # Check for the required headers in the CSV
    required_columns = {'Institution', 'City', 'State/Province', 'Country', 'Team Number', 'Advisor', 'Problem',
                        'Ranking'}
    if not required_columns.issubset(data_2015.columns):
        missing_columns = required_columns - set(data_2015.columns)
        print(f"Missing required columns: {missing_columns}")
        return

    # Apply fuzzy grouping to the institution names
    data_2015 = fuzzy_grouping(data_2015, 'Institution')

    # Replace nulls in 'State/Province' with 'Unknown'
    data_2015.loc[:, 'State/Province'] = data_2015['State/Province'].fillna('Unknown')

    for column in data_2015.columns:
        if data_2015[column].dtype == object and column != 'Country':
            if column == 'State/Province':
                # Convert 2-letter abbreviations to full names
                data_2015[column] = data_2015[column].str.strip().apply(
                    lambda x: state_abbreviations[x.upper()] if x.upper() in state_abbreviations and len(x) == 2 else x)
            else:
                # Capitalize other columns
                data_2015[column] = data_2015[column].str.strip().str.capitalize()

    # Creating a unique list of institutions
    institutions = data_2015[['Grouped Institution', 'City', 'State/Province', 'Country']].drop_duplicates(
        subset=['Grouped Institution'])
    institutions.reset_index(drop=True, inplace=True)
    institutions.index.name = 'Institution ID'
    institutions.reset_index(inplace=True)
    institutions.columns = ['Institution ID', 'Institution Name', 'City', 'State/Province', 'Country']

    # Save the Institutions CSV file
    institutions_path = 'results/Institutions.csv'
    institutions.to_csv(institutions_path, index=False)

    # Merging team data with institutions to get the correct Institution ID
    team_details_correct = data_2015[['Team Number', 'Advisor', 'Problem', 'Ranking', 'Institution']].copy()
    team_details_correct = team_details_correct.merge(institutions[['Institution Name', 'Institution ID']],
                                                      left_on='Institution', right_on='Institution Name', how='left')
    team_details_correct.drop('Institution Name', axis=1, inplace=True)

    # Save the Teams CSV file
    teams_path = 'results/Teams.csv'
    team_details_correct.to_csv(teams_path, index=False)

    print("Files saved:", institutions_path, teams_path)


def main():
    end_flag = False
    while not end_flag:
        file_location = input(
            "Enter the location of the csv to split, (1) for the test file (2015.csv), and (2) for exit: ")
        if file_location == "1":
            file_path = 'data/2015.csv'
            save_csv(file_path)
            end_flag = True
        elif file_location == "2":
            print("Quitting...")
            end_flag = True
        else:
            file_path = file_location
            save_csv(file_path)


if __name__ == '__main__':
    main()
