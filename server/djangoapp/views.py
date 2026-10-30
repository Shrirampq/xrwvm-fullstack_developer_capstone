from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
import logging
import json
import requests
from django.views.decorators.csrf import csrf_exempt
from .models import CarMake, CarModel

logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:3030"
SENTIMENT_URL = "http://localhost:5000"


@csrf_exempt
def login_user(request):
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)


def logout_request(request):
    logout(request)
    return JsonResponse({"userName": ""})


def get_cars(request):
    car_models = CarModel.objects.select_related('car_make')
    cars = [{"CarModel": cm.name, "CarMake": cm.car_make.name}
            for cm in car_models]
    return JsonResponse({"CarModels": cars})


def _backend_get(path):
    try:
        resp = requests.get(BACKEND_URL + path, timeout=10)
        return resp.json()
    except Exception as err:
        print("Backend error:", err)
        return None


def get_dealerships(request, state="All"):
    if state == "All":
        data = _backend_get("/fetchDealers")
    else:
        data = _backend_get("/fetchDealers/" + state)
    return JsonResponse({"status": 200, "dealers": data})


def get_dealer_details(request, dealer_id):
    data = _backend_get("/fetchDealer/" + str(dealer_id))
    return JsonResponse({"status": 200, "dealer": data})


def get_dealer_reviews(request, dealer_id):
    reviews = _backend_get("/fetchReviews/dealer/" + str(dealer_id)) or []
    for review in reviews:
        try:
            text = review.get("review", "")
            resp = requests.get(SENTIMENT_URL + "/analyze/" + text, timeout=10)
            review["sentiment"] = resp.json().get("sentiment", "neutral")
        except Exception:
            review["sentiment"] = "neutral"
    return JsonResponse({"status": 200, "reviews": reviews})


@csrf_exempt
def add_review(request):
    if request.user.is_anonymous:
        return JsonResponse({"status": 403, "message": "Unauthorized"})
    try:
        payload = json.loads(request.body)
        resp = requests.post(BACKEND_URL + "/insert_review",
                             json=payload, timeout=10)
        return JsonResponse({"status": 200, "result": resp.json()})
    except Exception as err:
        print("Error posting review:", err)
        return JsonResponse(
            {"status": 401, "message": "Error in posting review"})
