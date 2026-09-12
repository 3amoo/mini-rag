from fastapi import FastAPI

app = FastAPI()


@app.get("/hi")
def welcome():
    return {
        "message":"Helloooooo DUDE"
    }