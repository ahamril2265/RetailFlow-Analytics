"""
mock_data.py — Simulates FakeStore API responses for local dev/testing.
In production you'd hit the real API. We patch requests.get here.
"""

MOCK_PRODUCTS = [
    {"id": 1, "title": "Fjallraven Backpack", "price": 109.95, "description": "Great bag", "category": "men's clothing", "image": "https://fakestoreapi.com/img/1.jpg", "rating": {"rate": 3.9, "count": 120}},
    {"id": 2, "title": "Mens Casual T-Shirt", "price": 22.3,  "description": "Slim fit", "category": "men's clothing", "image": "https://fakestoreapi.com/img/2.jpg", "rating": {"rate": 4.1, "count": 259}},
    {"id": 3, "title": "Womens Dress",        "price": 15.99, "description": "Floral", "category": "women's clothing", "image": "https://fakestoreapi.com/img/3.jpg", "rating": {"rate": 2.6, "count": 235}},
    {"id": 4, "title": "Mens Casual Slim Fit", "price": -1.0, "description": "Bad price", "category": "men's clothing", "image": "https://fakestoreapi.com/img/4.jpg", "rating": {"rate": 2.1, "count": 430}},
    {"id": 5, "title": "",                    "price": 695.0, "description": "Ring", "category": "jewelery", "image": "https://fakestoreapi.com/img/5.jpg", "rating": {"rate": 6.2, "count": 400}},
]

MOCK_USERS = [
    {"id": 1, "email": "john@gmail.com", "username": "johnd",    "password": "m38rmF$", "name": {"firstname": "John", "lastname": "Doe"},    "address": {"city": "kilchurn", "street": "7835 new road", "number": 3, "zipcode": "12926-3874"}, "phone": "1-570-236-7033"},
    {"id": 2, "email": "morrison@gmail.com", "username": "mor_2314", "password": "83r5^_",  "name": {"firstname": "David", "lastname": "Morrison"}, "address": {"city": "kilchurn", "street": "7267 cam road", "number": 7, "zipcode": "12926-3874"}, "phone": "1-570-236-7033"},
    {"id": 3, "email": "not-an-email",    "username": "baduser",  "password": "pass123", "name": {"firstname": "Bad",   "lastname": "User"},     "address": {}, "phone": ""},
]

MOCK_CARTS = [
    {"id": 1, "userId": 1, "date": "2024-01-15", "products": [{"productId": 1, "quantity": 4}, {"productId": 2, "quantity": 1}]},
    {"id": 2, "userId": 2, "date": "2024-01-16", "products": [{"productId": 3, "quantity": 2}]},
    {"id": 3, "userId": 3, "date": "2024-01-16", "products": []},  # empty cart — validation should catch this
]