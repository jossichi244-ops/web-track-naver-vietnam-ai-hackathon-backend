from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth_routes, user_routes, task_routes,group_routes,group_member_routes,task_comment_routes,attachment_verification_rouytes

app = FastAPI(title="Web3 Auth + Users API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(task_routes.router)
app.include_router(group_routes.router)
app.include_router(group_member_routes.router) 
app.include_router(task_comment_routes.router)
app.include_router(attachment_verification_rouytes.router)