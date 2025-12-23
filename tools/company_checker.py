from name_matching.name_matcher import NameMatcher
import pandas as pd
from smolagents import Tool


class CompanyNameChecker(Tool):
    name = "com_check_tool"
    description = "Takes two company names, cleans them, and returns a number that scores how closely the cleaned names match."
    inputs = {"company_name_one": {"type": "string", "description": "first company name to be compared"},"company_name_two": {"type": "string", "description": "second company name to be compared"}}
    output_type = "integer"

    def forward(self,company_name_one: str,company_name_two:str) -> int:
        df_companies_a = pd.DataFrame({'Company name': [company_name_one]})
        df_companies_b = pd.DataFrame({'name': [company_name_two]})
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

        return int(combined.loc[0,"score"])