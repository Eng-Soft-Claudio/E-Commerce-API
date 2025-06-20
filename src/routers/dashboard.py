"""
Módulo de Roteamento para o Dashboard de Administração.

Fornece endpoints agregados para exibir estatísticas gerais da loja.
"""
from fastapi import APIRouter, Depends, HTTPException, status  # noqa: F401
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, auth
from ..database import get_db

router = APIRouter(
    prefix="/admin/stats",
    tags=["Admin Dashboard"],
    dependencies=[Depends(auth.get_current_superuser)]
)

@router.get("/")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Retorna as estatísticas agregadas para o painel de administração.
    """
    total_sales = db.query(func.sum(models.Order.total_price)).filter(models.Order.status == "paid").scalar() or 0
    total_orders = db.query(func.count(models.Order.id)).scalar() or 0
    total_users = db.query(func.count(models.User.id)).filter(models.User.is_superuser == False).scalar() or 0
    total_products = db.query(func.count(models.Product.id)).scalar() or 0
    
    return {
        "total_sales": total_sales,
        "total_orders": total_orders,
        "total_users": total_users,
        "total_products": total_products,
    }