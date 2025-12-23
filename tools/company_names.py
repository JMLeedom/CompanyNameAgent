from name_matching.name_matcher import NameMatcher
import pandas as pd
from smolagents import Tool


class CompanyNameMatcher(Tool):
    name = "company_tool"
    description = " Takes a misspelled or altered company name, cleans the name, and determines if the cleaned name matches any official company name in a database"
    inputs = {"company_name": {"type": "string", "description": "Name of company to be checked in database"}}
    output_type = "string"

    def forward(self,company_name: str) -> str:
            # define a dataset with bank names
        df_companies_a = pd.DataFrame({'Company name': [
            'Industrial and Commercial Bank of China Limited',
            'China Construction Bank',
            'Agricultural Bank of China',
            'Bank of China',
            'JPMorgan Chase',
            'Mitsubishi UFJ Financial Group',
            'Bank of America',
            'HSBC',
            'BNP Paribas',
            'Crédit Agricole']})
        df_companies_b = pd.DataFrame({'name': [company_name]})
        # initialise the name matcher
        matcher = NameMatcher(number_of_matches=1, 
                      legal_suffixes=True, 
                      common_words=False, 
                      top_n=50, 
                      verbose=False)
        # adjust the distance metrics to use 
        matcher.set_distance_metrics(['discounted_levenshtein','SSK','fuzzy_wuzzy_token_sort'])
        #matcher.set_distance_metrics(['bag', 'typo', 'refined_soundex'])

        # load the data to which the names should be matched
        matcher.load_and_process_master_data(column='Company name',
                                     df_matching_data=df_companies_a, 
                                     transform=True)
        # perform the name matching on the data you want matched
        matches = matcher.match_names(to_be_matched=df_companies_b, 
                              column_matching='name')

        # combine the datasets based on the matches
        combined = pd.merge(df_companies_a, matches, how='left', left_index=True, right_on='match_index')
        combined = pd.merge(combined, df_companies_b, how='left', left_index=True, right_index=True)

        potential_match = combined.loc[0,"Company name"]
        percent_match = int(combined.loc[0,"score"])

        return f"The closest match in the database is {potential_match} with a match percentage of {percent_match}"