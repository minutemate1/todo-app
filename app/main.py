from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import FastAPI, status, HTTPException, Depends
from sqlalchemy import  select
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from app.models.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(CORSMiddleware,
                   allow_origins=["http://localhost:3000"],
                   allow_methods=["*"])


def task_orm_to_model(task_orm: TaskORM) -> TaskSchema:
    return TaskSchema(id=task_orm.id, title=task_orm.title, completed=task_orm.completed)

def category_orm_to_model(category_orm: CategoryORM) -> CategorySchema:
    return CategorySchema(id=category_orm.id, name=category_orm.name)


@app.get("/tasks")
def read_tasks(db: Session = Depends(get_db)) -> list[TaskSchema]:
    tasks_from_db = db.scalars(select(TaskORM)).all()
    return [task_orm_to_model(task) for task in tasks_from_db]


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreateSchema, db: Session = Depends(get_db)) -> TaskSchema:
    new_task = TaskORM(id=str(uuid4()), title=payload.title, completed=False)
    db.add(new_task)
    db.commit()
    return task_orm_to_model(new_task)


@app.patch("/tasks/{task_id}")
def update_task(task_id: str, payload: TaskUpdateSchema, db: Session = Depends(get_db)):
    task_for_update = db.get(TaskORM, task_id)
    if payload.title:
        task_for_update.title = payload.title
    if payload.completed:
        task_for_update.completed = payload.completed

    db.commit()
    return task_for_update


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, db: Session = Depends(get_db)) -> None:
    task_for_delete = db.get(TaskORM, task_id)
    db.delete(task_for_delete)
    db.commit()


@app.get("/categories")
def read_categories(db: Session = Depends(get_db)) -> list[CategorySchema]:
    categories_from_db = db.scalars(select(CategoryORM)).all()
    return [category_orm_to_model(category) for category in categories_from_db]


@app.post("/categories", status_code=status.HTTP_201_CREATED)
def create_new_category(payload: CategoryCreateSchema, db: Session = Depends(get_db)) -> CategorySchema:
    new_category = CategoryORM(id=str(uuid4()), name=payload.name)
    db.add(new_category)
    db.commit()
    return category_orm_to_model(new_category)


@app.patch("/categories/{category_id}")
def update_category(category_id: str, payload: CategoryUpdateSchema, db: Session = Depends(get_db)) -> CategorySchema:
    category_to_update = db.get(CategoryORM, category_id)
    if payload.name:
        category_to_update.name = payload.name
    db.commit()
    return category_orm_to_model(category_to_update)


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: str, db: Session = Depends(get_db)):
    category_to_delete = db.get(CategoryORM, category_id)
    db.delete(category_to_delete)
    db.commit()