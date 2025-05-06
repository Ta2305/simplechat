# lambda/index.py
import json
import os
import urllib.request
import urllib.error

# FastAPI の URL
FASTAPI_URL = "https://57b8-34-124-254-60.ngrok-free.app/generate"

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
            "prompt": messages,
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
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
            with urllib.request.urlopen(request, timeout=60) as res:
                res_body = res.read()
                res_json = json.loads(res_body.decode("utf-8"))
    
                # FastAPIのレスポンスに合わせて出力
                answer = res_json.get("generated_text", "")
                return {
                    "statusCode": 200,
                    "body": json.dumps({"completion": answer})
                }

        except urllib.error.HTTPError as e:
            return {
                "statusCode": e.code,
                "body": json.dumps({"error": e.reason})
            }
        except urllib.error.URLError as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e.reason)})
            }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
