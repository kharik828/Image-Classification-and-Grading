import boto3
#    Using Google Gemini LLM
import numpy as np
import vertexai
from vertexai.generative_models import GenerativeModel, Part
#from vertexai.generation_config import GenerationConfig  
import requests
from PIL import Image
#import matplotlib.pyplot as plt
import io
import re
import json
import os
import ast
from botocore.exceptions import ClientError
import time
import random

def exponential_backoff_retry(func, max_retries=5, base_delay=1, backoff_multiplier=2, jitter=True):
    """
    Retry logic with exponential backoff.
    """
    delay = base_delay
    for attempt in range(max_retries):
        try:
            return func()  # Attempt the function
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise e  # Raise exception after all retries
            time.sleep(delay + (random.uniform(0, delay) if jitter else 0))
            delay *= backoff_multiplier  # Increase delay

# Wrap model call with exponential backoff
def generate_content_with_retry(model, image_uri, prompt, max_retries=5):
    def call_model():
        return model.generate_content([
            Part.from_uri(
                image_uri,
                mime_type="image/jpeg",
            ),
            prompt,
        ])
    return exponential_backoff_retry(call_model, max_retries=max_retries)

def fetch_service_account_key():
    s3_client = boto3.client('s3')
    bucket_name = "huggingfacedataset"  # Replace with your bucket name
    key_name = "YOUR GOOGLE GEMINI API KEY FILE.JSON"  # Replace with the key path

    # Download the file from S3 and save it to /tmp
    local_path = "/tmp/YOUR GOOGLE GEMINI API KEY FILE.JSON"
    s3_client.download_file(bucket_name, key_name, local_path)
    return local_path
# --------------- Main handler ------------------

def lambda_handler(event, context):
    
    #This Lambda function processes the payload sent by another Lambda function.
    s3_client = boto3.client('s3')
    try:
        # Parse the incoming event payload
        print("Received event:", event)
        # If the event is JSON stringified, parse it into a dictionary
        if isinstance(event, str):
            event = json.loads(event)
       
        # Access the image URLs and categories from the event payload
        image_urls = event.get("image_url", [])
        categories = event.get("category", [])
  
        # Set the path to the service account key file
        service_account_key_path = fetch_service_account_key()
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_key_path
        ## TDO(developer): Update and un-comment below line
        PROJECT_ID = "YOUR GOOGLE GEMINI PROJECT NAME"
        vertexai.init(project=PROJECT_ID, location="us-central1")
        # Set the generation configuration with the desired temperature
        model_config = {
            "temperature":0.1,  # Set temperature value (adjust between 0 and 1)
            "max_output_tokens":1000,  # Optionally, set the maximum number of output tokens
        }
        model = GenerativeModel("gemini-1.5-pro-002", generation_config=model_config)
        # Define a custom User-Agent header
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        
        AllImages_reponses={}
        for row in range(min(20,len(image_urls))):
            try:
                
                response = requests.get(image_urls[row],headers=headers, stream=True)
                response.raise_for_status()

                # Verify the content type
                content_type = response.headers.get("Content-Type", "")
                if "image" not in content_type:
                    raise ValueError(f"URL does not point to a valid image. Content-Type: {content_type}")
                
                #image_url = Image.open(io.BytesIO(response.content)).convert("RGB")
                # Display the image
                print(f"Processing image at index {row}: {image_urls[row]}")
                #plt.figure()  # Create a new figure for each image
                #plt.imshow(image_url)
                #plt.title(f"Image {index + 1}")  # Title for the image
                #plt.axis("off")  # Turn off axis labels
                #plt.show()

                category= ['soup' 'stew' 'meat' 'rice' 'bread' 'dessert' 'pancake' 'dim sum' 'dough'
                    'snack' 'fish' 'vegetable' 'seafood' 'fruit' 'chicken' 'beverages'
                    'side dish' 'dumpling' 'lamb' 'sweets' 'fritter' 'noodle' 'rice cake'
                    'cereal' 'curry' 'canned food' 'pastry' 'cake' 'pasta' 'salad'
                    'finger food' 'vegetables' 'cutlet' 'potato' 'crepe' 'doughnut' 'pudding'
                    'skewer' 'wrap' 'tofu' 'soybeans' 'stir fry' 'corn' 'egg' 'beans'
                    'biscuit' 'cookies' 'roll' 'pizza' 'sandwich' 'confectionery' 'condiment'
                    'dairy' 'grain' 'porridge' 'cheese' 'banana' 'casserole' 'spice' 'seed'
                    'meatball' 'dip' 'stuffed food' 'omelette' 'seaweed' 'butter' 'stock'
                    'hot pot' 'sweet paste' 'sugar' 'candy' 'jelly' 'sweetener' 'spread'
                    'tortilla' 'platter' 'lentil' 'pie' 'gravy' 'nuts' 'peas' 'sausage'
                    'mutton' 'caviar' 'sauce' 'flatbread' 'carrot' 'paste'
                ]

                prompt = f"""You are tasked with analyzing an image of a food dish after a customer has finished eating. Your objective is to:

                    Classify the food in the dish: Based on the image, identify and classify the dish into upto two major categories from the following list: {categories}. Each category is enclosed in quotes (e.g., 'soup' and 'stew'). Only the categories listed are allowed. No other categories should be included in the response.

                    Estimate the remaining food: Based on the all the visible cooked and uncooked food in the image, estimate the percentage of food remaining in the dish, which will be referred to as 'food %'.
                    Consider the quantities within the container or dish or plate or bowl with food and not the entire image to estimage the quantities.
                    Food can be more than just the above identified category. Follow these guidelines:

                    100%: The dish appears to be fully filled with all the food items (or the food fills the entire visible portion of the dish).
                    0%: No food from all the identified categories remains visible in the dish (the plate or dish is mostly empty).
                    Intermediate values (e.g., 10%, 50%, 80%): If there is some food remaining but not a full portion, estimate the visible food portion based on how much is left compared to a full dish. For example:
                    50% would mean the food items occupies about half of the dish.
                    10% would indicate that a very small amount of food of any category is remaining in the dish or plate or bowl.
                    90% would indicate that majority of the dish is filled with food of any category with only some portion of the fully filled dish was eaten.
                    
                    You can provide values in increments that best reflect the visible quantity of all food items in the dish. Make sure the sum of filled and unfilled % of dish in the image add up to 100%.
                    
                """
                response1 = generate_content_with_retry(model, image_urls[row], prompt)

                print(response1.text)
                #actual_category = ast.literal_eval(categories[str(row)])
                print(f'Actual Category is: {categories[row]} ')
        
                # Create the JSON object
                AllImages_reponses[row] = {
                    "image_url":image_urls[row],
                    "analysis_result": response1.text,
                    "actual_category": categories[row]
                }
                
          
                
              
            except Exception as e:
                print(f"Error fetching or displaying image at row {row}: {e}")
                    
                    # Ensure response cleanup
                    #finally:
                    #    if response1:
                    #        print("Processed successfully:", response1.text)

            response_json = json.dumps(AllImages_reponses,indent=4)
                    
            # Define S3 bucket and object key
            bucket_name = "foodimagegrade"
            object_key = f"lambda-responses_20241202/AllImage_responses.json"  # Path in the bucket
        
            # Upload the JSON response to S3
            s3_client.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=response_json,
                ContentType='application/json'
            )
            print(f"Response uploaded to s3://{bucket_name}/{object_key}")

    except Exception as e:
        print(f"Error in Lambda function: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    return {"statusCode": 200, "body": json.dumps({"message": "Processing completed"})}