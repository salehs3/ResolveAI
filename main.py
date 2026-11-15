from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv
from complaint_extractor import extract_complaint, ComplaintDetails
from resolve_agent import ask_resolveai
from openai import RateLimitError, APIConnectionError, APITimeoutError

load_dotenv()
import asyncio
import httpx

from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()
load_dotenv()

#Database
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL); # connect_args will will tell the sql to execute multiple thread sinstead of only one which is the default
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine) # make sures we dont reload everytime we 
Base = declarative_base()

#Database model - like a row in atable which has a col data
class cases(Base):
    __tablename__ = "cases"

    id = Column(Integer,primary_key=True,index=True)#index makes it indexable
    name = Column(String(100),nullable=False)
    email = Column(String(100),nullable=False,unique=True)
    status = Column(String(100),nullable=False)
    priority = Column(String(20),nullable=False,server_default="medium")


def get_db():
    # 1. Open a new database session for the incoming request
    db = SessionLocal()
    try:
        # 2. Hand the session to the route function (pauses here until request finishes)
        yield db
    finally:
        # 3. Guaranteed to run: close the session and return connection to the pool
        db.close()

#Pydantic models

class CaseCreate(BaseModel):    
    name:str
    email:str
    status:str

class Casesresponse(BaseModel): # this makes sure sensitive data like id doesnt go through api
    id: int
    name:str
    email:str
    status:str

    class Config:
        from_attributes = True




@app.get("/")
def intro():
    return {"message": "Integration with SQL"}

@app.get("/cases/{case_id}",response_model = Casesresponse, summary="Get case details",description="Input tour case ID and get relevant case details",responses={404 : {"description":"Case not found"}})
def get_case(case_id:int, db:Session = Depends(get_db)):
    case = db.query(cases).filter(cases.id == case_id).first()
    if not case :
        raise HTTPException(status_code=404 , detail="Case not found")
    return case

    
@app.post("/cases/",response_model = Casesresponse,status_code=201)
def create_case(case: CaseCreate,db:Session = Depends(get_db)):
    if db.query(cases).filter(cases.email == case.email).first():
        raise HTTPException(status_code=409, detail="Case already exists")

    #now create case

    new_case = cases(**case.dict())
    db.add(new_case)
    db.commit() #Important else it wont go to db
    db.refresh(new_case)
    return new_case


@app.put("/cases/{case_id}",response_model = Casesresponse)
def update_case(case_id:int, case:CaseCreate,db:Session = Depends(get_db)):
    db_user = db.query(cases).filter(cases.id == case_id).first()
    if not db_user: 
        raise HTTPException(status_code=404 , detail="Case not found")
    for key,val in case.dict().items():
        setattr(db_user,key,val)

    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/cases/{case_id}",response_model = Casesresponse)
def delete_case(case_id:int, db:Session = Depends(get_db)):
    db_user = db.query(cases).filter(cases.id == case_id).first()
    if not db_user: 
        raise HTTPException(status_code=404 , detail="Case not found")
    db.delete(db_user)
    db.commit()

    return db_user

@app.get("/cases/",response_model = List[Casesresponse])
def get_all(db:Session = Depends(get_db)):
    return db.query(cases).all()

async def fetch_with_retry(client, url):
    max_attempts = 3
    initial_delay = 1

    for i in range(max_attempts):
        try:
            r = await client.get(url)
            r.raise_for_status()
            return r.json()
        except(httpx.ConnectError,httpx.TimeoutException):
            if i == max_attempts - 1:
                raise
            delay = initial_delay * (2**i)
            await asyncio.sleep(delay)

@app.get("/cases/{case_id}/details")
async def get_case_details(case_id: int, db: Session = Depends(get_db)):
    db_case = db.query(cases).filter(cases.id==case_id).first()
    if not db_case:
        raise HTTPException(status_code=404,detail="Case not found")
    async with httpx.AsyncClient(timeout=5) as client:
       try:
            r, r2 = await asyncio.gather(
                fetch_with_retry(client, f"http://127.0.0.1:8001/orders/{case_id}"),
                fetch_with_retry(client, f"http://127.0.0.1:8002/shipments/{case_id}")
            )
            case_data = Casesresponse.model_validate(db_case).model_dump()

            return {
                "case": case_data,
                "order": r,
                "shipping": r2
            }
            
       except(httpx.ConnectError):
           raise HTTPException(status_code=503,detail="External service unavailable")
       except(httpx.TimeoutException):
           raise HTTPException(status_code=504,detail="External service timed out")
       except(httpx.HTTPStatusError) as e:
           if (e.response.status_code == 404):
            raise HTTPException(status_code=404,detail="External order or shipment not found")
           else:
            raise HTTPException(status_code=502,detail="External service returned an error")

class ComplaintRequest(BaseModel):
    complaint : str

@app.post("/complaints/extract",response_model=ComplaintDetails)
def extcomplaint(request:ComplaintRequest):
    result = extract_complaint(request.complaint)
    return result

class AgentRequest(BaseModel):
    question:str

@app.post("/agent/ask")
def askagent(request:AgentRequest):
    answer = ask_resolveai(request.question)
    return {"answer":answer}

@app.post("/complaints/resolve")
def complaintagent(request:ComplaintRequest):
    try:
        comp = extract_complaint(request.complaint)
        if comp.order_id is None:
            return {"complaint":comp,"answer":"Please provide a valid order id"}
        ans = ask_resolveai(request.complaint)

        return {"complaint": comp, "answer": ans}
    except RateLimitError:
        raise HTTPException(status_code=503,detail="AI service temporarily unavailable")
    except APITimeoutError:
            raise HTTPException(status_code=504,detail="AI service timed out")
    except APIConnectionError:
        raise HTTPException(status_code=503,detail="Unable to connect to AI service")   
    except ValueError:
        raise HTTPException(status_code=502,detail="Invalid AI response") 

           
           


         



