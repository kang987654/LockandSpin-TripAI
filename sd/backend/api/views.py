from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services.recommendation_service import get_recommendations

@api_view(['POST'])
def recommend_view(request):
    region = request.data.get('region', '')
    travel_date = request.data.get('date', '')
    query = request.data.get('query', '')
    
    if not region or not query:
        return Response({"error": "Region and query are required"}, status=400)
        
    try:
        results = get_recommendations(region, travel_date, query)
        return Response(results)
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return Response({"error": "현재 AI(Gemini) 무료 버전의 1분당 요청 한도를 초과했습니다. 약 30초에서 1분 정도 기다리신 후 다시 시도해 주세요!"}, status=429)
        return Response({"error": error_msg}, status=500)
