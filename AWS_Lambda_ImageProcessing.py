import boto3
import pandas as pd
import io
import re
import requests
import json

def lambda_handler(event, context):
    # S3 bucket and object details
    bucket_name = "huggingfacedataset"
    object_key = "worldfoodimages-dataset/dataset.parquet"
    
    # Initialize S3 client
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    try:
        # Download Parquet file from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        parquet_data = response['Body'].read()
        
        # Load the Parquet data into a pandas DataFrame
        food = pd.read_parquet(io.BytesIO(parquet_data))
        
        # Process the DataFrame
        #print("Columns in the dataset:", food.columns.tolist())
        #print(food)
            
    except Exception as e:
        print(f"Error reading Parquet file from S3: {e}")
        raise e

    image_url=[]
    new_image_url=[]
    Category=[]
    for row in range(min(20, len(food))):
        try:
            new_image_url = food.loc[row,"image1_url"]
            new_image_url = re.sub(r"\?.*$", "",new_image_url)
            headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
                        }    
            response = requests.get(new_image_url, headers=headers, stream=True)
            image_url.append(new_image_url)
            #print(image_url)
            #image_url = Image.open(io.BytesIO(response.content)).convert("RGB")
            Category.append({
                "category": str(food.loc[row, "coarse_categories"])
               
            })
       
        except Exception as e:
            print(f"Error fetching or displaying image at row {row}: {e}")
   
    # Convert any NumPy objects to lists for JSON serialization
   
    #image_url = list(image_url)  # Convert to list if it's an ndarray
    print(image_url)
    #Category = pd.DataFrame(Category).to_dict(orient='records') 
    print(Category)
    image_category = {
        "image_url": image_url,
        "category": Category
    }
  
    lambda_response=lambda_client.invoke(
        FunctionName='arn:aws:lambda:us-east-2:307946638225:function:lsg_foodimages',
        InvocationType='Event',
        Payload=json.dumps(image_category)

    )
    print("Lambda invoke response:", lambda_response)
    print('\n')

