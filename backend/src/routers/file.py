from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models.user import User
from src.routers.auth import get_current_user
from src.models.file import File as FileModel
from src.utils.document import markdown_to_docx, generate_radar_chart
from src.utils.parser import parse_assessment_excel, create_template_excel
import os
import uuid
import aiofiles
from src.config import settings

router = APIRouter(prefix="/api/files", tags=["文件处理"])

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    db_file = FileModel(
        user_id=current_user.id,
        name=file.filename,
        type=file.content_type,
        size=len(content),
        file_path=file_path
    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)
    
    return {
        "success": True,
        "data": {
            "id": db_file.id,
            "name": db_file.name,
            "type": db_file.type,
            "size": db_file.size
        }
    }

@router.post("/parse-assessment")
async def parse_assessment(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(FileModel).where(
            FileModel.id == file_id,
            FileModel.user_id == current_user.id
        )
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    async with aiofiles.open(file.file_path, 'rb') as f:
        content = await f.read()
    
    parsed = parse_assessment_excel(content)
    
    return {"success": True, "data": parsed}

@router.get("/download-template")
async def download_template():
    content = create_template_excel()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=assessment_template.xlsx"}
    )

@router.get("/download/{file_id}")
async def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(FileModel).where(
            FileModel.id == file_id,
            FileModel.user_id == current_user.id
        )
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    async with aiofiles.open(file.file_path, 'rb') as f:
        content = await f.read()
    
    return Response(
        content=content,
        media_type=file.type,
        headers={"Content-Disposition": f"attachment; filename={file.name}"}
    )

@router.post("/convert/markdown-to-docx")
async def convert_markdown_to_docx(
    content: str,
    title: str = "",
    current_user: User = Depends(get_current_user)
):
    docx_content = markdown_to_docx(content, title)
    
    os.makedirs(settings.GENERATED_DIR, exist_ok=True)
    file_path = os.path.join(settings.GENERATED_DIR, f"{uuid.uuid4()}.docx")
    
    with open(file_path, 'wb') as f:
        f.write(docx_content)
    
    return Response(
        content=docx_content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={title or 'document'}.docx"}
    )

@router.post("/generate-radar-chart")
async def create_radar_chart(
    scores: dict,
    title: str = "能力雷达图",
    current_user: User = Depends(get_current_user)
):
    chart_base64 = generate_radar_chart(scores, title)
    return {"success": True, "data": {"chart": chart_base64}}
