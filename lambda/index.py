# lambda/index.py
import json
import os
import urllib.request
import urllib.error

# FastAPI の URL
FASTAPI_URL = "https://57b8-34-124-254-60.ngrok-free.app/v1/llm/prompt"

# モデルID（必要に応じて使用する）
MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-lite-v1:0")

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))
        
        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        
        print("Processing message:", message)
        print("Using model:", MODEL_ID)
        
        # 会話履歴を使用
        messages = conversation_history.copy()
        
        # ユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })
        
        # FastAPIに送るリクエストペイロードを構築
        payload = {
            "messages": messages
        }
        
        # JSON データをエンコード
        json_data = json.dumps(payload).encode('utf-8')
        
        # リクエストヘッダー
        headers = {
            'Content-Type': 'application/json',
        }
        
        # HTTP リクエストを送信
        request = urllib.request.Request(FASTAPI_URL, data=json_data, headers=headers, method='POST')

        try:
            # レスポンスを受け取る
            with urllib.request.urlopen(request) as response:
                response_data = json.loads(response.read().decode())
                print("FastAPI response:", json.dumps(response_data, default=str))
            
            # アシスタントの応答を取得
            assistant_response = response_data.get('response')
            if not assistant_response:
                raise Exception("No response content from the model")
            
            # アシスタントの応答を会話履歴に追加
            messages.append({
                "role": "assistant",
                "content": assistant_response
            })
            
            # 成功レスポンスの返却
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                    "Access-Control-Allow-Methods": "OPTIONS,POST"
                },
                "body": json.dumps({
                    "success": True,
                    "response": assistant_response,
                    "conversationHistory": messages
                })
            }
        
        except urllib.error.HTTPError as e:
            # HTTPエラーが発生した場合の処理
            print(f"HTTP error occurred: {e.code} - {e.reason}")
            raise Exception(f"HTTP error occurred: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            # URLエラーが発生した場合の処理
            print(f"URL error occurred: {e.reason}")
            raise Exception(f"URL error occurred: {e.reason}")

    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
