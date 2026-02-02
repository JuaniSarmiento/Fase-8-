"""
Model Structure Viewer

Shows the structure of all SQLAlchemy models in a readable format
without requiring a database connection.

Usage:
    python show_model_structure.py              # Show all models
    python show_model_structure.py UserModel    # Show specific model
"""
import sys
from pathlib import Path
from colorama import init, Fore

# Initialize colorama
init(autoreset=True)

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from src_v3.infrastructure.persistence.sqlalchemy.simple_models import (
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

ALL_MODELS = {
    "UserModel": UserModel,
    "UserProfileModel": UserProfileModel,
    "SubjectModel": SubjectModel,
    "CourseModel": CourseModel,
    "CommissionModel": CommissionModel,
    "ActivityModel": ActivityModel,
    "SessionModelV2": SessionModelV2,
    "ExerciseModelV2": ExerciseModelV2,
    "ExerciseAttemptModelV2": ExerciseAttemptModelV2,
    "CognitiveTraceModelV2": CognitiveTraceModelV2,
    "RiskModelV2": RiskModelV2,
}


def show_model(model_class, model_name):
    """Display the structure of a model."""
    table = model_class.__table__
    
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}📦 {model_name}")
    print(f"{Fore.CYAN}{'='*80}")
    print(f"{Fore.YELLOW}Table: {table.name}")
    print()
    
    # Primary Keys
    pks = [col.name for col in table.primary_key.columns]
    print(f"{Fore.GREEN}🔑 Primary Keys: {', '.join(pks)}")
    print()
    
    # Columns
    print(f"{Fore.CYAN}📋 Columns:")
    for col in table.columns:
        pk_marker = "🔑 " if col.primary_key else "   "
        fk_marker = "🔗 " if col.foreign_keys else "   "
        null_marker = "NULL" if col.nullable else "NOT NULL"
        
        type_str = str(col.type)
        
        # Foreign keys info
        fk_info = ""
        if col.foreign_keys:
            fk_targets = [str(fk.target_fullname) for fk in col.foreign_keys]
            fk_info = f" → {', '.join(fk_targets)}"
        
        print(f"{pk_marker}{fk_marker}{Fore.WHITE}{col.name:30} {Fore.YELLOW}{type_str:20} {Fore.MAGENTA}{null_marker:8}{Fore.CYAN}{fk_info}")
    
    print()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        # Show specific model
        model_name = sys.argv[1]
        if model_name in ALL_MODELS:
            show_model(ALL_MODELS[model_name], model_name)
        else:
            print(f"{Fore.RED}❌ Model '{model_name}' not found!")
            print(f"\n{Fore.YELLOW}Available models:")
            for name in sorted(ALL_MODELS.keys()):
                print(f"  - {name}")
            sys.exit(1)
    else:
        # Show all models
        print(f"{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}📚 ALL MODELS STRUCTURE")
        print(f"{Fore.CYAN}{'='*80}")
        
        for model_name in sorted(ALL_MODELS.keys()):
            show_model(ALL_MODELS[model_name], model_name)
        
        print(f"{Fore.CYAN}{'='*80}")
        print(f"{Fore.GREEN}✅ Showing {len(ALL_MODELS)} models")
        print(f"{Fore.CYAN}{'='*80}")
        print()
        print(f"{Fore.YELLOW}💡 To see a specific model: python show_model_structure.py ModelName")


if __name__ == "__main__":
    main()
