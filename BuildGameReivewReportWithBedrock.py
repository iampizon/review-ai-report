import boto3
import json
import re
import time
import calendar
import base64

def read_file(file_path):
    """Load system prompt from a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Warning: System prompt file not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error reading system prompt file: {str(e)}")
        return None
        
def create_bedrock_client():
    # Initialize the Bedrock runtime client
    bedrock = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1"  # Change to your preferred region
    )
    return bedrock

def invoke_claude(system_prompt, prompt, client):
    # Model ID for Claude 3.5 Sonnet
    model_id = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    formatted_prompt = prompt
    if system_prompt:
        formatted_prompt = f"{system_prompt}\n\nHuman: {prompt}\nAssistant:"
      
    # Prepare the request body
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 3000,
        "messages": [
            {
                "role": "user",
                "content": formatted_prompt
            }
        ],
        "temperature": 1,
        "top_p": 0.9,
        "top_k": 250
    }

    try:
        # Invoke the model
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Parse and return the response
        response_body = json.loads(response.get('body').read())
        return response_body.get('content')[0]['text']

    except Exception as e:
        print(f"Error invoking Claude: {str(e)}")
        return None

def extract_all_tagged_content(text):
    # Find all tags and their content
    pattern = r'<(\w+)>\s*(.*?)\s*</\1>'
    matches = re.findall(pattern, text, re.DOTALL)
    # Convert to dictionary
    return {tag: content for tag, content in matches}

def save_to_s3(content_dict, bucket_name, folder_path='dataset'):
    # Initialize S3 client
    s3 = boto3.client('s3')
    
    try:
        # Save each tag's content to a separate file
        for tag, content in content_dict.items():
            # Create filename using the tag name
            filename = f"{folder_path}/{tag}/{tag}.csv"
            
            try:
                # Upload content to S3
                s3.put_object(
                    Bucket=bucket_name,
                    Key=filename,
                    Body=content.encode('utf-8')
                )
                print(f"Successfully saved {filename} to S3")
                
            except s3.exceptions.NoSuchBucket:
                print(f"Error: Bucket '{bucket_name}' does not exist")
                return
            except Exception as e:
                print(f"Error saving {filename}: {e}")
                
    except Exception as e:
        print(f"Error: {e}")

def get_cache(start_date, end_date):

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table("GameReviewReportResultCache")
    pkey = f"{start_date}-{end_date}"

    try:

        response = table.get_item(
            Key={
                'id': pkey
            }
        )

        print(response)

        decoded_bytes = base64.b64decode(response['Item']['reportResult'])
        decoded_string = decoded_bytes.decode('utf-8')

        print(f"Get Cache '{pkey}':{decoded_string}")
        return f"{decoded_string}"

    except Exception as e:
        print(f"Error querying items: {e}")
        return None

def put_cache(start_date, end_date, report_result):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table("GameReviewReportResultCache")

    report_result_bytes = report_result.encode('utf-8')
    encoded_bytes = base64.b64encode(report_result_bytes)
    encoded_string = encoded_bytes.decode('utf-8')

    try:
        pkey = f"{start_date}-{end_date}"
        table.put_item(
            Item={
                'id': pkey,
                'reportResult': encoded_string
            }
        )
        print(f"Put Cache '{pkey}'")

    except Exception as e:
        print(f"Error putting item: {e}")

def get_reviews(start_date, end_date):
    lambda_client = boto3.client('lambda')
    
    try:
        # Synchronous invocation
        response = lambda_client.invoke(
            FunctionName='GetGameReviewLogs',
            InvocationType='RequestResponse',  # Synchronous invocation
            Payload=json.dumps({
                'startDate': start_date,
                'endDate': end_date
            })
        )
        
        # Get the response payload
        response_payload = json.loads(response['Payload'].read())
        # print(response_payload)
        return response_payload

    except Exception as e:
        print(f"Error: {str(e)}")
        raise


def lambda_handler(event, context):

    # parse input
    input_str = event['input']
    input_json = json.loads(input_str)
    
    # extract dates
    start_date = input_json['startDate']
    end_date = input_json['endDate']
    
    print(f"Extracted dates: {start_date} to {end_date}")

    report_data = get_cache(start_date, end_date)

    if report_data is None:
        # get review data from DDB
        reviews = get_reviews(start_date, end_date)
        print(reviews['body_csv'])

        # ready system prompt
        system = read_file("./system_prompt.txt")
        user_input = f"""input : {reviews['body_csv']}"""

        # ask to bedrock
        client = create_bedrock_client()
        response = invoke_claude(system, user_input, client)
        if response:
            print(response)
            put_cache(start_date, end_date, response)
            report_data = response

    result = extract_all_tagged_content(report_data)

    # save to s3
    bucket_name='YOUR_BUCKET_NAME'
    save_to_s3(result, bucket_name, 'dataset')

    return {
        'statusCode': 200,
        'body': json.dumps('분석이 완료됐습니다.')
    }
