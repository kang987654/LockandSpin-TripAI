from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from recommendations.services.ai_service import recommend_food_menu

class FoodRecommendationView(APIView):
    """
    POST /api/recommendations/food/
    Body: {"region": "서울 홍대", "preference": "비도 오는데 따뜻한 국물"}
    """
    def post(self, request, *args, **kwargs):
        region = request.data.get('region', '').strip()
        preference = request.data.get('preference', '').strip()
        
        if not region or not preference:
            return Response({"error": "region and preference are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        result = recommend_food_menu(region, preference)
        if "error" in result:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(result, status=status.HTTP_200_OK)
