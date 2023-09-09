"""
    This script contains all the required functions for feature engineering required for this project
"""

# Importing nessecary libararies and packages
import pandas as pd
import numpy as np

# Main function: Feature Engineer
def feature_engineereing(_df:pd.DataFrame)->pd.DataFrame:
    """
        Used to create all defined possible engineering steps in the data.

        PARAMETERS
            _df: pandas dataframe, input dataframe.

        RETURN
            pandas DataFrame with created features.
    """

    # Create a copy of input dataframe
    df = _df.copy()

    # Convert to datetime
    df['Dt_Customer'] = pd.to_datetime(df['Dt_Customer'])

    # Customer Age
    df['Customer_Age'] = df['Dt_Customer'].dt.year - df['Year_Birth']

    # Total Spending

    # List of columns representing spending on different product categories
    product_columns = ['MntWines', 'MntFruits', 'MntMeatProducts', 'MntFishProducts', 'MntSweetProducts', 'MntGoldProds']

    # Calculate the total spending for each customer
    df['Total_Spending'] = df[product_columns].sum(axis=1)

    # Total Purchases

    # List of columns representing spending on different purchases channels
    channels_columns = ['NumWebPurchases', 'NumCatalogPurchases', 'NumStorePurchases']
                    
    # Calculate the total spending for each customer
    df['Total_Purchases'] = df[channels_columns].sum(axis=1)

    # Acceptance_Rate

    # List of columns representing accepted campaigns (Cmp1 to Cmp5)
    accepted_campaign_columns = ['AcceptedCmp1', 'AcceptedCmp2', 'AcceptedCmp3', 'AcceptedCmp4', 'AcceptedCmp5']

    # Calculate the total number of accepted campaigns for each customer
    df['Total_Accepted_Campaigns'] = df[accepted_campaign_columns].sum(axis=1)

    # Total number of marketing campaigns
    total_campaigns = len(accepted_campaign_columns)

    # Calculate the acceptance rate for each customer
    df['Acceptance_Rate'] = df['Total_Accepted_Campaigns'] / total_campaigns

    # Channel_Preference

    # Define the purchase channels
    channels = {
        'NumWebPurchases':'Web',
        'NumStorePurchases':'Store',
        'NumCatalogPurchases':'Catalog'
    }

    # Create a new column 'Channel_Preference' with the preferred channel for each customer
    df['Channel_Preference'] = df[['NumWebPurchases', 'NumStorePurchases', 'NumCatalogPurchases']].idxmax(axis=1)
    df['Channel_Preference'] = df['Channel_Preference'].replace(channels)

    # Avg_purchase_Amount

    # List of columns representing spending on different product categories
    product_columns = ['MntWines', 'MntFruits', 'MntMeatProducts', 'MntFishProducts', 'MntSweetProducts', 'MntGoldProds']

    # Calculate the total spending for each customer
    df['Total_Spending'] = df[product_columns].sum(axis=1)

    # List of columns representing the number of purchases in different channels
    purchase_columns = ['NumWebPurchases', 'NumStorePurchases', 'NumCatalogPurchases']

    # Calculate the total number of purchases for each customer
    df['Total_Purchases'] = df[purchase_columns].sum(axis=1)

    # Campaign_Engagement

    # Based on the EDA analysis in the previous notebook, it was shown that the most used compaing in descending orders are:
    campaigns = ['AcceptedCmp3', 'AcceptedCmp4', 'AcceptedCmp5', 'AcceptedCmp1', 'AcceptedCmp2']

    # Let's assume the weights Importance of each Campaing based on the most used campaign
    campaign_weights = [0.5, 0.4, 0.3, 0.2, 0.1]

    # Calculate the total campaign engagement for each customer
    df['Campaign_Engagement'] = (df[campaigns] * campaign_weights).sum(axis=1)

    # Num_Children
    df['Num_Children'] = df['Kidhome'] + df['Teenhome']

    df['Living_With'] = df["Marital_Status"].replace({
        "Married":"Partner", 
        "Together":"Partner", 
        "Absurd":"Alone", 
        "Widow":"Alone", 
        "YOLO":"Alone", 
        "Divorced":"Alone", 
        "Single":"Alone",})

    df["Education"]= df["Education"].replace({
        "Basic":"Undergraduate",
        "2n Cycle":"Undergraduate", 
        "Graduation":"Graduate", 
        "Master":"Postgraduate", 
        "PhD":"Postgraduate"})

    # Family_Size
    df['Family_Size'] = df['Living_With'].replace({'Alone':1, 'Partner':2}) + df['Num_Children']

    return df


