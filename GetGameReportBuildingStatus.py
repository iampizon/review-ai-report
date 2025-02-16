import boto3
import json

def lambda_handler(event, context):
    # Step Functions 클라이언트 생성
    stepfunctions_client = boto3.client('stepfunctions')
    
    # event에서 executionArn 가져오기
    execution_arn = event.get('executionArn')
    
    if not execution_arn:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'executionArn is required'})
        }
    
    try:
        # DescribeExecution 호출
        response = stepfunctions_client.describe_execution(
            executionArn=execution_arn
        )
        
        # 결과 반환
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': response['status'],
                'startDate': str(response['startDate']),
                'stopDate': str(response.get('stopDate', 'Still Running')),
                'input': response['input'],
                'output': response.get('output', 'No output yet'),
            })
        }
    except stepfunctions_client.exceptions.ExecutionDoesNotExist as e:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': f'Execution not found: {str(e)}'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'An error occurred: {str(e)}'})
        }
