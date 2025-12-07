import os
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes import auth_routes, user_routes, task_routes,group_routes,group_member_routes,task_comment_routes,attachment_verification_rouytes, community_challenge

app = FastAPI(title="Web3 Auth + Users API")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log chi tiết lỗi
    print(f"Validation error for request: {request.url}")
    print(f"Validation errors: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={
            "message": "Unprocessable Entity",
            "errors": exc.errors()  # Trả về thông báo lỗi chi tiết
        },
    )

@app.get("/", include_in_schema=False)
@app.head("/", include_in_schema=False)
def root():
    return {"message": "API is running 🚀"}

app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(task_routes.router)
app.include_router(group_routes.router)
app.include_router(group_member_routes.router) 
app.include_router(task_comment_routes.router)

app.include_router(attachment_verification_rouytes.router)
app.include_router(community_challenge.router)

