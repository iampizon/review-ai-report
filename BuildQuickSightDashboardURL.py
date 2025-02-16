import boto3
import json

def get_aws_account_id():
    # STS 클라이언트 생성
    sts_client = boto3.client('sts')

    # get_caller_identity 호출
    response = sts_client.get_caller_identity()

    # Account ID 추출
    account_id = response["Account"]
    return account_id

def lambda_handler(event, context):
    # QuickSight 클라이언트 생성
    quicksight_client = boto3.client('quicksight', region_name='ap-northeast-2')  # 지역 설정
    
    # 필요한 변수 설정
    aws_account_id = get_aws_account_id() # AWS 계정 ID
    dashboard_arn = 'YOUR_DASHBOARD_ARN'
    allowed_domains = ['YOUR_DOMAIN']  # 허용된 도메인 리스트
    
    try:
        # generate-embed-url-for-anonymous-user API 호출
        response = quicksight_client.generate_embed_url_for_anonymous_user(
            AwsAccountId=aws_account_id,
            Namespace='default',
            AuthorizedResourceArns=[dashboard_arn],
            AllowedDomains=allowed_domains,
            ExperienceConfiguration={
                'Dashboard': {
                    'InitialDashboardId': dashboard_arn.split('/')[-1]
                }
            },
            SessionLifetimeInMinutes=600  # 세션 지속 시간 (최대 10시간)
        )
        
        # 성공적으로 URL 생성 시 반환
        return {
            'statusCode': 200,
            'body': json.dumps({
                'EmbedUrl': response['EmbedUrl']
            })
        }
    except Exception as e:
        # 오류 처리
        return {
            'statusCode': 500,
            'body': json.dumps({
                'Error': str(e)
            })
        }
