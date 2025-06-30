import pandas as pd 
import numpy as np

if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test
  
@transformer
def transform(df: pd.DataFrame, *args, **kwargs):
    """
    Template code for a transformer block.

    Add more parameters to this function if this block has multiple parent blocks.
    There should be one parameter for each output variable from each parent block.

    Args:
        data: The output from the upstream parent block
        args: The output from any additional upstream blocks (if applicable)

    Returns:
        Anything (e.g. data frame, dictionary, array, int, str, etc.)
    """
    # Specify your transformation logic here
    df.drop_duplicates(inplace=True)
    df.reset_index(drop=True, inplace=True)
    df['trip_id'] = df.index + 1 # A surrogate Key 
    # Reorder columns to move 'trip_id' to the front
    cols = df.columns.tolist()
    cols.remove('trip_id')
    df = df[['trip_id'] + cols]
    df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])
    ## Building the date_dim, vendor_dim, passenger_count_dim, ratecode_dim, payment_dim, pick_up_location_dim, dropoff_location_dim
    # This will create the dimension tables for the star schema

    date_dim = df[['tpep_pickup_datetime', 'tpep_dropoff_datetime']].reset_index(drop=True)
    date_dim['pickup_year'] = date_dim['tpep_pickup_datetime'].dt.year  
    date_dim['pickup_month'] = date_dim['tpep_pickup_datetime'].dt.month
    date_dim['pickup_weekday'] = date_dim['tpep_pickup_datetime'].dt.weekday
    date_dim['pickup_day'] = date_dim['tpep_pickup_datetime'].dt.day
    date_dim['pickup_hour'] = date_dim['tpep_pickup_datetime'].dt.hour
    date_dim['dropoff_year'] = date_dim['tpep_dropoff_datetime'].dt.year
    date_dim['dropoff_month'] = date_dim['tpep_dropoff_datetime'].dt.month
    date_dim['dropoff_weekday'] = date_dim['tpep_dropoff_datetime'].dt.weekday
    date_dim['dropoff_day'] = date_dim['tpep_dropoff_datetime'].dt.day
    date_dim['dropoff_hour'] = date_dim['tpep_dropoff_datetime'].dt.hour

    date_dim['datetime_id'] = date_dim.index + 1
    date_dim = date_dim[['datetime_id', 'tpep_pickup_datetime', 'tpep_dropoff_datetime', 
                        'pickup_year', 'pickup_month', 'pickup_weekday', 'pickup_day', 'pickup_hour',
                        'dropoff_year', 'dropoff_month', 'dropoff_weekday', 'dropoff_day', 'dropoff_hour']]
    ## vendor_dim
    vendor_dim = df[['VendorID']].drop_duplicates().reset_index(drop=True)
    vendor_dim['vendor_id'] = vendor_dim.index + 1
    vendor_dim['vendor_name'] = np.where(vendor_dim['VendorID'] == 1, 'Creative Mobile Technologies, LLC', 'VeriFone Inc.')
    vendor_dim = vendor_dim[['vendor_id', 'VendorID', 'vendor_name']]
    passenger_count_dim = df[['passenger_count']].drop_duplicates().reset_index(drop=True)
    passenger_count_dim['passenger_count_id'] = passenger_count_dim.index + 1
    passenger_count_dim = passenger_count_dim[['passenger_count_id','passenger_count']]
    rate_code_type = {
            1:"Standard rate",
            2:"JFK",
            3:"Newark",
            4:"Nassau or Westchester",
            5:"Negotiated fare",
            6:"Group ride"
    }

    rate_code_dim = df[['RatecodeID']].drop_duplicates().reset_index(drop=True)
    rate_code_dim['ratecode_id'] = rate_code_dim.index + 1
    rate_code_dim['rate_code_name'] = rate_code_dim['RatecodeID'].map(rate_code_type)
    rate_code_dim = rate_code_dim[['ratecode_id','RatecodeID','rate_code_name']]
    payment_type_name = {
            1:"Credit card",
            2:"Cash",
            3:"No charge",
            4:"Dispute",
            5:"Unknown",
            6:"Voided trip"
    }
    payment_type_dim = df[['payment_type']].drop_duplicates().reset_index(drop=True)
    payment_type_dim["payment_type_id"] = payment_type_dim.index + 1
    payment_type_dim['payment_type_name'] = payment_type_dim['payment_type'].map(payment_type_name)
    payment_type_dim = payment_type_dim[["payment_type_id",'payment_type','payment_type_name']]

    pickup_location_dim = df[['pickup_longitude', 'pickup_latitude']].drop_duplicates().reset_index(drop=True)
    pickup_location_dim['pickup_location_id'] = pickup_location_dim.index + 1
    pickup_location_dim = pickup_location_dim[['pickup_location_id','pickup_latitude','pickup_longitude']] 


    dropoff_location_dim = df[['dropoff_longitude', 'dropoff_latitude']].drop_duplicates().reset_index(drop=True)
    dropoff_location_dim['dropoff_location_id'] = dropoff_location_dim.index + 1
    dropoff_location_dim = dropoff_location_dim[['dropoff_location_id','dropoff_latitude','dropoff_longitude']]
    ## Now let's build the fact table

    fact_table = df.merge(date_dim, how='left', left_on='trip_id', right_on='datetime_id')\
                .merge(vendor_dim, how='left', on='VendorID')\
                .merge(passenger_count_dim, how='left', on='passenger_count')\
                .merge(rate_code_dim, how='left', on='RatecodeID')\
                .merge(payment_type_dim, how='left', on='payment_type')\
                .merge(pickup_location_dim, on=['pickup_longitude', 'pickup_latitude'], how='left')\
                .merge(dropoff_location_dim, on=['dropoff_longitude', 'dropoff_latitude'], how='left')
    fact_table = fact_table[['trip_id', 'VendorID', 'datetime_id', 'passenger_count_id',
               'ratecode_id', 'payment_type_id', 'pickup_location_id', 
               'dropoff_location_id', 'store_and_fwd_flag', 'trip_distance',
               'fare_amount', 'extra', 'mta_tax', 'tip_amount', 'tolls_amount',
               'improvement_surcharge', 'total_amount']]  
    return {"datetime_dim":date_dim.to_dict(orient="dict"),
    "passenger_count_dim":passenger_count_dim.to_dict(orient="dict"),
    "vendor_dim":vendor_dim.to_dict(orient="dict"),
    "rate_code_dim":rate_code_dim.to_dict(orient="dict"),
    "pickup_location_dim":pickup_location_dim.to_dict(orient="dict"),
    "dropoff_location_dim":dropoff_location_dim.to_dict(orient="dict"),
    "payment_type_dim":payment_type_dim.to_dict(orient="dict"),
    "fact_table":fact_table.to_dict(orient="dict")}




@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    print(type(output))
    assert output is not None, 'The output is undefined'