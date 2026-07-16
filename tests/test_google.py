from services.distance_service import GoogleDistanceService

service = GoogleDistanceService()

result = service.get_distance(
    "53 Avenue de la Gare, 34970 Lattes"
)

print(result)