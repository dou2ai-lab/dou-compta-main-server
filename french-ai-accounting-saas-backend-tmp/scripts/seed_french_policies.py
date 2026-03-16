# -----------------------------------------------------------------------------
# File: seed_french_policies.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 01-12-2025
# Description: Seed French expense policies (meal caps, hotel caps, mileage)
# Run from backend with venv activated (not base):
#   .\venv\Scripts\Activate.ps1
#   $env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
#   python scripts/seed_french_policies.py
# If ModuleNotFoundError: pip install -r requirements.txt
# -----------------------------------------------------------------------------

"""
Seed French expense policies
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

from common.models import Base, Tenant
from services.admin.models import ExpensePolicy

# Database URL (convert async to sync)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dou_user:dou_password@localhost:5432/dou_expense_audit")
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

def seed_french_policies():
    """Seed French expense policies"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Get default tenant
        tenant_result = db.execute(select(Tenant).limit(1))
        tenant = tenant_result.scalar_one_or_none()
        
        if not tenant:
            print("No tenant found. Please create a tenant first.")
            return
        
        print(f"Seeding policies for tenant: {tenant.name}")
        
        # French Meal Caps Policy
        meal_policy = ExpensePolicy(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="French Meal Caps (Tax-Free Limits)",
            description="French tax-free meal reimbursement limits per meal type",
            policy_type="meal_cap",
            policy_rules={
                "breakfast": {
                    "max_amount": 19.00,
                    "requires_comment": True
                },
                "lunch": {
                    "max_amount": 25.00,
                    "requires_comment": True
                },
                "dinner": {
                    "max_amount": 25.00,
                    "requires_comment": True
                },
                "default": {
                    "max_amount": 25.00,
                    "requires_comment": True
                }
            },
            applies_to_roles=[],
            is_active=True,
            effective_from=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(meal_policy)
        
        # Hotel Accommodation Cap Policy
        hotel_policy = ExpensePolicy(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="Hotel Accommodation Cap",
            description="Maximum hotel expense per night",
            policy_type="hotel_cap",
            policy_rules={
                "max_amount": 200.00,
                "allow_with_approval": True,
                "requires_comment": True
            },
            applies_to_roles=[],
            is_active=True,
            effective_from=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(hotel_policy)
        
        # Mileage Reimbursement Policy
        mileage_policy = ExpensePolicy(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="French Mileage Reimbursement Rate",
            description="Standard mileage reimbursement rate for France",
            policy_type="mileage_rate",
            policy_rules={
                "rate_per_km": 0.629,
                "requires_comment": True
            },
            applies_to_roles=[],
            is_active=True,
            effective_from=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(mileage_policy)
        
        # General Amount Limit Policy
        amount_limit_policy = ExpensePolicy(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="General Expense Amount Limit",
            description="Maximum expense amount without approval",
            policy_type="amount_limit",
            policy_rules={
                "max_amount": 1000.00,
                "block_on_exceed": False,
                "requires_comment_on_exceed": True
            },
            applies_to_roles=[],
            is_active=True,
            effective_from=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(amount_limit_policy)
        
        # Required Fields Policy
        required_fields_policy = ExpensePolicy(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="Required Expense Fields",
            description="Mandatory fields for expense submission",
            policy_type="required_fields",
            policy_rules={
                "required_fields": ["description", "merchant_name", "category"]
            },
            applies_to_roles=[],
            is_active=True,
            effective_from=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(required_fields_policy)
        
        db.commit()
        
        print("Successfully seeded French expense policies:")
        print(f"  - Meal Caps Policy: {meal_policy.id}")
        print(f"  - Hotel Cap Policy: {hotel_policy.id}")
        print(f"  - Mileage Rate Policy: {mileage_policy.id}")
        print(f"  - Amount Limit Policy: {amount_limit_policy.id}")
        print(f"  - Required Fields Policy: {required_fields_policy.id}")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding policies: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_french_policies()

