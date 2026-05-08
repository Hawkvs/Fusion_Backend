import json
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

CATALOG_FILE = os.path.join(os.path.dirname(__file__), "frontend_catalog.json")

class FrontendCatalogView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not os.path.exists(CATALOG_FILE):
            default_data = [
              { 'id': 1, 'name': 'Merit Cum Means', 'category': 'Merit', 'amount': '?10,000', 'frequency': 'Per Semester', 'eligibility': 'CPI > 8.0, Income < ?5L, 0 Backlogs', 'deadline': '2026-10-15', 'description': 'The Merit Cum Means (MCM) scholarship is awarded to meritorious students whose total annual family income falls under ? 5,000,000. It requires a CPI of 8.0 or above with no standing backlogs.' },
              { 'id': 2, 'name': 'Single Parent', 'category': 'Need-based', 'amount': '?15,000', 'frequency': 'Per Year', 'eligibility': 'Single Parent, Income < ?3L', 'deadline': '2026-12-31', 'description': 'This scholarship is dedicated to students who rely on a single parent. The primary criterion is that the family income should not exceed ? 3,00,000 annually. Verification documents such as Death Certificate and Income Document are mandatory.' },
            ]
            with open(CATALOG_FILE, 'w') as f:
                json.dump(default_data, f)
            return Response(default_data)

        with open(CATALOG_FILE, 'r') as f:
            data = json.load(f)
        return Response(data)

    def post(self, request):
        with open(CATALOG_FILE, 'w') as f:
            json.dump(request.data, f)
        return Response({"status": "success", "data": request.data})
