# ======================================================
# Import Libs
# ======================================================

from fastapi import APIRouter, Depends, UploadFile, status # pyright: ignore[reportMissingImports]
from fastapi.responses import JSONResponse # pyright: ignore[reportMissingImports]
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
import aiofiles # pyright: ignore[reportMissingModuleSource]
from models import ResponseSignal
import logging
from .schemes.data import ProcessRequest
import os

logger = logging.getLogger('hypercorn.error')

# ======================================================
# Func.
# ======================================================
# - upload
#   - test validation
#   - test path
#   - stored data algorithm
# ======================================================

data_router = APIRouter(
    prefix='/api/v1/data'
)

@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str, file: UploadFile, 
                        app_settings: Settings = Depends(get_settings)):

    data_controller = DataController()


    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal
            } 
        )

    project_dir_path = ProjectController().get_project_path(project_id=project_id)
    file_path, file_id = data_controller.generate_unique_file_path(
        orig_file_name=file.filename, 
        project_id=project_id
    )


    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:

        logger.error(f"Error while uploading file: {e}")


        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_UPLOADED_FAIL.value
            } 
        )
    
    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOADED_SUCCESS.value,
            "file_id": file_id
        } 
    )



@data_router.post("/process/{project_id}")
async def process_endpoint(project_id: str, process_request: ProcessRequest):

    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    chunk_overlap = process_request.chunk_overlap

    process_controller = ProcessController(project_id=project_id)
    file_content = process_controller.get_file_content(file_id=file_id)
    file_chunks = process_controller.process_file_content(
        file_content=file_content,
        file_id=file_id,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                "signal": ResponseSignal.PROCESSING_FAILD
            }

        )

    return file_chunks 