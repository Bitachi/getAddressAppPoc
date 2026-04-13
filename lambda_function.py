import json
import urllib.request
import urllib.parse
import os

# Lambda環境変数から取得（コードに直書きしないこと）
GOOGLE_MAPS_API_KEY = os.environ['GOOGLE_MAPS_API_KEY']

def lambda_handler(event, context):
    # CORSヘッダー（S3からのブラウザリクエストに必要）
    cors_headers = {
        'Access-Control-Allow-Origin': '*',  # 本番ではS3のURLに絞ること
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Content-Type': 'application/json'
    }

    # OPTIONSリクエスト（プリフライト）への対応
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': ''
        }

    try:
        # リクエストボディのパース
        body = json.loads(event.get('body', '{}'))
        lat = body.get('lat')
        lng = body.get('lng')

        if lat is None or lng is None:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'lat, lng が必要です'}, ensure_ascii=False)
            }

        # Google Maps Geocoding API 呼び出し
        params = urllib.parse.urlencode({
            'latlng': f'{lat},{lng}',
            'language': 'ja',           # 日本語で住所を返す
            'result_type': 'street_address|sublocality',  # 番地レベルを優先
            'key': GOOGLE_MAPS_API_KEY
        })
        url = f'https://maps.googleapis.com/maps/api/geocode/json?{params}'

        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode('utf-8'))

        # レスポンス解析
        if data.get('status') == 'OK' and data.get('results'):
            address = data['results'][0]['formatted_address']

            # 「日本、」プレフィックスを除去
            if address.startswith('日本、'):
                address = address[3:]

            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'address': address}, ensure_ascii=False)
            }

        elif data.get('status') == 'ZERO_RESULTS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'error': '該当する住所が見つかりませんでした'}, ensure_ascii=False)
            }

        else:
            print(f"Geocoding API error: {data.get('status')}, {data.get('error_message', '')}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'error': f"Geocoding APIエラー: {data.get('status')}"}, ensure_ascii=False)
            }

    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'error': 'リクエストボディのJSONが不正です'}, ensure_ascii=False)
        }
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': 'サーバーエラーが発生しました'}, ensure_ascii=False)
        }
