"""
Schema Drift Audit Script

This script compares SQLAlchemy Models against the live PostgreSQL Database Schema
to detect any mismatches (e.g., column names, primary keys, missing tables/columns).

Usage:
    python audit_schema.py                    # Normal mode (requires DB connection)
    python audit_schema.py --dry-run          # Dry run mode (no DB connection needed)
    python audit_schema.py --help             # Show this help

Modes:
    Normal:  Connects to live database and compares schemas
    Dry-run: Shows what would be checked without connecting to database

Requirements:
    - Database must be running (for normal mode)
    - .env file with DATABASE_URL configured
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from sqlalchemy import create_engine, inspect, MetaData
from sqlalchemy.orm import DeclarativeMeta
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Add backend to path for imports
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from src_v3.infrastructure.persistence.sqlalchemy.simple_models import (
        Base,
        UserModel,
        UserProfileModel,
        SubjectModel,
        CourseModel,
        CommissionModel,
        ActivityModel,
        SessionModelV2,
        ExerciseModelV2,
        ExerciseAttemptModelV2,
        CognitiveTraceModelV2,
        RiskModelV2,
    )
except ImportError as e:
    print(f"{Fore.RED}❌ Failed to import models: {e}")
    print(f"{Fore.YELLOW}💡 Make sure you're running from the project root")
    sys.exit(1)


def get_database_url() -> str:
    """Get database URL from environment, converting asyncpg to psycopg2 for sync connection."""
    from dotenv import load_dotenv
    
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print(f"{Fore.YELLOW}⚠️  DATABASE_URL not found in .env file")
        print(f"{Fore.YELLOW}💡 Trying default: postgresql://postgres:postgres@127.0.0.1:5433/ai_native")
        db_url = "postgresql://postgres:postgres@127.0.0.1:5433/ai_native"
    else:
        # Convert async URL to sync URL for inspection
        if "postgresql+asyncpg://" in db_url:
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    return db_url


def get_model_info(model: DeclarativeMeta) -> Dict:
    """Extract column and primary key information from a SQLAlchemy model."""
    table = model.__table__
    
    columns = {}
    for col in table.columns:
        columns[col.name] = {
            "type": str(col.type),
            "nullable": col.nullable,
            "primary_key": col.primary_key,
            "foreign_keys": [str(fk.target_fullname) for fk in col.foreign_keys],
        }
    
    primary_keys = [col.name for col in table.primary_key.columns]
    
    return {
        "table_name": table.name,
        "columns": columns,
        "primary_keys": primary_keys,
    }


def get_db_table_info(inspector, table_name: str) -> Dict:
    """Extract column and primary key information from the database."""
    try:
        columns_info = inspector.get_columns(table_name)
        pk_constraint = inspector.get_pk_constraint(table_name)
        
        columns = {}
        for col in columns_info:
            columns[col["name"]] = {
                "type": str(col["type"]),
                "nullable": col["nullable"],
                "primary_key": col["name"] in pk_constraint.get("constrained_columns", []),
            }
        
        primary_keys = pk_constraint.get("constrained_columns", [])
        
        return {
            "columns": columns,
            "primary_keys": primary_keys,
            "exists": True,
        }
    except Exception as e:
        return {
            "columns": {},
            "primary_keys": [],
            "exists": False,
            "error": str(e),
        }


def compare_schema(model_info: Dict, db_info: Dict) -> Tuple[bool, List[str]]:
    """
    Compare model schema with database schema.
    
    Returns:
        Tuple of (is_match, list_of_issues)
    """
    issues = []
    
    # Check if table exists
    if not db_info["exists"]:
        issues.append(f"❌ Table '{model_info['table_name']}' does NOT exist in database")
        return False, issues
    
    model_columns = set(model_info["columns"].keys())
    db_columns = set(db_info["columns"].keys())
    
    # Check for columns in model but not in DB
    missing_in_db = model_columns - db_columns
    if missing_in_db:
        for col in missing_in_db:
            issues.append(f"❌ Column '{col}' defined in Model but MISSING in Database")
    
    # Check for columns in DB but not in model
    extra_in_db = db_columns - model_columns
    if extra_in_db:
        for col in extra_in_db:
            issues.append(f"⚠️  Column '{col}' exists in Database but NOT in Model")
    
    # Check primary key mismatches
    model_pks = set(model_info["primary_keys"])
    db_pks = set(db_info["primary_keys"])
    
    if model_pks != db_pks:
        issues.append(
            f"❌ PRIMARY KEY MISMATCH:\n"
            f"   Model expects: {sorted(model_pks)}\n"
            f"   Database has:  {sorted(db_pks)}"
        )
    
    # Check column properties for matching columns
    for col_name in model_columns & db_columns:
        model_col = model_info["columns"][col_name]
        db_col = db_info["columns"][col_name]
        
        # Check nullable mismatch
        if model_col["nullable"] != db_col["nullable"]:
            issues.append(
                f"⚠️  Column '{col_name}' nullable mismatch: "
                f"Model={model_col['nullable']}, DB={db_col['nullable']}"
            )
    
    return len(issues) == 0, issues


def audit_all_models(models: List[DeclarativeMeta], engine):
    """Audit all models against the database."""
    inspector = inspect(engine)
    
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}🔍 SCHEMA DRIFT AUDIT")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    total_models = len(models)
    matched = 0
    mismatched = 0
    
    for model in models:
        model_info = get_model_info(model)
        table_name = model_info["table_name"]
        
        print(f"{Fore.CYAN}📋 Checking Model: {Fore.WHITE}{model.__name__} → Table: {Fore.YELLOW}{table_name}")
        
        db_info = get_db_table_info(inspector, table_name)
        is_match, issues = compare_schema(model_info, db_info)
        
        if is_match:
            print(f"{Fore.GREEN}✅ SCHEMA MATCHES - All columns and primary keys are correct!")
            matched += 1
        else:
            print(f"{Fore.RED}❌ SCHEMA MISMATCH DETECTED:")
            for issue in issues:
                print(f"   {issue}")
            mismatched += 1
        
        print()  # Empty line between models
    
    # Summary
    print(f"{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}📊 AUDIT SUMMARY")
    print(f"{Fore.CYAN}{'='*80}")
    print(f"Total Models:     {total_models}")
    print(f"{Fore.GREEN}✅ Matched:       {matched}")
    print(f"{Fore.RED}❌ Mismatched:    {mismatched}")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    if mismatched == 0:
        print(f"{Fore.GREEN}🎉 SUCCESS! All models match the database schema perfectly!")
        return 0
    else:
        print(f"{Fore.RED}⚠️  WARNING! Found {mismatched} schema mismatch(es). Review and fix them!")
        return 1


def main():
    """Main execution."""
    # Check for command line arguments
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)
    
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        print(f"{Fore.YELLOW}🔍 Running in DRY-RUN mode (no database connection)")
        print(f"{Fore.YELLOW}   This will show the models that would be audited\n")
    
    try:
        # List of all models to audit
        models = [
            UserModel,
            UserProfileModel,
            SubjectModel,
            CourseModel,
            CommissionModel,
            ActivityModel,
            SessionModelV2,
            ExerciseModelV2,
            ExerciseAttemptModelV2,
            CognitiveTraceModelV2,
            RiskModelV2,
        ]
        
        if dry_run:
            # Show what would be audited
            print(f"{Fore.CYAN}{'='*80}")
            print(f"{Fore.CYAN}📋 MODELS THAT WOULD BE AUDITED")
            print(f"{Fore.CYAN}{'='*80}\n")
            
            for model in models:
                model_info = get_model_info(model)
                table_name = model_info["table_name"]
                pks = ", ".join(model_info["primary_keys"])
                col_count = len(model_info["columns"])
                
                print(f"{Fore.CYAN}📦 {model.__name__}")
                print(f"   Table: {Fore.YELLOW}{table_name}")
                print(f"   Primary Keys: {Fore.GREEN}{pks}")
                print(f"   Columns: {col_count}")
                print(f"   Column Names: {', '.join(sorted(model_info['columns'].keys()))}")
                print()
            
            print(f"{Fore.CYAN}{'='*80}")
            print(f"{Fore.YELLOW}💡 To run actual audit against database:")
            print(f"{Fore.YELLOW}   python audit_schema.py")
            print(f"{Fore.CYAN}{'='*80}\n")
            sys.exit(0)
        
        # Normal mode - connect to database
        print(f"{Fore.CYAN}🔌 Connecting to database...")
        db_url = get_database_url()
        engine = create_engine(db_url, echo=False)
        
        # Test connection
        with engine.connect() as conn:
            print(f"{Fore.GREEN}✅ Connected successfully!")
        
        # Run audit
        exit_code = audit_all_models(models, engine)
        
        engine.dispose()
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"\n{Fore.RED}❌ FATAL ERROR: {e}")
        print(f"\n{Fore.YELLOW}💡 Troubleshooting Tips:")
        print(f"   1. Make sure PostgreSQL is running (check: Get-Service postgresql*)")
        print(f"   2. Verify .env file has correct DATABASE_URL")
        print(f"   3. Check if password is correct (default: postgres)")
        print(f"   4. Verify port 5433 is correct for your setup")
        print(f"   5. Try running: python find_db_password.py to find correct password")
        print(f"\n{Fore.YELLOW}📝 Current DATABASE_URL should be in .env file")
        print(f"   Format: postgresql+asyncpg://postgres:YOUR_PASSWORD@127.0.0.1:5433/ai_native")
        print(f"\n{Fore.CYAN}💡 Or run in dry-run mode to see model structure:")
        print(f"   python audit_schema.py --dry-run")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
