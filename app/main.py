import json
from jose import jwt
from fastapi import Cookie, FastAPI, Form, Request, templating, Response
from fastapi.responses import RedirectResponse
from flowers_repository import Flower, FlowersRepository
from purchases_repository import Purchase, PurchasesRepository
from users_repository import User, UsersRepository

app = FastAPI()
templates = templating.Jinja2Templates("../templates")


flowers_repository = FlowersRepository()
purchases_repository = PurchasesRepository()
users_repository = UsersRepository()


def create_jwt(id: int) -> str:
    body = {"id": id}
    token = jwt.encode(body, "BadBreacking", "HS256")
    return token


def decode_jwt(token: str) -> int:
    data = jwt.decode(token, "BadBreacking", "HS256")
    return data["id"]

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/signup")
def get_signup(request: Request):
    return templates.TemplateResponse("/authorization/signup.html",
                                      {
                                          "request": request,
                                      })

@app.post("/signup")
def post_signup(
        email: str = Form(),
        full_name: str = Form(),
        password: str = Form(),
):
    user = User(email=email, full_name=full_name, password=password)
    users_repository.save(user)
    return RedirectResponse("/login", status_code=303)

@app.get("/login")
def get_login(request: Request):
    return templates.TemplateResponse("/authorization/login.html",
                                      {
                                          "request": request,

                                      })
@app.post("/login")
def post_login(
        email: str = Form(),
        password: str = Form(),

):
    user = users_repository.get_by_email(email)
    if user.password == password:
        response = RedirectResponse("/profile", status_code=303)
        print(user.id)
        print(user)
        token = create_jwt(user.id)
        response.set_cookie("token", token)
        return response

    return RedirectResponse("/login", status_code=303)

@app.get("/profile")
def get_profile(
        request: Request,
        token: str = Cookie(default=None)
):
    if not token:
        return RedirectResponse("/login", status_code=303)
    user_id = decode_jwt(token)
    user = users_repository.get_by_id(user_id)

    return templates.TemplateResponse(
        "authorization/profile.html",
        {
            "request": request,
            "user": user
        }
    )

@app.get("/flowers")
def get_flowers(request: Request):
    flowers = flowers_repository.get_all()
    return templates.TemplateResponse(
        "/main/flowers.html",
        {"request": request,
         "flowers": flowers}
    )
@app.post("/flowers")
def post_flowers(name: str = Form(),
                 count: int = Form(),
                 cost: int = Form()):
    flower = Flower(name=name, count=count, cost=cost)
    flowers_repository.save(flower)
    return RedirectResponse("/flowers", status_code=303)

shopping_cart = []
@app.post("/cart/items")
def add_to_cart(flower_id: int = Form(),):
    shopping_cart.append(flower_id)
    response = RedirectResponse("/flowers", status_code=303)
    response.set_cookie(key="cart_items", value=",".join(map(str, shopping_cart)))
    return response

@app.get("/cart/items")
def get_to_cart(request: Request,
                ):
    cart_items = request.cookies.get("cart_items")
    cart_flowers = []
    total_price = 0.0

    if cart_items:
        cart_items_list = list(map(int, cart_items.split(",")))
        for flower_id in cart_items_list:
            flower = flowers_repository.get_by_id(flower_id)
            if flower:
                cart_flowers.append(flower)
                total_price += flower.cost

    return templates.TemplateResponse(
        "/main/cart.html", {"request": request, "cart_flowers": cart_flowers, "total_price": total_price}
    )