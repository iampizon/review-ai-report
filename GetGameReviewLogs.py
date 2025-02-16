import boto3
import json
from datetime import datetime
from typing import Dict, Any

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:

    try:

        start_date = event.get('startDate')
        end_date = event.get('endDate')
        print(start_date, end_date)

        # Initialize DynamoDB resource
        table_name = 'GameReviewLogs'  # Replace with your table name
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        # Scan parameters
        scan_params = {
            'FilterExpression': '#date_field BETWEEN :start_date AND :end_date',
            'ExpressionAttributeNames': {
                '#date_field': 'DATE'
            },
            'ExpressionAttributeValues': {
                ':start_date': start_date,
                ':end_date': end_date
            }
        }

        items = []
        response = table.scan(**scan_params)
        items.extend(response.get('Items', []))

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            scan_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = table.scan(**scan_params)
            items.extend(response.get('Items', []))

        # Format the response to match your frontend expectations
        formatted_items = []
        for item in items:
            formatted_items.append({
                'userid': item.get('ID', ''),
                'date': item.get('DATE', ''),
                'rating': int(item.get('RATING', 0)),
                'review': item.get('REVIEW', '')
            })

        print(formatted_items)
        
        csv_output = f"ID,DATE,RATING,REVIEW\n"
        for item in items:
            csv_output = f"{csv_output}{item.get('ID', '')},{item.get('DATE', '')},{(item.get('RATING', 0))},{item.get('REVIEW', '')}\n"
        
        print(csv_output)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'count': len(formatted_items),
                'items': formatted_items
            }, default=str),
            'body_csv': json.dumps({
                'count': len(formatted_items),
                'items': csv_output
            }, default=str)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Error scanning items: {str(e)}'
            })
        }
