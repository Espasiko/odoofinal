from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

# Importar dependencias
from ..models.schemas import User
from ..services.auth_service import get_current_active_user
from ..services.odoo_service import odoo_service

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Modelos Pydantic para Tasks
class TaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    priority: Optional[str] = "normal"
    stage_id: Optional[int] = None
    user_id: Optional[int] = None
    partner_id: Optional[int] = None
    date_deadline: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    name: Optional[str] = None

class Task(TaskBase):
    id: int
    create_date: datetime
    write_date: datetime
    active: bool = True

    class Config:
        from_attributes = True

@router.get("/", response_model=List[Task])
async def get_tasks(
    _start: int = Query(0, description="Offset for pagination"),
    _end: int = Query(10, description="Limit for pagination"),
    _sort: str = Query("create_date", description="Field to sort by"),
    _order: str = Query("desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener lista de tareas"""
    try:
        # Configurar ordenamiento
        order = f"{_sort} {_order}"
        
        # Buscar tareas en Odoo
        domain = [('active', '=', True)]  # Solo tareas activas
        
        # Por ahora devolvemos datos de ejemplo hasta que se implemente la conexión con Odoo
        # TODO: Implementar conexión real con Odoo
        tasks_data = [
            {
                'id': 1,
                'name': 'Tarea de ejemplo 1',
                'description': 'Descripción de la tarea 1',
                'priority': 'high',
                'stage_id': [1, 'En progreso'],
                'user_id': [1, 'Usuario 1'],
                'partner_id': [1, 'Cliente 1'],
                'date_deadline': '2024-12-31',
                'create_date': '2024-01-01 10:00:00',
                'write_date': '2024-01-02 15:30:00',
                'active': True
            },
            {
                'id': 2,
                'name': 'Tarea de ejemplo 2',
                'description': 'Descripción de la tarea 2',
                'priority': 'normal',
                'stage_id': [2, 'Pendiente'],
                'user_id': [2, 'Usuario 2'],
                'partner_id': [2, 'Cliente 2'],
                'date_deadline': '2024-12-25',
                'create_date': '2024-01-03 09:00:00',
                'write_date': '2024-01-04 11:15:00',
                'active': True
            }
        ]
        
        # Convertir a formato esperado
        tasks = []
        for task_data in tasks_data:
            task = {
                'id': task_data['id'],
                'name': task_data['name'],
                'description': task_data.get('description', ''),
                'priority': task_data.get('priority', 'normal'),
                'stage_id': task_data.get('stage_id', [None, None])[0] if task_data.get('stage_id') else None,
                'user_id': task_data.get('user_id', [None, None])[0] if task_data.get('user_id') else None,
                'partner_id': task_data.get('partner_id', [None, None])[0] if task_data.get('partner_id') else None,
                'date_deadline': task_data.get('date_deadline'),
                'create_date': task_data['create_date'],
                'write_date': task_data['write_date'],
                'active': task_data.get('active', True)
            }
            tasks.append(task)
        
        return tasks
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener tareas: {str(e)}")

@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Obtener una tarea específica"""
    try:
        # Datos de ejemplo - TODO: Implementar conexión real con Odoo
        if task_id == 1:
            task = {
                'id': 1,
                'name': 'Tarea de ejemplo 1',
                'description': 'Descripción de la tarea 1',
                'priority': 'high',
                'stage_id': 1,
                'user_id': 1,
                'partner_id': 1,
                'date_deadline': '2024-12-31',
                'create_date': '2024-01-01T10:00:00',
                'write_date': '2024-01-02T15:30:00',
                'active': True
            }
        elif task_id == 2:
            task = {
                'id': 2,
                'name': 'Tarea de ejemplo 2',
                'description': 'Descripción de la tarea 2',
                'priority': 'normal',
                'stage_id': 2,
                'user_id': 2,
                'partner_id': 2,
                'date_deadline': '2024-12-25',
                'create_date': '2024-01-03T09:00:00',
                'write_date': '2024-01-04T11:15:00',
                'active': True
            }
        else:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener tarea: {str(e)}")

@router.post("/", response_model=Task)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Crear una nueva tarea"""
    try:
        # Preparar datos para crear la tarea
        task_data = {
            'name': task.name,
            'description': task.description,
            'priority': task.priority,
            'user_id': task.user_id or current_user.get('id'),
            'partner_id': task.partner_id,
            'date_deadline': task.date_deadline.isoformat() if task.date_deadline else None,
        }
        
        if task.stage_id:
            task_data['stage_id'] = task.stage_id
        
        # Crear tarea en Odoo
        task_id = await odoo_client.create('project.task', task_data)
        
        # Obtener la tarea creada
        return await get_task(task_id, current_user, odoo_client)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear tarea: {str(e)}")

@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: int,
    task: TaskUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar una tarea existente"""
    try:
        # Preparar datos para actualizar
        update_data = {}
        
        if task.name is not None:
            update_data['name'] = task.name
        if task.description is not None:
            update_data['description'] = task.description
        if task.priority is not None:
            update_data['priority'] = task.priority
        if task.stage_id is not None:
            update_data['stage_id'] = task.stage_id
        if task.user_id is not None:
            update_data['user_id'] = task.user_id
        if task.partner_id is not None:
            update_data['partner_id'] = task.partner_id
        if task.date_deadline is not None:
            update_data['date_deadline'] = task.date_deadline.isoformat()
        
        # Actualizar en Odoo
        success = await odoo_client.write('project.task', [task_id], update_data)
        
        if not success:
            raise HTTPException(status_code=400, detail="No se pudo actualizar la tarea")
        
        # Obtener la tarea actualizada
        return await get_task(task_id, current_user, odoo_client)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar tarea: {str(e)}")

@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Eliminar una tarea (marcar como inactiva)"""
    try:
        # En lugar de eliminar, marcar como inactiva
        success = await odoo_client.write('project.task', [task_id], {'active': False})
        
        if not success:
            raise HTTPException(status_code=400, detail="No se pudo eliminar la tarea")
        
        return {"message": "Tarea eliminada correctamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar tarea: {str(e)}")