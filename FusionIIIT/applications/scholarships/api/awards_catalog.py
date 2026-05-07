import json
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

CATALOG_FILE = os.path.join(os.path.dirname(__file__), "awards_catalog.json")

class AwardsCatalogView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not os.path.exists(CATALOG_FILE):
            default_data = [
              { "id": 1, "name": "Director's Gold Medal", "category": "Excellence", "amount": "Gold Medal", "frequency": "Annual", "eligibility": "Top academic performance across all disciplines, Outstanding all-round achievement.", "deadline": "2026-05-15", "description": "The Director's Gold Medal is awarded annually to the graduating student who demonstrates outstanding academic performance, exemplary leadership, and significant contributions to the institute's extracurricular activities." },
              { "id": 2, "name": "Director's Silver Medal", "category": "Excellence", "amount": "Silver Medal", "frequency": "Annual", "eligibility": "Highest CPI in the respective branch/discipline.", "deadline": "2026-05-15", "description": "The Director's Silver Medal is awarded to the student securing the highest academic standing (CPI) in their respective B.Tech or M.Tech discipline among the graduating class." },
              { "id": 3, "name": "Convocation Medals", "category": "Merit", "amount": "Medal/Certificate", "frequency": "Annual", "eligibility": "Excellence in specific technical, cultural, or sports domains.", "deadline": "2026-05-15", "description": "The Proficiency Medal is bestowed upon students demonstrating exceptional proficiency and dedication in specific institute-level clubs, societies, or domains including technical, cultural, and sports." }
            ]
            with open(CATALOG_FILE, "w") as f:
                json.dump(default_data, f)
            return Response(default_data)

        with open(CATALOG_FILE, "r") as f:
            data = json.load(f)
        return Response(data)

    def post(self, request):
        if not os.path.exists(CATALOG_FILE):
            data = []
        else:
            with open(CATALOG_FILE, "r") as f:
                try:
                    data = json.load(f)
                except:
                    data = []
        
        req_data = request.data
        if isinstance(req_data, dict) and "id" in req_data:
            for item in data:
                if str(item.get("id")) == str(req_data["id"]):
                    if "catalog" in req_data:
                        item["description"] = req_data["catalog"]
                    break
        elif isinstance(req_data, list):
            data = req_data

        with open(CATALOG_FILE, "w") as f:
            json.dump(data, f)
        return Response({"status": "success", "data": data})
