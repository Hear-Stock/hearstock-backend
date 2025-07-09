from fastapi import APIRouter

router = APIRouter(prefix="/api/test")

@router.get("")
def test_deploy():
    return {"message": "testtest"}