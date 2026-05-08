import json
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

MERIT_LIST_FILE = os.path.join(os.path.dirname(__file__), "merit_list.json")

class MeritListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not os.path.exists(MERIT_LIST_FILE):
            default_data = []
            with open(MERIT_LIST_FILE, 'w') as f:
                json.dump(default_data, f)
            return Response(default_data)
        with open(MERIT_LIST_FILE, 'r') as f:
            data = json.load(f)
        return Response(data)

    def post(self, request):
        with open(MERIT_LIST_FILE, 'w') as f:
            json.dump(request.data, f)
        return Response({"status": "success", "data": request.data})
