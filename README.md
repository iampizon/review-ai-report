# 게임 리뷰 AI 분석 보고서 생성 DEMO

## 소개

- 커뮤니티에서 크롤링한 유저들의 리뷰를 AWS Bedrock의 생성형 AI로 분석하여 QuickSight로 보고서로 만들어주는 DEMO 아키텍처의 소스입니다.

#### 테스트 페이지
- 다음 링크에서 테스트 가능 합니다.
[bit.ly/game-review-ai-report-demo](https://bit.ly/game-review-ai-report-demo)
- 2025년 4월1일부터 4월30일까지의 가상 게임의 리뷰가 조회가능 합니다(생성형 AI로 만든 가상 리뷰).
- 리뷰 조회 후 "보고서 생성"을 클릭하면 조회 기간에 해당하는 동향을 분석하여 실시간으로 QuickSight 보고서로 출력합니다.

## 아키텍처

#### DEMO 웹페이지 아키텍처
<img src="images/arch-1.png" width=700/>

- DEMO 웹페이지의 아키텍처입니다. S3와 CloundFront를 통해 호스팅되며, API-Gateway를 통해 3개의 API가 호출됩니다.
  - 리뷰 조회 API ( GetGameReviewsLogs <-> DynamoDB 리뷰 조회 )
  - 보고서 생성 API (  BuildGameReviewReport Step Functions -> 보고서 생성 워크플로우 수행 )
  - 보고서 생성 진행상황 조회 API ( BuildGameReviewReport Step Functions 진행 상황 조회 )

#### 보고서 생성 워크플로우 아키텍처
<img src="images/arch-2.png"  width=700/>

- BuildGameReviewReport Step Functions 를 호출하는 보고서 생성 API의 상세 아키텍처 입니다.
  - BuildGameReviewReportWithBedrock Lambda를 호출
    - 이 함수는 GetGameReviewsLogs Lambda를 호출하여 조건에 맞는 리뷰를 조회하며 이를 Bedrock에 입력하여 분석을 수행합니다.
    - Bedrock의 분석결과를 S3에 저장하며, 이는 Athena의 데이터소스가 됩니다.
    - QuickSight는 이 Athena에 direct query를 실행하여 보고서를 생성합니다.
  - 분석이 완료되면, BuildQuickSightDashboardURL를 호출
    - 이 함수는 Athena의 분석결과로 생성된 QuickSightDashboard의 Embedding URL을 생성합니다.
    - 이 URL로 익명 사용자가 보고서에 접근할 수 있게 됩니다.

#### 전체 아키텍처
<details>
<img src="images/arch-3.png"/>
</details>

## 활용 방법
- 기존에 리뷰를 모아둔 데이터 레이크, DB 등이 있다면 "보고서 생성 워크플로우 아키텍처"를 그대로 활용하여 AI 분석 보고서 생성에 사용할 수 있습니다.
- 리뷰를 조회하는 GetGameReviewsLogs Lambda를 환경에 맞게 수정하여 Json 형태로 출력하게 수정해주면 됩니다.
- 리뷰를 클로링하고 데이터 레이크등에 적재하는 워크를로우의 아키텍처 샘플도 이 후 제공 예정입니다.

## 설치 방법
- "보고서 생성 워크플로우 아키텍처"의 Cloudformation 제공 예정입니다.

## TODO
- Cloudformation 배포
  - 구현중
- QuickSight 보고서 PDF 출력 기능 구현
  - 구현중
- DEMO 웹사이트 가운데 창 크기 조정 가능하도록
  - 완료함
- QuickSight dataset refresh가 24시간에 32회가 hard limit 이어서 하루에 32회 이상 보고서 업데이트 안되던 문제
  - 완료함 : Spice를 사용하지 않고, Athena에 direct query를 쓰도록 함. 보고서 조회 속도는 약간 느려졌지만 보고서 생성 횟수 제한 없어짐.
- Bedrock Throttling 문제
  - input token 수가 클 경우(분석 리뷰가 많은 경우), 보고서 생성이 안되는 경우가 있음. 몇 분간 기다렸다가 하면 되는데, 현재로서는 quota 문제로 해결할 수 없음
  - 일단, 한번 분석된 결과는 캐싱하게 하여 동일 범위의 조회일 경우 캐싱된 데이터로 보고서를 생성하게 해둠.
  - 이 후 Throttling exception 발생시 AWS region를 변경하여 retry 하는 로직 구현 예정.

